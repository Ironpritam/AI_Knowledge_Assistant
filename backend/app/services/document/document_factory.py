from pathlib import Path

from app.services.document.code_document_service import CodeDocumentService
from app.services.document.office_document_service import OfficeDocumentService
from app.services.document.pdf_service import PDFService
from app.services.document.text_document_service import TextDocumentService


class DocumentFactory:
    TEXT_EXTENSIONS = {
        ".txt", ".md", ".csv", ".json", ".html", ".htm", ".css",
        ".sql", ".xml", ".yaml", ".yml", ".log",
    }
    OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
    CODE_EXTENSIONS = CodeDocumentService.CODE_EXTENSIONS

    @staticmethod
    def extract_document(file_path: Path) -> dict:
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return PDFService.extract_document(file_path)
        if extension in DocumentFactory.OFFICE_EXTENSIONS:
            return OfficeDocumentService.extract_document(file_path)
        if extension in DocumentFactory.TEXT_EXTENSIONS:
            return TextDocumentService.extract_document(file_path)
        if extension in DocumentFactory.CODE_EXTENSIONS:
            return CodeDocumentService.extract_document(file_path)

        raise ValueError(f"Unsupported file type: {extension}")
