from pathlib import Path

from app.services.document.chunker import DocumentChunker
from app.services.document.document_factory import DocumentFactory
# from app.services.vector.embedding_service import EmbeddingService
# from app.services.vector.chroma_service import ChromaService


class DocumentIngestionService:
    def __init__(self,
        embedding_service,
        chroma_service,
    ):
        self.chunker = DocumentChunker()

        self.embedding_service = embedding_service
        self.chroma_service = chroma_service

    def ingest(
        self,
        pdf_path: Path,
        collection_name: str = "test_all.0.0.0.0",
        document_id: str | None = None,
        source_filename: str | None = None,
    ) -> dict:
        pdf_data = DocumentFactory.extract_document(pdf_path)
        chunks = self.chunker.chunk_pages(
            pages=pdf_data["pages"],
            source_filename=source_filename or pdf_path.name,
        )

        if document_id is not None:
            for chunk in chunks:
                chunk["metadata"]["document_id"] = document_id

        texts = [chunk["text"]for chunk in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        collection = self.chroma_service.get_collection(
            collection_name=collection_name,
            embedding_model=self.embedding_service.model_key,
            embedding_dimension=self.embedding_service.dimension,
        )

        self.chroma_service.add_chunks(
            collection=collection,
            chunks=chunks,
            embeddings=embeddings,
        )

        return {
            "filename": pdf_path.name,
            "page_count": pdf_data["page_count"],
            "chunk_count": len(chunks),
            "embedding_model": self.embedding_service.model_key,
            "embedding_dimension": self.embedding_service.dimension,
            "vector_count": len(embeddings),
        }
