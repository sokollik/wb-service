from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError

from core.config.settings import get_settings
from core.services.elastic_search_service import EmployeeElasticsearchService

_elasticsearch_client: Optional[Elasticsearch] = None
_elasticsearch_service: Optional[EmployeeElasticsearchService] = None


def get_elasticsearch_client() -> Elasticsearch:
    global _elasticsearch_client

    settings = get_settings()

    if _elasticsearch_client is None:
        _elasticsearch_client = Elasticsearch(
            [settings.ELASTICSEARCH_HOST],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )

    return _elasticsearch_client


def get_elasticsearch_service() -> EmployeeElasticsearchService:
    global _elasticsearch_service
    settings = get_settings()
    if _elasticsearch_service is None:
        es_client = get_elasticsearch_client()
        _elasticsearch_service = EmployeeElasticsearchService(
            es_client=es_client, index_name=settings.ELASTICSEARCH_INDEX_NAME
        )

    return _elasticsearch_service
