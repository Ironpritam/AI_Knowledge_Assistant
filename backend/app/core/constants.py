from pathlib import Path


API_PREFIX = "/api/v1"

MAX_FILE_SIZE_MB = 25

SUPPORTED_DOCUMENTS = [
    ".pdf",
    ".docx",
    ".txt",
]


# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]

VECTOR_DB_DIR = BASE_DIR / "storage" / "vector_db"