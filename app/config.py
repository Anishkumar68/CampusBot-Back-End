import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PDF_PATH = os.path.join(BASE_DIR, "../default_docs/default.pdf")
USER_UPLOAD_PDF_PATH = os.path.join(BASE_DIR, "../uploads/user_upload.pdf")
VECTOR_INDEX_PATH = os.path.join(BASE_DIR, "../vector_index")

# Ensure the uploads directory exists
if not os.path.exists(os.path.dirname(USER_UPLOAD_PDF_PATH)):
    os.makedirs(os.path.dirname(USER_UPLOAD_PDF_PATH))
