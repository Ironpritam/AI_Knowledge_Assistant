from pathlib import Path

from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = BASE_DIR / "models"


EMBEDDING_MODELS = {
    "bge-small": MODELS_DIR / "bge-small-en-v1.5",
    "qwen-0.6b": MODELS_DIR / "qwen3-embedding-0.6b",
}


class EmbeddingService:

    def __init__(self, model_name: str = "bge-small"):

        if model_name not in EMBEDDING_MODELS:
            raise ValueError(
                f"Unknown embedding model: {model_name}. "
                f"Available models: {list(EMBEDDING_MODELS)}"
            )

        self.model_key = model_name
        self.model_path = EMBEDDING_MODELS[model_name]

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Embedding model not found: {self.model_path}"
            )

        self.model = SentenceTransformer(
            str(self.model_path)
        )

    def embed_query(
        self,
        query: str,
    ) -> list[float]:

        if self.model_key == "qwen-0.6b":

            embedding = self.model.encode(
                query,
                prompt_name="query",
                normalize_embeddings=True,
            )

        else:

            embedding = self.model.encode(
                query,
                normalize_embeddings=True,
            )

        return embedding.tolist()

    def embed_document(
        self,
        text: str,
    ) -> list[float]:

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()