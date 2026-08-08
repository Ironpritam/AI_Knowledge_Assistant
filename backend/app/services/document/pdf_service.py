from pathlib import Path
import fitz


class PDFService:
    @staticmethod
    def extract_document(pdf_path: Path) -> dict:
        """
        Extract text and metadata from a PDF.
        """

        try:
            document = fitz.open(pdf_path)

        except Exception as e:
            raise RuntimeError(f"Unable to process PDF: {e}")

        pages = []

        for page_number, page in enumerate(document, start=1):

            pages.append(
                {
                    "page": page_number,
                    "text": page.get_text("text")
                }
            )

        result = {
            "filename": pdf_path.name,
            "page_count": len(document),
            "metadata": document.metadata,
            "pages": pages,
        }

        document.close()

        return result