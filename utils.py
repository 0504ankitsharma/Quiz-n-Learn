from PyPDF2 import PdfReader
import pandas as pd

def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def calculate_score(mcqs, user_answers):
    total_points = len(mcqs) * 20  # Each question is worth 20 points
    earned_points = sum(20 for idx, mcq in enumerate(mcqs) 
                       if user_answers[idx] == mcq['answer'])
    percentage = (earned_points / total_points) * 100
    return earned_points, total_points, percentage

def get_grade(percentage):
    if percentage >= 90: return "A", "Excellent!"
    elif percentage >= 80: return "B", "Very Good!"
    elif percentage >= 70: return "C", "Good!"
    elif percentage >= 60: return "D", "Pass!"
    else: return "F", "Need Improvement!"