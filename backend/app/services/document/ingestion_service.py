from pathlib import Path

from app.services.document.pdf_service import PDFService
from app.services.document.chunker import DocumentChunker
# from app.services.vector.embedding_service import EmbeddingService
# from app.services.vector.chroma_service import ChromaService


class DocumentIngestionService:
    # def __init__(self,embedding_model: str = "bge-small",collection_name: str = "documents",):
    #     self.chunker = DocumentChunker()
    #     self.embedding_service = EmbeddingService(model_name=embedding_model)
        
    #     self.vector_store = ChromaService(
    #         collection_name=collection_name,
    #         embedding_model=self.embedding_service.model_key,
    #         embedding_dimension=self.embedding_service.dimension,
    #     )
    #     self.vector_store.validate_embedding_model(
    #         embedding_model=self.embedding_service.model_key,
    #         embedding_dimension=self.embedding_service.dimension,
    #     )
    def __init__(self,
        embedding_service,
        chroma_service,
    ):
        self.chunker = DocumentChunker()

        self.embedding_service = embedding_service
        self.chroma_service = chroma_service
    

    # def ingest(self,pdf_path: Path,) -> dict:
    #     pdf_data = PDFService.extract_document(pdf_path)
    #     chunks = self.chunker.chunk_pages(
    #         pages=pdf_data["pages"],
    #         source_filename=pdf_path.name,
    #     )

    #     texts = [chunk["text"]for chunk in chunks]
    #     embeddings = (self.embedding_service.embed_documents(texts))

    #     self.vector_store.add_chunks(chunks=chunks,embeddings=embeddings,)

    #     return {
    #         "filename": pdf_path.name,
    #         "page_count": pdf_data["page_count"],
    #         "chunk_count": len(chunks),
    #         "embedding_model": (
    #             self.embedding_service.model_key
    #         ),
    #         "embedding_dimension": (
    #             self.embedding_service.dimension
    #         ),
    #         "vector_count": self.vector_store.count(),
    #     }

    def ingest(self, pdf_path: Path, collection_name: str = "documents",) -> dict:
        pdf_data = PDFService.extract_document(pdf_path)
        chunks = self.chunker.chunk_pages(
            pages=pdf_data["pages"],
            source_filename=pdf_path.name,
        )

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
            "vector_count": self.chroma_service.count(collection),
        }