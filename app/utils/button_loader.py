import csv
from typing import List, Dict
import os


# Safe path for your CSV
csv_path = os.path.join(os.path.dirname(__file__), "../rag/quickbuttons(Sheet1).csv")


def load_button_data(file_path: str = csv_path) -> List[Dict]:
    buttons = []
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            buttons.append(
                {
                    "id": row.get("id", "").strip(),
                    "question_keywords": (
                        [kw.strip() for kw in row["question_keywords"].split(",")]
                        if row.get("question_keywords")
                        else []
                    ),
                    "question_text": row.get("question_text", "").strip(),
                    "answer_text": row.get("answer_text", "").strip(),
                    "intent_type": row.get("intent_type", "").strip(),
                    "topic_tag": row.get("topic_tag", "").strip(),
                    "response_type": row.get("response_type", "rule").strip(),
                }
            )
    return buttons


def get_button_questions() -> List[Dict[str, str]]:
    return [
        {"id": button["id"], "question": button["question_text"]}
        for button in load_button_data()
    ]
