from sentence_transformers import CrossEncoder


class RerankerService:
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.model = CrossEncoder(self.model_name)

    def rerank(self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        
        if not documents:
            return []

        pairs = [(query, document) for document in documents]
        scores = self.model.predict(pairs)
        ranked = sorted(
            enumerate(scores),
            key=lambda x: float(x[1]),
            reverse=True,
        )

        return [
            (index, float(score))
            for index, score in ranked[:top_k]
        ]
    
    def retrieve(
        self,
        query: str,
        collection_name: str,
        retrieval_k: int = 15,
        top_k: int = 5,
    ):
        collection = self.chroma_service.get_collection(collection_name)

        query_embedding = self.embedding_service.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=retrieval_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            return []

        reranked = self.reranker_service.rerank(
            query=query,
            documents=documents,
            top_k=top_k,
        )

        final_results = []

        for index, score in reranked:
            final_results.append(
                {
                    "text": documents[index],
                    "metadata": metadatas[index],
                    "distance": distances[index],
                    "rerank_score": score,
                }
            )

        return final_results