# from app.services.vector.embedding_service import (EmbeddingService,)
# from app.services.vector.chroma_service import (ChromaService,)


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
    ):
        collection = self.chroma_service.get_collection(
            collection_name=collection_name,
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )

        query_embedding = self.embedding_service.embed_query(query)

        where = None

        if document_ids:
            document_ids = [str(doc_id) for doc_id in document_ids]

            if len(document_ids) == 1:
                where = {
                    "document_id": document_ids[0]
                }
            else:
                where = {
                    "$or": [
                        {"document_id": document_id}
                        for document_id in document_ids
                    ]
                }

        results = self.chroma_service.search(
            collection=collection,
            query_embedding=query_embedding,
            top_k=top_k,
            where=where,
        )

        return results
