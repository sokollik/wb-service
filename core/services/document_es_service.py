import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class DocumentElasticsearchService:

    def __init__(self, es_client: Elasticsearch, index_name: str = "documents"):
        self.es = es_client
        self.index_name = index_name

    def create_index(self):
        try:
            if self.es.indices.exists(index=self.index_name):
                return
        except Exception as e:
            logger.error(f"Ошибка проверки индекса документов: {e}")
            raise

        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "filter": {
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_",
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian",
                        },
                        "edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                        },
                    },
                    "analyzer": {
                        "russian_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "russian_stop",
                                "russian_stemmer",
                            ],
                        },
                        "autocomplete": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "edge_ngram_filter"],
                        },
                    },
                },
            },
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "russian_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "autocomplete": {
                                "type": "text",
                                "analyzer": "autocomplete",
                            },
                        },
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "russian_analyzer",
                    },
                    "type": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "author_id": {"type": "keyword"},
                    "curator_id": {"type": "keyword"},
                    "folder_id": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                },
            },
        }

        try:
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Индекс документов '{self.index_name}' создан")
        except Exception as e:
            logger.error(f"Ошибка создания индекса документов: {e}")
            raise

    def index_document(self, doc_data: Dict[str, Any]):
        try:
            self.es.index(
                index=self.index_name,
                id=str(doc_data["doc_id"]),
                document=doc_data,
            )
        except Exception as e:
            logger.error(f"Ошибка индексации документа {doc_data.get('doc_id')}: {e}")

    def update_document_meta(self, doc_id: int, fields: Dict[str, Any]):
        try:
            self.es.update(
                index=self.index_name,
                id=str(doc_id),
                doc=fields,
            )
        except Exception as e:
            logger.warning(f"Ошибка обновления метаданных документа {doc_id} в ES: {e}")

    def delete_document(self, doc_id: int):
        try:
            self.es.delete(index=self.index_name, id=str(doc_id))
        except Exception as e:
            logger.warning(f"Ошибка удаления документа {doc_id} из ES: {e}")

    def search_documents(
        self,
        query: Optional[str] = None,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        author_id: Optional[str] = None,
        curator_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        show_archived: bool = False,
        from_: int = 0,
        size: int = 20,
    ) -> Dict[str, Any]:
        filter_conditions = []

        if status:
            filter_conditions.append({"term": {"status": status}})
        elif not show_archived:
            filter_conditions.append(
                {"bool": {"must_not": [{"term": {"status": "ARCHIVED"}}]}}
            )

        if doc_type:
            filter_conditions.append({"term": {"type": doc_type}})
        if author_id:
            filter_conditions.append({"term": {"author_id": author_id}})
        if curator_id:
            filter_conditions.append({"term": {"curator_id": curator_id}})

        date_range: Dict[str, str] = {}
        if date_from:
            date_range["gte"] = date_from.isoformat()
        if date_to:
            date_range["lte"] = date_to.isoformat()
        if date_range:
            filter_conditions.append({"range": {"created_at": date_range}})

        if not query or not query.strip():
            query_clause: Dict[str, Any] = {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": filter_conditions,
                }
            }
        else:
            query_clause = {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": [
                                                "title.autocomplete^4",
                                                "title^3",
                                                "content^1",
                                            ],
                                            "type": "cross_fields",
                                            "operator": "and",
                                        }
                                    },
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": [
                                                "title^3",
                                                "title.autocomplete^2",
                                                "content",
                                            ],
                                            "type": "best_fields",
                                            "fuzziness": "AUTO",
                                            "operator": "or",
                                        }
                                    },
                                ],
                                "minimum_should_match": 1,
                            }
                        }
                    ],
                    "filter": filter_conditions,
                }
            }

        try:
            result = self.es.search(
                index=self.index_name,
                query=query_clause,
                from_=from_,
                size=size,
                sort=[
                    {"_score": {"order": "desc"}},
                    {"created_at": {"order": "desc"}},
                ],
            )
            return {
                "total": result["hits"]["total"]["value"],
                "results": [
                    self._format_hit(hit) for hit in result["hits"]["hits"]
                ],
            }
        except Exception as e:
            logger.error(f"Ошибка поиска документов: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    def _format_hit(self, hit: Dict) -> Dict[str, Any]:
        source = hit["_source"]
        folder_id = source.get("folder_id")
        return {
            "doc_id": int(source["doc_id"]),
            "title": source.get("title", ""),
            "type": source.get("type"),
            "status": source.get("status"),
            "author_id": source.get("author_id"),
            "curator_id": source.get("curator_id"),
            "folder_id": int(folder_id) if folder_id else None,
            "created_at": source.get("created_at"),
            "updated_at": source.get("updated_at"),
            "score": round(hit.get("_score", 0) or 0, 2),
        }
