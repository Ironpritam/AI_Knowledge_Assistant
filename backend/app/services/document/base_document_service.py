from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseDocumentService(ABC):
    @staticmethod
    @abstractmethod
    def extract_document(file_path: Path) -> dict:
        raise NotImplementedError
