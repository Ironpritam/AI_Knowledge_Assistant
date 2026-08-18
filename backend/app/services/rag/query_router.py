import re
from dataclasses import dataclass
from enum import Enum

import numpy as np


class QueryIntent(str, Enum):
    CONVERSATIONAL = "conversational"
    DOCUMENT = "document"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


@dataclass
class QueryRoute:
    intent: QueryIntent
    confidence: float
    scores: dict[str, float]


class QueryIntentRouter:
    """
    Lightweight semantic query router.

    Reuses the application's existing EmbeddingService.
    No additional model is loaded.
    """

    DEFAULT_PROTOTYPES = {
        QueryIntent.CONVERSATIONAL: [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
            "how is it going",
            "how are you doing",
            "thanks",
            "thank you",
            "thank you very much",
            "bye",
            "goodbye",
            "see you later",
            "nice to talk to you",
            "what can you do",
            "what's up",
            "how's it going",
            "good night",
            "greetings",
        ],
        QueryIntent.DOCUMENT: [
            "what does the document say about this?",
            "what does the PDF say about this topic?",
            "according to the document, what is this?",
            "explain this topic from the uploaded document",
            "what are the main points discussed in the document?",
            "summarize the document",
            "what are the objectives described in the document?",
            "what does the document say about this subject?",
            "find information about this topic in the uploaded documents",
            "according to the uploaded documents, explain this",
            "what does this document say?",
            "what does the document say about this topic?",
            "according to the document, what is this?",
            "what does the PDF say about this?",
            "give me a summary of the uploaded file",
            "extract the key ideas from this document",
            "what are the key findings in this paper?",
            "tell me the main takeaways from the file",
            "what conclusions are mentioned in the document?",
            "summarize the report for me",
        ],
        QueryIntent.HYBRID: [
            "hello, can you explain this topic from the document?",
            "hi, what does the document say about this?",
            "good morning, can you explain this from the PDF?",
            "thanks, now explain this topic from the document",
            "hey, can you tell me what the uploaded document says about this?",
            "hello, what does this document say?",
            "hey, can you tell me what the PDF says about this?",
            "good evening, summarize the uploaded document for me",
            "hi there, can you explain the key points in this file?",
            "how are you? can you summarize the document for me?",
        ],
    }

    def __init__(
        self,
        embedding_service,
        conversation_threshold: float = 0.55,
        document_threshold: float = 0.55,
    ):
        self.embedding_service = embedding_service
        self.conversation_threshold = conversation_threshold
        self.document_threshold = document_threshold
        self._prototype_embeddings = self._build_prototypes()

    def _build_prototypes(self) -> dict[str, np.ndarray]:
        """Generate prototype embeddings once when the router is initialized."""
        prototypes: dict[str, np.ndarray] = {}

        for intent, examples in self.DEFAULT_PROTOTYPES.items():
            embeddings = self.embedding_service.embed_classifications(examples)
            prototypes[intent.value] = np.asarray(embeddings)

        return prototypes

    def _contains_phrase(self, text: str, phrase: str) -> bool:
        normalized_text = re.sub(r"[^a-z0-9\s']+", " ", text.lower())
        normalized_phrase = re.sub(r"[^a-z0-9\s']+", " ", phrase.lower())

        text_tokens = re.findall(r"[a-z0-9']+", normalized_text)
        phrase_tokens = re.findall(r"[a-z0-9']+", normalized_phrase)

        if not phrase_tokens:
            return False

        if len(phrase_tokens) == 1:
            return phrase_tokens[0] in text_tokens

        for i in range(len(text_tokens) - len(phrase_tokens) + 1):
            if text_tokens[i : i + len(phrase_tokens)] == phrase_tokens:
                return True

        return False

    def classify(self, query: str) -> QueryRoute:
        query = query.strip()
        if not query:
            return QueryRoute(intent=QueryIntent.UNKNOWN, confidence=0.0, scores={})

        normalized_query = query.lower()
        q_emb = np.asarray(self.embedding_service.embed_query(query))

        conv = self._prototype_embeddings.get(QueryIntent.CONVERSATIONAL.value)
        doc = self._prototype_embeddings.get(QueryIntent.DOCUMENT.value)
        hybrid = self._prototype_embeddings.get(QueryIntent.HYBRID.value)

        conversation_score = float(np.max(np.dot(conv, q_emb))) if conv is not None else 0.0
        document_score = float(np.max(np.dot(doc, q_emb))) if doc is not None else 0.0
        hybrid_score = float(np.max(np.dot(hybrid, q_emb))) if hybrid is not None else 0.0

        scores = {
            "conversation": conversation_score,
            "document": document_score,
            "hybrid": hybrid_score,
        }

        casual_keywords = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
            "how's it going",
            "what's up",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "see you later",
            "good night",
        ]
        greeting_match = any(
            self._contains_phrase(normalized_query, keyword) for keyword in casual_keywords
        )

        document_keywords = [
            "document",
            "pdf",
            "according to",
            "summarize",
            "summary",
            "summarise",
            "explain",
            "what does this say",
            "key points",
            "main points",
            "objectives",
            "uploaded file",
            "report",
            "paper",
            "findings",
            "extract",
        ]
        document_match = any(
            self._contains_phrase(normalized_query, keyword) for keyword in document_keywords
        )

        if greeting_match and document_match and (
            hybrid_score >= 0.85
            or (conversation_score >= 0.65 and document_score >= 0.75 and hybrid_score >= 0.75)
        ):
            return QueryRoute(
                intent=QueryIntent.HYBRID,
                confidence=max(conversation_score, document_score),
                scores=scores,
            )

        if document_match and document_score >= 0.6:
            return QueryRoute(
                intent=QueryIntent.DOCUMENT,
                confidence=document_score,
                scores=scores,
            )

        if greeting_match:
            return QueryRoute(
                intent=QueryIntent.CONVERSATIONAL,
                confidence=max(conversation_score, 0.5),
                scores=scores,
            )

        if (
            document_match
            and conversation_score >= self.conversation_threshold
            and document_score >= self.document_threshold
            and abs(conversation_score - document_score) < 0.08
            and hybrid_score >= max(conversation_score, document_score)
        ):
            return QueryRoute(
                intent=QueryIntent.HYBRID,
                confidence=max(conversation_score, document_score),
                scores=scores,
            )

        if conversation_score >= self.conversation_threshold and conversation_score > document_score + 0.08:
            return QueryRoute(
                intent=QueryIntent.CONVERSATIONAL,
                confidence=conversation_score,
                scores=scores,
            )

        if document_score >= self.document_threshold and document_score > conversation_score + 0.08:
            return QueryRoute(
                intent=QueryIntent.DOCUMENT,
                confidence=document_score,
                scores=scores,
            )

        if conversation_score >= self.conversation_threshold:
            return QueryRoute(
                intent=QueryIntent.CONVERSATIONAL,
                confidence=conversation_score,
                scores=scores,
            )

        if document_score >= self.document_threshold:
            return QueryRoute(
                intent=QueryIntent.DOCUMENT,
                confidence=document_score,
                scores=scores,
            )

        return QueryRoute(
            intent=QueryIntent.UNKNOWN,
            confidence=max(conversation_score, document_score),
            scores=scores,
        )