import chromadb
from pathlib import Path

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

    def __init__(self, persist_directory: Path | None = None):
        self.client = chromadb.PersistentClient(
            path=str(persist_directory or VECTOR_DB_DIR)
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

        ids = [
            (
                f"{chunk['metadata']['document_id']}_{chunk['metadata']['chunk_index']}"
                if "document_id" in chunk["metadata"]
                else f"{chunk['metadata']['source']}_{chunk['metadata']['chunk_index']}"
            )
            for chunk in chunks
        ]
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
        where: dict | None = None,
    ) -> list[dict]:

        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        if where is not None:
            query_args["where"] = where

        results = collection.query(**query_args)

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

    def get_document_chunks_count(
        self,
        collection_name: str,
        document_id: str,
    ) -> int:
        """
        Get the count of chunks for a specific document in the collection.
        
        Args:
            collection_name: Name of the collection
            document_id: Document ID to count chunks for
            
        Returns:
            Number of chunks found for the document
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            # Query with the where filter to count matching documents
            results = collection.get(where={"document_id": document_id})
            return len(results.get("ids", []))
        except Exception:
            return 0

    def delete_document_chunks(
        self,
        collection_name: str,
        document_id: str,
    ) -> None:
        """
        Delete all chunks for a specific document from ChromaDB.
        
        Uses document_id in metadata to identify chunks to delete.
        
        Args:
            collection_name: Name of the collection
            document_id: Document ID to delete chunks for
            
        Raises:
            ValueError: If collection doesn't exist or delete fails
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Count chunks before deletion (for logging)
            count_before = collection.count()
            
            # Delete chunks where document_id matches
            collection.delete(where={"document_id": document_id})
            
            # Verify deletion
            count_after = collection.count()
            deleted_count = count_before - count_after
            
            if deleted_count == 0:
                raise ValueError(
                    f"No chunks deleted for document {document_id} in collection {collection_name}. "
                    f"This may indicate the document_id was not stored in chunk metadata."
                )
                
        except Exception as exc:
            raise ValueError(
                f"Failed to delete document chunks for {document_id} "
                f"in collection {collection_name}: {str(exc)}"
            ) from exc
