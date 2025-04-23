from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.auth import (
    get_current_user,
    get_current_user_from_token,
    require_role,
)

from app.config import USER_UPLOAD_PDF_PATH, DEFAULT_PDF_PATH
from app.utils.pdf_loader import process_pdf_and_store
import os

router = APIRouter()


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin", "premium")),
    db: Session = Depends(get_db),
):
    with open(USER_UPLOAD_PDF_PATH, "wb") as f:
        f.write(await file.read())

    msg = process_pdf_and_store(USER_UPLOAD_PDF_PATH)
    return {"status": "success", "detail": msg}


@router.post("/reset-pdf")
async def reset_pdf(
    current_user: User = Depends(require_role("admin", "premium")),
    db: Session = Depends(get_db),
):
    msg = process_pdf_and_store(DEFAULT_PDF_PATH)
    return {"status": "reset", "detail": msg}
