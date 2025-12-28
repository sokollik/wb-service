# core/services/search_service.py (ПЕРЕРАБОТАННАЯ версия)
import logging
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

logger = logging.getLogger(__name__)


class EmployeeElasticsearchService:

    def __init__(
        self, es_client: Elasticsearch, index_name: str = "employee"
    ):
        self.es = es_client
        self.index_name = index_name

    def create_index(self):
        """Создание индекса с поддержкой русского и английского языков"""
        try:
            if self.es.indices.exists(index=self.index_name):
                return
        except Exception as e:
            logger.error(f"Error checking index: {e}")
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
                        "english_stop": {
                            "type": "stop",
                            "stopwords": "_english_",
                        },
                        "english_stemmer": {
                            "type": "stemmer",
                            "language": "english",
                        },
                        "edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                        },
                    },
                    "analyzer": {
                        "multilang_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "russian_stop",
                                "english_stop",
                                "russian_stemmer",
                                "english_stemmer",
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
                    "eid": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "analyzer": "multilang_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "autocomplete": {
                                "type": "text",
                                "analyzer": "autocomplete",
                            },
                        },
                    },
                    "position": {
                        "type": "text",
                        "analyzer": "multilang_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "work_email": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "standard",
                            }
                        },
                    },
                    "work_phone": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "standard",
                            }
                        },
                    },
                    "organization_unit_name": {
                        "type": "text",
                        "analyzer": "multilang_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "organization_unit_id": {"type": "keyword"},
                    "work_band": {
                        "type": "text",
                        "analyzer": "multilang_analyzer",
                    },
                    "is_fired": {"type": "boolean"},
                    "hire_date": {"type": "date"},
                    "indexed_at": {"type": "date"},
                }
            },
        }

        try:
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Index '{self.index_name}' created")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def index_employee(self, employee_data: Dict[str, Any]):
        """Индексация одного сотрудника"""
        try:
            self.es.index(
                index=self.index_name,
                id=str(employee_data.get("eid")),
                document=employee_data,
            )
        except Exception as e:
            logger.error(
                f"Error indexing employee {employee_data.get('eid')}: {e}"
            )

    def bulk_index_employees(self, employees: List[Dict[str, Any]]):
        """Массовая индексация сотрудников"""
        if not employees:
            return

        actions = []
        for emp in employees:
            actions.append(
                {
                    "_index": self.index_name,
                    "_id": str(emp.get("eid")),
                    "_source": emp,
                }
            )

        try:
            success, failed = bulk(
                self.es, actions, raise_on_error=False, chunk_size=500
            )
            logger.info(f"Bulk indexing: {success} success, {failed} failed")
        except Exception as e:
            logger.error(f"Error in bulk indexing: {e}")

    def search_employees(
        self,
        query: Optional[str] = None,
        from_: int = 0,
        size: int = 10,
    ):
        filter_conditions = [{"term": {"is_fired": False}}]

        if not query or query.strip() == "":
            query_clause = {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": filter_conditions,
                }
            }
        else:
            eid_condition = None
            try:
                eid_value = int(query.strip())
                eid_condition = {"term": {"eid": str(eid_value)}}
            except (ValueError, TypeError):
                pass

            must_conditions = [
                {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "full_name^4",
                                        "position^2",
                                        "organization_unit_name^2",
                                        "work_email",
                                        "work_phone",
                                        "work_band",
                                    ],
                                    "type": "cross_fields",
                                    "operator": "and",
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "full_name^3",
                                        "position^1.5",
                                        "organization_unit_name^1.5",
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
            ]

            if eid_condition:
                query_clause = {
                    "bool": {
                        "should": [
                            {"bool": {"must": must_conditions}},
                            eid_condition,
                        ],
                        "filter": filter_conditions,
                        "minimum_should_match": 1,
                    }
                }
            else:
                query_clause = {
                    "bool": {
                        "must": must_conditions,
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
                    {"hire_date": {"order": "desc"}},
                ],
            )

            return {
                "total": result["hits"]["total"]["value"],
                "results": [
                    self._format_hit(hit) for hit in result["hits"]["hits"]
                ],
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

    def suggest_employees(
        self, query: str, size: int = 10
    ):
        if not query or len(query) < 1:
            return []

        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "full_name.autocomplete^2",
                                "full_name",
                            ],
                            "type": "best_fields",
                            "operator": "or",
                        }
                    }
                ],
                "filter": [{"term": {"is_fired": False}}],
            }
        }

        try:
            result = self.es.search(
                index=self.index_name,
                query=search_query,
                size=size,
                _source=[
                    "eid",
                    "full_name",
                    "position",
                    "organization_unit_name",
                ],
            )

            suggestions = []
            for hit in result["hits"]["hits"]:
                source = hit["_source"]
                suggestions.append(
                    {
                        "eid": int(source["eid"]),
                        "full_name": source["full_name"],
                        "position": source["position"],
                        "department": source.get("organization_unit_name", ""),
                    }
                )

            return suggestions

        except Exception as e:
            logger.error(f"Suggest error: {e}")
            return []

    def _format_hit(self, hit: Dict) -> Dict[str, Any]:
        source = hit["_source"]
        return {
            "eid": int(source["eid"]),
            "full_name": source.get("full_name", ""),
            "position": source.get("position", ""),
            "work_email": source.get("work_email"),
            "work_phone": source.get("work_phone"),
            "organization_unit_id": source.get("organization_unit_id"),
            "organization_unit_name": source.get("organization_unit_name"),
            "work_band": source.get("work_band"),
            "score": round(hit.get("_score", 0), 2),
        }

    def delete_employee(self, eid: int):
        try:
            self.es.delete(index=self.index_name, id=str(eid))
        except Exception as e:
            logger.warning(f"Could not delete employee {eid}: {e}")

    def sync_employee(self, employee_data: Dict[str, Any]):
        self.index_employee(employee_data)

    def get_index_stats(self) -> Dict[str, Any]:
        try:
            count = self.es.count(index=self.index_name)
            return {
                "index_name": self.index_name,
                "document_count": count.get("count", 0),
                "status": "ok",
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                "index_name": self.index_name,
                "document_count": 0,
                "status": "error",
                "error": str(e),
            }