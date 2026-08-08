import re


class TextCleaner:

    @staticmethod
    def clean(text: str) -> str:
        # Normalize line endings
        text = text.replace("\r\n", "\n")

        # Remove PDF-extracted Markdown-style email links.
        #
        # Example:
        # \[email@example.com](mailto\:email@example.com)
        #
        # becomes:
        # ""
        text = re.sub(
            r"\\\[[^\]]+\]\(mailto\\:[^)]+\)",
            "",
            text,
        )

        # Remove excessive spaces and tabs
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove remaining escaped square brackets
        text = text.replace(r"\[", "")
        text = text.replace(r"\]", "")

        return text.strip()