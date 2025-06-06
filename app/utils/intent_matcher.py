from app.utils.button_loader import load_button_data

def match_intent(user_input: str) -> dict | None:
    """
    Rule-based intent matcher using keyword scanning from button data.
    Returns the first matched button dictionary, or None.
    """
    user_input_lower = user_input.lower()

    for button in load_button_data():
        keywords = button.get("question_keywords", [])
        if not keywords:
            continue

        for keyword in keywords:
            if keyword.strip().lower() in user_input_lower:
                return button 
    return None  
