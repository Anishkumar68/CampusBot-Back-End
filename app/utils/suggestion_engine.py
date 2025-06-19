from app.utils.button_loader import load_button_data
from random import sample
from typing import List, Dict


def get_rule_based_suggestions(message: str):
    suggestions = []

    msg = message.lower()

    if "financial aid" in msg:
        suggestions = [
            "What documents are needed?",
            "What’s the deadline?",
            "Is FAFSA required?",
        ]
    elif "admission" in msg:
        suggestions = [
            "How do I apply?",
            "What are the admission requirements?",
            "Is there an application fee?",
        ]
    elif "housing" in msg:
        suggestions = [
            "What are the housing options?",
            "How do I apply for housing?",
            "What is the cost of housing?",
        ]
    elif "registration" in msg:
        suggestions = [
            "How do I register for classes?",
            "What is the registration deadline?",
            "Can I change my schedule after registration?",
        ]
    elif "transcript" in msg:
        suggestions = [
            "How do I request my transcript?",
            "Is there a fee for transcripts?",
            "How long does it take to process a transcript request?",
        ]
    elif "graduation" in msg:
        suggestions = [
            "What are the graduation requirements?",
            "When is the graduation ceremony?",
            "How do I apply for graduation?",
        ]
    elif "student services" in msg:
        suggestions = [
            "What services are available to students?",
            "How do I access student services?",
            "Are there any workshops or events for students?",
        ]
    elif "academic advising" in msg:
        suggestions = [
            "How do I schedule an advising appointment?",
            "What is the role of an academic advisor?",
            "Can I change my major with my advisor's help?",
        ]
    elif "campus events" in msg:
        suggestions = [
            "What events are happening this week?",
            "How do I find out about campus events?",
            "Are there any upcoming workshops or seminars?",
        ]
    elif "library" in msg:
        suggestions = [
            "What are the library hours?",
            "How do I access online resources?",
            "Can I reserve a study room?",
        ]
    elif "career services" in msg:
        suggestions = [
            "How do I find job opportunities?",
            "What career counseling services are available?",
            "Are there any resume workshops?",
        ]
    elif "health services" in msg:
        suggestions = [
            "What health services are available on campus?",
            "How do I make an appointment with health services?",
            "Are there any mental health resources?",
        ]
    elif "transportation" in msg:
        suggestions = [
            "What transportation options are available?",
            "Is there a campus shuttle service?",
            "How do I get a parking permit?",
        ]
    elif "international students" in msg:
        suggestions = [
            "What resources are available for international students?",
            "How do I apply for a student visa?",
            "Are there any orientation programs for international students?",
        ]
    elif "student organizations" in msg:
        suggestions = [
            "How do I join a student organization?",
            "What organizations are available on campus?",
            "Are there any leadership opportunities in student organizations?",
        ]
    elif "financial literacy" in msg:
        suggestions = [
            "What financial literacy resources are available?",
            "Are there any workshops on budgeting and saving?",
            "How do I manage student loans effectively?",
        ]
    elif "scholarships" in msg:
        suggestions = [
            "What scholarships are available?",
            "How do I apply for scholarships?",
            "What are the eligibility criteria for scholarships?",
        ]
    elif "student rights" in msg:
        suggestions = [
            "What are my rights as a student?",
            "How do I report a violation of student rights?",
            "Are there any resources for understanding student rights?",
        ]
    else:
        # Load button data for general suggestions
        button_data = load_button_data()
        if button_data:
            # Randomly select 3 suggestions from the loaded data
            suggestions = sample(button_data, min(3, len(button_data)))
        else:
            suggestions = ["How can I assist you further?"]

    return suggestions
