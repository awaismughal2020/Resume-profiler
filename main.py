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
        model="gpt-4-turbo",  # Or gpt-4 / gpt-3.5-turbo
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

        # Save extracted text in file with UUID
        file_uuid = str(uuid.uuid4())

        # Save original extracted text
        original_file_path = os.path.join(DATA_DIR, f"{file_uuid}_original.txt")
        with open(original_file_path, "w", encoding='utf-8') as f:
            f.write(extracted_text)

        # Save the structured review as JSON
        review_json_path = os.path.join(DATA_DIR, f"{file_uuid}_review.json")
        review_data = {
            "file_uuid": file_uuid,
            "original_filename": file.filename,
            "structured_review": structured_review,
            "questions": questions,
            "raw_response": raw_response,
        }

        with open(review_json_path, "w", encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

        # Save the comprehensive review file (formatted text)
        review_profile_file_path = os.path.join(DATA_DIR, f"{file_uuid}_review_profile.txt")
        with open(review_profile_file_path, "w", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPLETE RESUME REVIEW ASSESSMENT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"File ID: {file_uuid}\n")
            f.write(f"Original Filename: {file.filename}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("ORIGINAL RESUME TEXT\n")
            f.write("=" * 80 + "\n")
            f.write(extracted_text)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("DETAILED REVIEW ASSESSMENT\n")
            f.write("=" * 80 + "\n")
            f.write(structured_review)

            if questions:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("CLARIFICATION QUESTIONS\n")
                f.write("=" * 80 + "\n")
                for i, question in enumerate(questions, 1):
                    f.write(f"{i}. {question}\n")

        # Build response with properly structured data
        file_info = {
            "file_uuid": file_uuid,
            "original_filename": file.filename,
            "files_created": {
                "original_text": f"{file_uuid}_original.txt",
                "review_json": f"{file_uuid}_review.json"
            }
        }

        return JSONResponse(content={
            "file": file_uuid,
            "review_profile_file": f"{file_uuid}_review.json",
            "resume_review": structured_review,  # Clean text review
            "questions": questions,  # Parsed questions array
            "file_info": file_info,
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@app.post("/generate-profile")
async def generate_profile(input_data: GenerateProfileInput):
    try:
        file_uuid = input_data.file_id
        review_profile_file_id = input_data.review_profile_file_id

        # Validate that file_id and review_profile_file_id match
        if file_uuid != review_profile_file_id:
            # Extract UUID from review_profile_file_id if it contains the full filename
            if review_profile_file_id.endswith('_review_profile.txt'):
                extracted_uuid = review_profile_file_id.replace('_review_profile.txt', '')
                if extracted_uuid != file_uuid:
                    raise HTTPException(
                        status_code=400,
                        detail="file_id and review_profile_file_id do not match"
                    )
            # Also handle _review.json format
            elif review_profile_file_id.endswith('_review.json'):
                extracted_uuid = review_profile_file_id.replace('_review.json', '')
                if extracted_uuid != file_uuid:
                    raise HTTPException(
                        status_code=400,
                        detail="file_id and review_profile_file_id do not match"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid review_profile_file_id format or mismatch with file_id"
                )

        # Define file paths
        original_file_path = os.path.join(DATA_DIR, f"{file_uuid}_original.txt")
        review_profile_path = os.path.join(DATA_DIR, f"{file_uuid}_review_profile.txt")
        review_json_path = os.path.join(DATA_DIR, f"{file_uuid}_review.json")

        # Check if required files exist
        if not os.path.exists(original_file_path):
            raise HTTPException(status_code=404, detail=f"Original file not found: {file_uuid}_original.txt")

        if not os.path.exists(review_profile_path):
            raise HTTPException(status_code=404,
                                detail=f"Review profile file not found: {file_uuid}_review_profile.txt")

        # Load original profile text
        with open(original_file_path, "r", encoding='utf-8') as f:
            original_profile_text = f.read()

        # Load review profile content
        with open(review_profile_path, "r", encoding='utf-8') as f:
            review_profile_content = f.read()

        # Load structured review data if available
        structured_review_data = {}
        if os.path.exists(review_json_path):
            with open(review_json_path, "r", encoding='utf-8') as f:
                structured_review_data = json.load(f)

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
        combined_input = f"""ORIGINAL RESUME TEXT:
{original_profile_text}

COMPLETE REVIEW ASSESSMENT:
{review_profile_content}

CLARIFICATION QUESTIONS AND ANSWERS:
{formatted_questions}

STRUCTURED REVIEW DATA (for reference):
{json.dumps(structured_review_data, indent=2, ensure_ascii=False)}

---
Please generate an improved resume based on the original resume, the detailed review assessment, and the provided answers to clarification questions."""

        # Call OpenAI for final resume generation
        improved_resume = call_openai(generate_prompt, combined_input)

        # Generate timestamp for tracking
        from datetime import datetime
        generation_timestamp = datetime.now().isoformat()

        # Save the improved resume with comprehensive metadata
        improved_resume_path = os.path.join(DATA_DIR, f"{file_uuid}_improved_resume.txt")
        with open(improved_resume_path, "w", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("IMPROVED RESUME GENERATED\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"File ID: {file_uuid}\n")
            f.write(f"Review Profile File ID: {review_profile_file_id}\n")
            f.write(f"Generation Timestamp: {generation_timestamp}\n")
            f.write(f"Questions Answered: {len(input_data.questions)}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("IMPROVED RESUME CONTENT\n")
            f.write("=" * 80 + "\n")
            f.write(improved_resume)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("CLARIFICATION ANSWERS PROVIDED\n")
            f.write("=" * 80 + "\n")
            f.write(formatted_questions)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("GENERATION METADATA\n")
            f.write("=" * 80 + "\n")
            f.write(f"Original File: {file_uuid}_original.txt\n")
            f.write(f"Review File: {review_profile_file_id}\n")
            f.write(f"Questions Count: {len(input_data.questions)}\n")
            f.write(f"Generation Method: AI-Enhanced Resume Optimization\n")

        # Save generation metadata as JSON
        generation_metadata = {
            "file_id": file_uuid,
            "review_profile_file_id": review_profile_file_id,
            "generation_timestamp": generation_timestamp,
            "questions_count": len(input_data.questions),
            "questions_provided": input_data.questions,  # Store original list format
            "files_used": {
                "original_file": f"{file_uuid}_original.txt",
                "review_profile_file": f"{file_uuid}_review_profile.txt",
                "review_json_file": f"{file_uuid}_review.json"
            },
            "output_file": f"{file_uuid}_improved_resume.txt"
        }

        generation_metadata_path = os.path.join(DATA_DIR, f"{file_uuid}_generation_metadata.json")
        with open(generation_metadata_path, "w", encoding='utf-8') as f:
            json.dump(generation_metadata, f, indent=2, ensure_ascii=False)

        # Prepare response
        response_data = {
            "file_id": file_uuid,
            "review_profile_file_id": review_profile_file_id,
            "improved_resume": improved_resume,
            "improved_resume_file": f"{file_uuid}_improved_resume.txt",
            "generation_metadata": {
                "timestamp": generation_timestamp,
                "questions_answered": len(input_data.questions),
                "files_processed": {
                    "original_file": f"{file_uuid}_original.txt",
                    "review_file": review_profile_file_id,
                    "output_file": f"{file_uuid}_improved_resume.txt"
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

