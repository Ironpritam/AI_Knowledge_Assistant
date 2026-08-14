# from app.services.vector.embedding_service import (EmbeddingService,)
# from app.services.vector.chroma_service import (ChromaService,)


class RetrievalService:
    def __init__(self,embedding_service, chroma_service,):
        self.embedding_service = embedding_service            
        self.chroma_service = chroma_service


    def retrieve(self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 5,
        document_id: str | None = None,
    ):
        collection = self.chroma_service.get_collection(
            collection_name=collection_name,
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )
        query_embedding = self.embedding_service.embed_query(query)

        results = self.chroma_service.search(
            collection=collection,
            query_embedding=query_embedding,
            top_k=top_k,
            where={"document_id": document_id} if document_id is not None else None,
        )
        return results
