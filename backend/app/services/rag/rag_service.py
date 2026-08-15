# from app.services.vector.retrieval_service import RetrievalService
# from app.services.llm.llm_service import LLMService
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.document import Document


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
        db: Session | None = None,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.db = db

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
    
    def _get_document_filenames_map(self, document_ids: list[str]) -> dict[str, str]:
        """
        Get a mapping of document_id to original_filename from the database.
        
        Optimized to:
        - Only fetch needed columns (id, original_filename)
        - Use batch query (not N+1)
        - Handle empty or None document_ids gracefully
        
        Args:
            document_ids: List of document IDs to look up
            
        Returns:
            Dictionary mapping document_id to original_filename
        """
        if not document_ids or self.db is None:
            return {}
        
        # Filter out None/empty values
        valid_ids = [doc_id for doc_id in document_ids if doc_id]
        if not valid_ids:
            return {}
        
        # Query only needed columns for efficiency
        stmt = select(Document.id, Document.original_filename).filter(
            Document.id.in_([UUID(doc_id) for doc_id in valid_ids])
        )
        results = self.db.execute(stmt).all()
        
        # Build mapping from document_id to original_filename
        return {str(doc_id): filename for doc_id, filename in results}
    
    # def ask(self,question: str,top_k: int = 5,) -> dict:
    #     results = self.retrieval_service.search(query=question,top_k=top_k,)

    #     context = self._build_context(results)
    
    def ask(self,
        question: str,
        collection_name: str = "test_all_0.0.0.0",
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
        model_id: str | None = None,
    ) -> dict:

        retrieval_top_k = max(top_k, 12)
        retrieved_chunks = self.retrieval_service.retrieve(
            query=question,
            collection_name=collection_name,
            top_k=retrieval_top_k,
            document_ids=document_ids,
        )

        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "No relevant document chunks were found in the selected collection.",
                "model_id": model_id,
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

        # Get document IDs from retrieved chunks to fetch original filenames
        doc_ids_in_results = set()
        for result in retrieved_chunks[:top_k]:
            doc_id = result["metadata"].get("document_id")
            if doc_id:  # Only collect non-None IDs
                doc_ids_in_results.add(doc_id)
        
        # Batch query for filenames (single DB call, not N+1)
        filename_map = self._get_document_filenames_map(list(doc_ids_in_results))

        # Build sources list with original filenames
        sources = []
        for result in retrieved_chunks[:top_k]:
            source_data = {
                **result["metadata"],
                "collection_name": collection_name,
                "distance": result["distance"],
            }
            
            # Replace "source" with original_filename if document_id is available
            if "document_id" in result["metadata"] and result["metadata"]["document_id"] in filename_map:
                source_data["source"] = filename_map[result["metadata"]["document_id"]]
            
            sources.append(source_data)

        return {
            "question": question,
            "answer": answer,
            "model_id": model_id,
            "sources": sources,
        }
