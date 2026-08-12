import chromadb

from app.core.constants import VECTOR_DB_DIR



# class ChromaService:
#     def __init__(self,
#             collection_name: str = "documents",
#             embedding_model: str = "bge-small",
#             embedding_dimension: int | None = None,
#         ):
        
#         self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
#         metadata = {"embedding_model": embedding_model,}

#         if embedding_dimension is not None:
#             metadata["embedding_dimension"] = embedding_dimension
#         self.collection = self.client.get_or_create_collection(name=collection_name,metadata=metadata,)

class ChromaService:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR)
        )

    def get_collection(self,
        collection_name: str,
        embedding_model: str,
        embedding_dimension: int,
    ):
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "embedding_model": embedding_model,
                "embedding_dimension": embedding_dimension,
            },
        )

        self._validate_embedding_model(
            collection=collection,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
        )

        return collection

    def _validate_embedding_model(self,
        collection,
        embedding_model: str,
        embedding_dimension: int,
    ) -> None:

        metadata = collection.metadata or {}

        stored_model = metadata.get("embedding_model")
        stored_dimension = metadata.get("embedding_dimension")

        if (stored_model is not None and stored_model != embedding_model):
            raise ValueError(
                f"Embedding model mismatch. "
                f"Collection uses '{stored_model}', "
                f"but '{embedding_model}' was requested."
            )

        if (stored_dimension is not None and stored_dimension != embedding_dimension):
            raise ValueError(
                f"Embedding dimension mismatch. "
                f"Collection uses {stored_dimension} dimensions, "
                f"but {embedding_dimension} were requested."
            )

    def add_chunks(self,
        collection,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> None:

        ids = [f"{chunk['metadata']['source']}_{chunk['metadata']['chunk_index']}" for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(self,
        collection,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        return [
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def count(self, collection) -> int:
        return collection.count()