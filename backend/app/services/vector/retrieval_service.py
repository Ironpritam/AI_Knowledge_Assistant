from app.services.vector.embedding_service import (EmbeddingService,)
from app.services.vector.chroma_service import (ChromaService,)


class RetrievalService:
    def __init__(self,embedding_model: str = "bge-small",collection_name: str = "documents",):
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        
        self.vector_store = ChromaService(
            collection_name=collection_name,
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )
        self.vector_store.validate_embedding_model(
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )

    def search(self,query: str,top_k: int = 5,) -> list[dict]:
        query_embedding = (self.embedding_service.embed_query(query))

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )