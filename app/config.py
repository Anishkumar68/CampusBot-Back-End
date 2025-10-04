# app/utils/config.py

import os
from pathlib import Path

# Base directory of the project (assuming this file is in app/utils/)
BASE_DIR = Path(__file__).resolve().parent.parent

# PDF / Upload paths
DEFAULT_PDF_PATH = BASE_DIR / "rag" / "default.pdf"
USER_UPLOAD_PDF_PATH = BASE_DIR / "uploads" / "user_upload.pdf"

# Make sure upload directories exist
(USER_UPLOAD_PDF_PATH.parent).mkdir(parents=True, exist_ok=True)
DEFAULT_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

# Vector index storage path
VECTOR_INDEX_PATH = BASE_DIR / "vector_index"
VECTOR_INDEX_PATH.mkdir(parents=True, exist_ok=True)

# Helping data JSON (student help / FAQ content)
HELPING_DATA_JSON = BASE_DIR / "data" / "helping_data.json"
(HELPING_DATA_JSON.parent).mkdir(parents=True, exist_ok=True)

# URL list file (each line a website URL to index / crawl)
URLS_LIST_FILE = BASE_DIR / "data" / "urls.txt"
(URLS_LIST_FILE.parent).mkdir(parents=True, exist_ok=True)

# Other config constants (chunk sizes, overlap, etc.)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
