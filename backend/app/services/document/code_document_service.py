from pathlib import Path

from app.services.document.base_document_service import BaseDocumentService
from app.services.document.text_cleaner import TextCleaner


class CodeDocumentService(BaseDocumentService):
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cc", ".cpp",
        ".cxx", ".h", ".hpp", ".rs", ".go", ".kt", ".swift", ".php", ".rb",
        ".cs", ".scala", ".sh", ".bash",
    }

    @staticmethod
    def extract_document(file_path: Path) -> dict:
        extension = file_path.suffix.lower()
        if extension not in CodeDocumentService.CODE_EXTENSIONS:
            raise ValueError(f"Unsupported code format: {extension}")

        text = file_path.read_text(encoding="utf-8", errors="replace")
        return {
            "filename": file_path.name,
            "page_count": 1,
            "metadata": {"source_type": extension.lstrip("."), "file_type": extension},
            "pages": [{"page": 1, "text": TextCleaner.clean(text)}],
        }
