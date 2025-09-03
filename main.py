import uuid
import os
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

# Initialize app and OpenAI
load_dotenv()
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = "data"
PROMPT_DIR = "prompts"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROMPT_DIR, exist_ok=True)

# prompt files
REVIEW_PROMPT_FILE = os.path.join(PROMPT_DIR, "review_prompt.txt")
GENERATE_PROMPT_FILE = os.path.join(PROMPT_DIR, "generate_prompt.txt")


# -------- Models --------
class GenerateProfileInput(BaseModel):
    file_id: str
    review_profile_file_id: str
    questions: list  # Changed from dict to list of question-answer objects


# -------- Helper functions --------
def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    reader = PdfReader(pdf_file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def call_openai(prompt: str, text: str) -> str:
    """Helper to call OpenAI API"""
    response = client.chat.completions.create(
        model="gpt-4o",  # Or gpt-4 / gpt-3.5-turbo
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# -------- Endpoints --------
@app.post("/review-profile")
async def review_profile(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file)

        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # Load prompt
        if not os.path.exists(REVIEW_PROMPT_FILE):
            raise HTTPException(status_code=500, detail="Review prompt file not found")

        with open(REVIEW_PROMPT_FILE, "r", encoding='utf-8') as f:
            review_prompt = f.read()

        # Call OpenAI
        raw_response = call_openai(review_prompt, extracted_text)

        # Parse JSON response
        try:
            # Try to parse the JSON response
            parsed_review = json.loads(raw_response)
            structured_review = parsed_review.get("resume_review", "")
            questions = parsed_review.get("questions", [])
        except json.JSONDecodeError:
            # Fallback: if JSON parsing fails, use raw response
            structured_review = raw_response
            questions = []
            print(f"Warning: Could not parse JSON response for file {file.filename}")

        # Generate UUID for file identification
        file_uuid = str(uuid.uuid4())

        # Save original CV text in separate file
        cv_file_path = os.path.join(DATA_DIR, f"{file_uuid}_cv.txt")
        with open(cv_file_path, "w", encoding='utf-8') as f:
            f.write(extracted_text)

        # Save only the raw AI response in review file (no formatting, no headers)
        review_file_path = os.path.join(DATA_DIR, f"{file_uuid}_review.txt")
        with open(review_file_path, "w", encoding='utf-8') as f:
            f.write(raw_response)

        # Build simplified response
        return JSONResponse(content={
            "file_id": file_uuid,
            "cv_file": f"{file_uuid}_cv.txt",
            "review_file": f"{file_uuid}_review.txt",
            "resume_review": structured_review,
            "questions": questions,
            "original_filename": file.filename,
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


# Updated Models
class GenerateProfileInput(BaseModel):
    file_id: str
    questions: list  # List of question-answer objects


@app.post("/generate-profile")
async def generate_profile(input_data: GenerateProfileInput):
    try:
        file_uuid = input_data.file_id

        # Define file paths
        cv_file_path = os.path.join(DATA_DIR, f"{file_uuid}_cv.txt")
        review_file_path = os.path.join(DATA_DIR, f"{file_uuid}_review.txt")

        # Check if required files exist
        if not os.path.exists(cv_file_path):
            raise HTTPException(status_code=404, detail=f"CV file not found: {file_uuid}_cv.txt")

        if not os.path.exists(review_file_path):
            raise HTTPException(status_code=404, detail=f"Review file not found: {file_uuid}_review.txt")

        # Load CV content
        with open(cv_file_path, "r", encoding='utf-8') as f:
            cv_content = f.read()

        # Load review content (raw AI response)
        with open(review_file_path, "r", encoding='utf-8') as f:
            review_content = f.read()

        # Load generation prompt
        if not os.path.exists(GENERATE_PROMPT_FILE):
            raise HTTPException(status_code=500, detail="Generate prompt file not found")

        with open(GENERATE_PROMPT_FILE, "r", encoding='utf-8') as f:
            generate_prompt = f.read()

        # Format questions and answers for better readability
        formatted_questions = "\n".join([
            f"Q: {qa.get('question', 'N/A')}\nA: {qa.get('answer', 'N/A')}\n"
            for qa in input_data.questions
        ])

        # Prepare comprehensive input for resume generation
        combined_input = f"""ORIGINAL CV:
{cv_content}

REVIEW ASSESSMENT:
{review_content}

CLARIFICATION QUESTIONS AND ANSWERS:
{formatted_questions}

---
Please generate an improved resume based on the original CV, the detailed review assessment, and the provided answers to clarification questions."""

        # Call OpenAI for final resume generation
        improved_resume = call_openai(generate_prompt, combined_input)

        # Generate timestamp for tracking
        from datetime import datetime
        generation_timestamp = datetime.now().isoformat()

        # Save the improved resume
        improved_resume_path = os.path.join(DATA_DIR, f"{file_uuid}_improved_resume.txt")
        with open(improved_resume_path, "w", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("IMPROVED RESUME\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"File ID: {file_uuid}\n")
            f.write(f"Generation Timestamp: {generation_timestamp}\n")
            f.write(f"Questions Answered: {len(input_data.questions)}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("ENHANCED RESUME CONTENT\n")
            f.write("=" * 80 + "\n")
            f.write(improved_resume)

            if input_data.questions:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("ANSWERED CLARIFICATION QUESTIONS\n")
                f.write("=" * 80 + "\n")
                f.write(formatted_questions)

        # Prepare response
        response_data = {
            "file_id": file_uuid,
            "improved_resume": improved_resume,
            "improved_resume_file": f"{file_uuid}_improved_resume.txt",
            "generation_metadata": {
                "timestamp": generation_timestamp,
                "questions_answered": len(input_data.questions),
                "source_files": {
                    "cv_file": f"{file_uuid}_cv.txt",
                    "review_file": f"{file_uuid}_review.txt"
                }
            },
            "success": True
        }

        return JSONResponse(content=response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating profile: {str(e)}")


# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy", "message": "Resume review service is running"})

