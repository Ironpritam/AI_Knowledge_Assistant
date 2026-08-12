from app.services.vector.embedding_service import EmbeddingService
from app.services.llm.llm_service import LLMService
from app.services.rag.rag_service import RAGService


class ApplicationContainer:
    def __init__(self):
        print("Initializing AI Knowledge Assistant...")

        self.embedding_service = EmbeddingService(model_name="bge-small")
        self.llm_service = LLMService(
            provider="ollama",
            model="qwen3:8b",
        )
        self.rag_service = RAGService(
            embedding_service=self.embedding_service,
            llm_service=self.llm_service,
            collection_name= "test_ingestion_bge"
        )

        print("AI Knowledge Assistant ready.")