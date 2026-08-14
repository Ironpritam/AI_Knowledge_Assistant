# from app.services.vector.retrieval_service import RetrievalService
# from app.services.llm.llm_service import LLMService


class RAGService:
    # def __init__(self,
    #     embedding_model: str = "bge-small",
    #     llm_provider: str = "ollama",
    #     llm_model: str = "qwen3:8b",
    #     collection_name: str = "documents",
    # ):
        
    #     self.retriever = RetrievalService(embedding_model=embedding_model,collection_name=collection_name,)
    #     self.llm = LLMService(provider=llm_provider,model=llm_model,)

    def __init__(self,
        retrieval_service,
        llm_service,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def _build_context(self,results: list[dict],) -> str:
        grouped_by_page: dict[tuple[str, int], list[dict]] = {}

        for result in results:
            metadata = result["metadata"]
            page_key = (
                metadata.get("source", "unknown"),
                int(metadata.get("page", 0)),
            )
            grouped_by_page.setdefault(page_key, []).append(result)

        context_parts = []
        for index, ((source, page), page_results) in enumerate(
            sorted(
                grouped_by_page.items(),
                key=lambda item: (item[0][0], item[0][1]),
            ),
            start=1,
        ):
            ordered_chunks = sorted(
                page_results,
                key=lambda item: int(item["metadata"].get("chunk_index", 0)),
            )
            page_text = "\n\n".join(
                chunk["text"].strip()
                for chunk in ordered_chunks
                if chunk.get("text")
            ).strip()

            if not page_text:
                continue

            chunk_numbers = ", ".join(
                str(int(chunk["metadata"].get("chunk_index", 0)))
                for chunk in ordered_chunks
            )

            context_parts.append(
                f"[Source {index}]\n"
                f"Document: {source}\n"
                f"Page: {page}\n"
                f"Chunks: {chunk_numbers}\n\n"
                f"{page_text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _build_prompt(self,question: str,context: str,) -> str:
        return f"""
            You are a document question-answering assistant.

            Answer the user's question using ONLY the provided context.

            Rules:
            1. Do not use outside knowledge.
            2. If the answer cannot be found in the context, say that the information is not available in the provided document.
            3. Do not invent facts.
            4. Give a complete answer that covers the key points, not a fragmentary response.
            5. Use 2-5 sentences or a short bullet list when it helps explain clearly.
            6. When possible, mention the relevant source page.

            Context:

            {context}

            User question:

            {question}
            """
    
    # def ask(self,question: str,top_k: int = 5,) -> dict:
    #     results = self.retrieval_service.search(query=question,top_k=top_k,)

    #     context = self._build_context(results)
    
    def ask(self,
        question: str,
        collection_name: str = "test_ingestion_bge",
        top_k: int = 5,
        document_id: str | None = None,
    ) -> dict:

        retrieval_top_k = max(top_k, 12)
        retrieved_chunks = self.retrieval_service.retrieve(
            query=question,
            collection_name=collection_name,
            top_k=retrieval_top_k,
            document_id=document_id,
        )

        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "No relevant document chunks were found in the selected collection.",
                "sources": [],
            }

        context = self._build_context(retrieved_chunks)

        prompt = self._build_prompt(question=question,context=context,)
        answer = self.llm_service.generate(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    **result["metadata"],
                    "collection_name": collection_name,
                    "distance": result["distance"],
                }
                for result in retrieved_chunks[:top_k]
            ],
        }
