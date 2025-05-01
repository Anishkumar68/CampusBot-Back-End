from fastapi import APIRouter, HTTPException
from app.utils.button_loader import get_button_questions, load_button_data

router = APIRouter()


@router.get("/buttons", tags=["Quick Buttons"])
async def get_quick_buttons():
    return {"buttons": get_button_questions()}


@router.get("/buttons/{button_id}", tags=["Quick Buttons"])
async def get_button_detail(button_id: str):
    for btn in load_button_data():
        if btn["id"] == button_id:
            return btn
    raise HTTPException(status_code=404, detail="Button not found")
