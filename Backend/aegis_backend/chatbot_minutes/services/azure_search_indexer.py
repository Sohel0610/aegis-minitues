"""Azure AI Search index provisioning and document-chunk synchronisation.

The runtime query client uses a query key. Index provisioning and writes require
an admin key and are deliberately separate from normal chat requests.
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Document, Embedding


class AzureSearchIndexer:
    def _clients(self):
        if not all([settings.AZURE_SEARCH_ENDPOINT, settings.AZURE_SEARCH_ADMIN_KEY, settings.AZURE_SEARCH_INDEX]):
            raise ValueError("Azure Search endpoint, admin key, and index name are required for index provisioning/writes")
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            from azure.search.documents.indexes import SearchIndexClient
        except ImportError as exc:
            raise ValueError("Install azure-search-documents to enable Azure AI Search indexing") from exc
        credential = AzureKeyCredential(settings.AZURE_SEARCH_ADMIN_KEY)
        return (
            SearchIndexClient(settings.AZURE_SEARCH_ENDPOINT, credential),
            SearchClient(settings.AZURE_SEARCH_ENDPOINT, settings.AZURE_SEARCH_INDEX, credential),
        )

    def ensure_index(self) -> None:
        """Create or update the documented index schema. Run as a deployment step."""
        try:
            from azure.search.documents.indexes.models import (
                HnswAlgorithmConfiguration,
                SearchField,
                SearchFieldDataType,
                SearchIndex,
                SearchableField,
                SimpleField,
                VectorSearch,
                VectorSearchProfile,
            )
        except ImportError as exc:
            raise ValueError("Install azure-search-documents to provision the Azure AI Search index") from exc
        index_client, _ = self._clients()
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SimpleField(name=settings.AZURE_SEARCH_OWNER_FIELD, type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="document_id", type=SearchFieldDataType.Int64, filterable=True),
            SimpleField(name="filename", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="location", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="extraction_method", type=SearchFieldDataType.String, filterable=True),
            # Meeting metadata fields for metadata-filtered retrieval
            SimpleField(name="meeting_title", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SimpleField(name="meeting_date", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SimpleField(name="meeting_type", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="company_name", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name=settings.AZURE_SEARCH_CONTENT_FIELD, type=SearchFieldDataType.String),
            SearchField(
                name=settings.AZURE_SEARCH_VECTOR_FIELD,
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=settings.COHERE_EMBED_DIMENSIONS,
                vector_search_profile_name="aegis-hnsw-profile",
            ),
        ]
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="aegis-hnsw")],
            profiles=[VectorSearchProfile(name="aegis-hnsw-profile", algorithm_configuration_name="aegis-hnsw")],
        )
        index_client.create_or_update_index(SearchIndex(name=settings.AZURE_SEARCH_INDEX, fields=fields, vector_search=vector_search))

    def upsert_document(self, db: Session, document: Document) -> int:
        """Push already-created embeddings and source metadata to Azure AI Search."""
        _, search_client = self._clients()
        chunks = db.query(Embedding).filter(Embedding.document_id == document.id).order_by(Embedding.chunk_index).all()
        payload: List[Dict[str, Any]] = []
        for chunk in chunks:
            metadata = chunk.chunk_metadata or {}
            payload.append({
                "id": f"minutes-{document.id}-{chunk.chunk_index}",
                settings.AZURE_SEARCH_OWNER_FIELD: str(document.user_id),
                "document_id": document.id,
                "filename": document.filename,
                "chunk_index": chunk.chunk_index or 0,
                "location": metadata.get("location", "Document"),
                "extraction_method": document.extraction_method or "unknown",
                # Meeting metadata from enriched chunk metadata
                "meeting_title": metadata.get("meeting_title", ""),
                "meeting_date": metadata.get("meeting_date", ""),
                "meeting_type": metadata.get("meeting_type", ""),
                "company_name": metadata.get("company_name", ""),
                settings.AZURE_SEARCH_CONTENT_FIELD: chunk.chunk_text,
                settings.AZURE_SEARCH_VECTOR_FIELD: chunk.embedding_vector,
            })
        if not payload:
            return 0
        result = search_client.merge_or_upload_documents(payload)
        failed = [item for item in result if not item.succeeded]
        if failed:
            raise RuntimeError(f"Azure AI Search rejected {len(failed)} chunk(s)")
        return len(payload)
