from app.utils.button_loader import load_button_data
from random import sample
from typing import List, Dict


def get_rule_based_suggestions(
    topic_tag: str, exclude_id: str, count: int = 2
) -> List[Dict]:
    """
    Returns up to `count` rule-based button suggestions matching the given topic,
    excluding the original button by ID.
    """
    all_buttons = load_button_data()

    if not suggestions:
        suggestions = [btn for btn in all_buttons if btn.get("id") != exclude_id]
    return sample(suggestions, min(count, len(suggestions)))

    # Filter buttons based on topic tag and exclude the original button ID
    # and ensure the response type is "rule"

    suggestions = [
        btn
        for btn in all_buttons
        if btn.get("response_type", "rule") == "rule"
        and btn.get("topic_tag", "").strip().lower() == topic_tag.strip().lower()
        and btn.get("id") != exclude_id
    ]

    return sample(suggestions, min(count, len(suggestions)))
