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
        context_parts = []
        for index, result in enumerate(results,start=1,):
            metadata = result["metadata"]
            context_parts.append(
                f"[Source {index}]\n"
                f"Document: {metadata['source']}\n"
                f"Page: {metadata['page']}\n"
                f"Chunk: {metadata['chunk_index']}\n\n"
                f"{result['text']}"
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
            4. Give a concise, direct answer.
            5. When possible, mention the relevant source page.

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
        collection_name: str = "documents",
        top_k: int = 5,
    ) -> dict:

        retrieved_chunks = self.retrieval_service.retrieve(
            query=question,
            collection_name=collection_name,
            top_k=top_k,
        )
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
                result["metadata"]
                for result in retrieved_chunks
            ],
        }