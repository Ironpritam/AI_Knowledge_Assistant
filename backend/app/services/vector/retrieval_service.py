# from app.services.vector.embedding_service import (EmbeddingService,)
# from app.services.vector.chroma_service import (ChromaService,)


import math


class RetrievalService:
    def __init__(self,embedding_service, chroma_service,):
        self.embedding_service = embedding_service            
        self.chroma_service = chroma_service


    def retrieve(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 5,
        document_ids: list[str] | None = None,
        ensure_document_coverage: bool = False,
    ):
        collection = self.chroma_service.get_collection(
            collection_name=collection_name,
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )

        query_embedding = self.embedding_service.embed_query(query)

        if not document_ids:
            return self.chroma_service.search(
                collection=collection,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        unique_document_ids = list(dict.fromkeys(str(doc_id) for doc_id in document_ids))
        if not ensure_document_coverage or len(unique_document_ids) == 1:
            where = (
                {"document_id": unique_document_ids[0]}
                if len(unique_document_ids) == 1
                else {
                    "$or": [
                        {"document_id": document_id}
                        for document_id in unique_document_ids
                    ]
                }
            )
            return self.chroma_service.search(
                collection=collection,
                query_embedding=query_embedding,
                top_k=top_k,
                where=where,
            )

        # Multi-document summaries and comparisons need context from every
        # selected document. Query them separately only for that coverage mode.
        results_by_document = []
        results_per_document = max(
            1, math.ceil(top_k / len(unique_document_ids))
        )

        for document_id in unique_document_ids:
            results_by_document.append(
                self.chroma_service.search(
                    collection=collection,
                    query_embedding=query_embedding,
                    top_k=results_per_document,
                    where={"document_id": document_id},
                )
            )

        # Interleave per-document rankings so the answer context and the first
        # displayed sources represent every selected document.
        results = []
        max_result_count = max((len(items) for items in results_by_document), default=0)
        for result_index in range(max_result_count):
            for document_results in results_by_document:
                if result_index < len(document_results):
                    results.append(document_results[result_index])

        return results
