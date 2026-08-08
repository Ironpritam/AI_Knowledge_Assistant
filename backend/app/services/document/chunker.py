from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:

    def __init__(self,chunk_size: int = 800,chunk_overlap: int = 120,):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def chunk_pages(self,pages: list[dict],source_filename: str,) -> list[dict]:
        chunks = []
        global_chunk_index = 0

        for page in pages:

            page_number = page["page"]
            text = page["text"].strip()

            if not text:
                continue

            page_chunks = self.splitter.split_text(text)

            for chunk_text in page_chunks:
                chunks.append(
                    {
                        "text": chunk_text,
                        "metadata": {
                            "source": source_filename,
                            "page": page_number,
                            "chunk_index": global_chunk_index,
                        },
                    }
                )
                global_chunk_index += 1

        return chunks