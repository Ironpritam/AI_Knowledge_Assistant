# from app.services.vector.retrieval_service import RetrievalService
# from app.services.llm.llm_service import LLMService
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.document import Document
from app.services.rag.query_router import (
    DocumentRetrievalStrategy,
    QueryIntent,
    QueryIntentRouter,
)


class RAGService:
    def __init__(
        self,
        retrieval_service,
        llm_service,
        db: Session | None = None,
        query_router: QueryIntentRouter | None = None,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.db = db
        self.query_router = query_router

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
            2. If unavailable in the context, say it is not available in the provided document.
            3. Do not invent facts.
            4. Give a complete answer that covers the key points, not a fragmentary response.
            5. Use 2-5 sentences or a short bullet list when it helps explain clearly.
            6. When possible, mention the relevant source page.
            7. Treat retrieved context as authoritative; prior chat messages are background only.

            Context:

            {context}

            User question:

            {question}
            """

    def _build_coverage_instruction(
        self,
        document_ids: list[UUID] | None,
        results: list[dict],
    ) -> tuple[str, int]:
        filename_map = self._get_document_filenames_map(
            [str(document_id) for document_id in document_ids or []]
        )
        result_filenames = {
            str(result["metadata"].get("document_id")): result["metadata"].get("source")
            for result in results
            if result["metadata"].get("document_id")
        }
        selected_document_ids = list(
            dict.fromkeys(str(document_id) for document_id in document_ids or [])
        )
        if not selected_document_ids:
            selected_document_ids = list(result_filenames)

        text_sizes = {
            document_id: sum(
                len(str(result.get("text", "")))
                for result in results
                if str(result["metadata"].get("document_id")) == document_id
            )
            for document_id in selected_document_ids
        }
        document_count = len(selected_document_ids)
        total_text_size = sum(text_sizes.values())

        max_output_tokens = max(
            settings.LLM_MAX_OUTPUT_TOKENS,
            settings.RAG_COVERAGE_MAX_OUTPUT_TOKENS,
        )
        minimum_per_document = min(
            settings.RAG_COVERAGE_MIN_TOKENS_PER_DOCUMENT,
            max_output_tokens // document_count,
        )
        minimum_total = minimum_per_document * document_count
        base_output_tokens = max(settings.LLM_MAX_OUTPUT_TOKENS, minimum_total)
        text_scale = min(
            1.0,
            total_text_size / settings.RAG_COVERAGE_TEXT_CHARS_FOR_MAX_OUTPUT,
        )
        output_budget = round(
            base_output_tokens
            + (max_output_tokens - base_output_tokens) * text_scale
        )

        remaining_tokens = output_budget - minimum_total
        size_divisor = total_text_size or document_count
        token_targets = {
            document_id: minimum_per_document
            + int(remaining_tokens * text_sizes[document_id] / size_divisor)
            for document_id in selected_document_ids
        }
        undistributed_tokens = output_budget - sum(token_targets.values())
        for document_id in sorted(
            selected_document_ids,
            key=lambda item: text_sizes[item],
            reverse=True,
        )[:undistributed_tokens]:
            token_targets[document_id] += 1

        document_sections = []
        for document_id in selected_document_ids:
            filename = (
                filename_map.get(document_id)
                or result_filenames.get(document_id)
                or document_id
            )
            document_sections.append(
                f"- {filename}: approximately {token_targets[document_id]} tokens"
            )

        instruction = (
            "This is a multi-document coverage task. Write one clearly labeled "
            "section for every document below. Do not omit a document or combine "
            "them into one summary. If the retrieved content for a document is "
            "insufficient, state that explicitly under its heading. Keep each "
            "section concise, with at most four bullets. Use the per-document "
            "targets as a guide, not an exact requirement.\n\n"
            "Required document sections and target lengths:\n"
            + "\n".join(document_sections)
        )
        return instruction, output_budget

    @staticmethod
    def _build_history_context(conversation_history: list[dict] | None) -> str:
        if not conversation_history:
            return ""

        lines: list[str] = []
        for message in conversation_history:
            role = str(message.get("role", "")).strip().lower()
            content = str(message.get("content", "")).strip()
            if not role or not content:
                continue

            speaker = "User" if role == "user" else "Assistant"
            lines.append(f"{speaker}: {content}")

        return "\n".join(lines)

    @staticmethod
    def _compose_question_with_history(
        question: str,
        history_context: str,
    ) -> str:
        if not history_context:
            return question

        return (
            "Conversation history:\n"
            f"{history_context}\n\n"
            f"Current question: {question}"
        )
    
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
    
    def ask_qwen(
        self,
        question: str,
        collection_name: str = "test_all_0.0.0.0",
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
        model_id: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        return self.ask(
            question=question,
            collection_name=collection_name,
            top_k=top_k,
            document_ids=document_ids,
            model_id=model_id,
            conversation_history=conversation_history,
        )
    
    def ask(self,
        question: str,
        collection_name: str = "test_all_0.0.0.0",
        top_k: int = 5,
        document_ids: list[UUID] | None = None,
        model_id: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        history_context = self._build_history_context(conversation_history)
        effective_question = self._compose_question_with_history(
            question=question,
            history_context=history_context,
        )

        retrieval_strategy = QueryIntentRouter.document_retrieval_strategy(
            question,
            len(document_ids or []),
        )
        ensure_document_coverage = (
            retrieval_strategy == DocumentRetrievalStrategy.COVERAGE
        )

        if self.query_router is not None:
            route = self.query_router.classify(question)

            if (
                route.intent == QueryIntent.CONVERSATIONAL
                and not ensure_document_coverage
            ):
                system_content = (
                    "You are a helpful AI assistant. "
                    "Respond naturally and briefly to casual conversation. "
                    "Do not invent or discuss document content unless the user asks about it."
                )
                if history_context:
                    system_content += (
                        " Use the recent conversation context to keep references coherent."
                    )
                messages = [
                        {
                            "role": "system",
                            "content": system_content,
                        },
                        {
                            "role": "user",
                            "content": effective_question,
                        },
                    ]
                answer = self.llm_service.generate(messages=messages)
                return {
                    "question": question,
                    "answer": answer,
                    "model_id": model_id,
                    "sources": [],
                }

            if route.intent == QueryIntent.UNKNOWN and not ensure_document_coverage:
                system_content = (
                    "You are an AI knowledge assistant."
                    "The user's request is ambiguous."

                    "If they are asking about uploaded documents, ask them to "
                    "specify what they want to know."

                    "If they are making casual conversation, respond naturally."

                    "Do not invent information about the documents."
                )
                if history_context:
                    system_content += (
                        " Use the recent conversation context to resolve references."
                    )
                messages = [
                        {
                            "role": "system",
                            "content": system_content,
                        },
                        {
                            "role": "user",
                            "content": effective_question,
                        },
                    ]
                answer = self.llm_service.generate(messages=messages)
                return {
                    "question": question,
                    "answer": answer,
                    "model_id": model_id,
                    "sources": [],
                }
 
        retrieval_top_k = max(top_k, 12)
        retrieved_chunks = self.retrieval_service.retrieve(
            query=question,
            collection_name=collection_name,
            top_k=retrieval_top_k,
            document_ids=document_ids,
            ensure_document_coverage=ensure_document_coverage,
        )

        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "No relevant document chunks were found in the selected collection.",
                "model_id": model_id,
                "sources": [],
            }

        context = self._build_context(retrieved_chunks)

        prompt_sections = []
        coverage_output_budget = None
        if ensure_document_coverage:
            coverage_instruction, coverage_output_budget = (
                self._build_coverage_instruction(document_ids, retrieved_chunks)
            )
            prompt_sections.append(coverage_instruction)
        elif history_context:
            prompt_sections.append(
                "Recent conversation context:\n"
                f"{history_context}"
            )
        prompt_sections.append(
            self._build_prompt(question=question, context=context)
        )

        answer = ""
        for _ in range(2):
            generation_kwargs = (
                {"max_tokens": coverage_output_budget}
                if coverage_output_budget is not None
                else {}
            )
            generated_answer = self.llm_service.generate(
                messages=[
                    {
                        "role": "user",
                        "content": "\n\n".join(prompt_sections),
                    }
                ],
                **generation_kwargs,
            )
            if isinstance(generated_answer, str) and generated_answer.strip():
                answer = generated_answer.strip()
                break

        if not answer:
            answer = (
                "The language model returned an empty response. "
                "Please retry your question."
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
            if (
                "document_id" in result["metadata"]
                and result["metadata"]["document_id"] in filename_map
            ):
                source_data["source"] = filename_map[result["metadata"]["document_id"]]
            
            sources.append(source_data)

        return {
            "question": question,
            "answer": answer,
            "model_id": model_id,
            "sources": sources,
        }    
