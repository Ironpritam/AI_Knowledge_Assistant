from pathlib import Path

from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = BASE_DIR / "models"


EMBEDDING_MODELS = {
    "bge-small": MODELS_DIR / "bge-small-en-v1.5",
    "qwen-0.6b": MODELS_DIR / "Qwen3-Embedding-0.6B-FP8",
    "qwen3-embedding-0.6b": MODELS_DIR / "Qwen3-Embedding-0.6B-FP8",
    "qwen3-embedding-0.6b-gguf": MODELS_DIR / "Qwen3-Embedding-0.6B-Q8_0.gguf",
    "nomic-v1.5": MODELS_DIR / "nomic-embed-text-v1.5",
}


class EmbeddingService:
    def __init__(self, model_name: str = "nomic-v1.5"):
        if model_name not in EMBEDDING_MODELS:
            raise ValueError(
                f"Unknown embedding model: {model_name}. "
                f"Available models: {list(EMBEDDING_MODELS)}"
            )

        self.model_key = model_name
        self.model_path = EMBEDDING_MODELS[model_name]

        # if self.model_path.suffix.lower() == ".gguf":
        #     raise ValueError(
        #         "The GGUF embedding file is not compatible with the current SentenceTransformer-based "
        #         "EmbeddingService. Use the local qwen3-embedding-0.6b folder or integrate a llama.cpp-based "
        #         "embedding backend for Qwen3-Embedding-0.6B-Q8_0.gguf."
        #     )

        if not self.model_path.exists():
            raise FileNotFoundError(f"Embedding model not found: {self.model_path}")

        self.model = SentenceTransformer(str(self.model_path))
        # print(f"Loaded embedding model: {model_name} from {self.model_path}")

    @property
    def dimension(self) -> int:
        return self.model.get_embedding_dimension()

    def embed_query(self,query: str,) -> list[float]:
        if self.model_key == "nomic-v1.5":
            text = f"search_query: {query}"
            embedding = self.model.encode(text,normalize_embeddings=True,)
        if self.model_key == "qwen-0.6b":
            embedding = self.model.encode(query,prompt_name="query",normalize_embeddings=True,)
        else:
            embedding = self.model.encode(query,normalize_embeddings=True,)

        return embedding.tolist()


    def embed_document(self,text: str,) -> list[float]:
        if self.model_key == "nomic-v1.5":
            text = f"search_document: {text}"
        embedding = self.model.encode(text,normalize_embeddings=True,)

        return embedding.tolist()


    def embed_documents(self,texts: list[str],) -> list[list[float]]:
        if self.model_key == "nomic-v1.5":
            texts = [
                f"search_document: {text}"
                for text in texts
            ]
        embeddings = self.model.encode(texts,normalize_embeddings=True,)
        return embeddings.tolist()

    
    def embed_classification(self, text: str) -> list[float]:
        if self.model_key == "nomic-v1.5":
            text = f"classification: {text}"

        embedding = self.model.encode(text,normalize_embeddings=True,)
        return embedding.tolist()


    def embed_classifications(self,texts: list[str],) -> list[list[float]]:
        if self.model_key == "nomic-v1.5":
            texts = [
                f"classification: {text}"
                for text in texts
            ]

        embeddings = self.model.encode(texts,normalize_embeddings=True,)
        return embeddings.tolist()