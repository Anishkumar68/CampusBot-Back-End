from fastapi import APIRouter, HTTPException
from app.utils.button_loader import get_button_questions, load_button_data

router = APIRouter()


@router.get("/", tags=["Quick Buttons"])
async def get_quick_buttons():
    return {"buttons": get_button_questions()}


@router.get("/{button_id}", tags=["Quick Buttons"])
async def get_button_detail(button_id: str):
    for btn in load_button_data():
        if btn["id"] == button_id:
            return btn
    raise HTTPException(status_code=404, detail="Button not found")


@router.get("/all", tags=["Quick Buttons"])
async def get_all_buttons():
    buttons = load_button_data()
    if not buttons:
        raise HTTPException(status_code=404, detail="No buttons found")
    return {"buttons": buttons}


@router.get("/all/{button_id}", tags=["Quick Buttons"])
async def get_all_button_detail(button_id: str):
    buttons = load_button_data()
    for btn in buttons:
        if btn["id"] == button_id:
            return btn
    raise HTTPException(status_code=404, detail="Button not found")


@router.get("/all/{button_id}/questions", tags=["Quick Buttons"])
async def get_all_button_questions(button_id: str):
    buttons = load_button_data()
    for btn in buttons:
        if btn["id"] == button_id:
            return {"questions": btn.get("questions", [])}
    raise HTTPException(status_code=404, detail="Button not found")
