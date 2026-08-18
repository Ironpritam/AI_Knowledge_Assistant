from pathlib import Path

from app.routers.document import ALLOWED_EXTENSIONS


def test_supported_document_extensions_include_office_text_and_code_files():
    supported = {
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
        ".txt", ".md", ".csv", ".json", ".html", ".css", ".sql",
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cc",
        ".cpp", ".cxx", ".h", ".hpp", ".rs", ".go", ".kt", ".swift",
        ".php", ".rb", ".cs", ".scala", ".sh", ".bash", ".yaml", ".yml",
    }

    assert supported.issubset(ALLOWED_EXTENSIONS)
