import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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

REVIEW_PROMPT_FILE = os.path.join(PROMPT_DIR, "review_prompt.txt")
GENERATE_QUESTIONS_PROMPT_FILE = os.path.join(PROMPT_DIR, "generate_questions_prompt.txt")

@app.get("/generate-questions")
async def generate_questions():
    try:
        cv_file_path = "resume/cv1_extracted.txt"
        cv_review_file_path = "data/comprehensive_analysis.txt"

        missing_files = []
        existing_files = []

        if not os.path.exists(cv_file_path):
            missing_files.append(f"CV file: {cv_file_path}")
        else:
            existing_files.append(f"CV file: {cv_file_path}")

        if not os.path.exists(cv_review_file_path):
            missing_files.append(f"CV review file: {cv_review_file_path}")
        else:
            existing_files.append(f"CV review file: {cv_review_file_path}")

        if not os.path.exists(GENERATE_QUESTIONS_PROMPT_FILE):
            missing_files.append(f"Prompt file: {GENERATE_QUESTIONS_PROMPT_FILE}")
        else:
            existing_files.append(f"Prompt file: {GENERATE_QUESTIONS_PROMPT_FILE}")

        print(f"Existing files: {existing_files}")
        print(f"Missing files: {missing_files}")

        if missing_files:
            raise HTTPException(
                status_code=404,
                detail=f"Missing required files: {', '.join(missing_files)}. Existing files: {', '.join(existing_files)}"
            )

        # Read CV text from file
        with open(cv_file_path, "r", encoding='utf-8') as f:
            cv_text = f.read().strip()

        # Read CV review from file
        with open(cv_review_file_path, "r", encoding='utf-8') as f:
            cv_review_text = f.read().strip()

        # Load prompt from file
        with open(GENERATE_QUESTIONS_PROMPT_FILE, "r", encoding='utf-8') as f:
            prompt = f.read()

        # Combine prompt, CV text, and CV review
        combined_input = f"{prompt}\n\nCV CONTENT:\n{cv_text}\n\nCV REVIEW:\n{cv_review_text}"

        # Call OpenAI
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": combined_input}
            ],
            max_completion_tokens=65000
        )

        ai_response = response.choices[0].message.content.strip()

        # Save response to questions.txt
        questions_file_path = os.path.join(DATA_DIR, "questions.txt")

        with open(questions_file_path, "w", encoding='utf-8') as f:
            f.write(ai_response)

        # Return response
        return JSONResponse(content={
            "response": ai_response,
            "response_file": "questions.txt",
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

# -------- Endpoints --------
@app.get("/review-profile")
async def review_profile():
    try:
        # Read CV text from file
        cv_file_path = "resume/cv1_extracted.txt"
        if not os.path.exists(cv_file_path):
            raise HTTPException(status_code=404, detail="CV file not found at resume/cv1_extracted.txt")

        with open(cv_file_path, "r", encoding='utf-8') as f:
            cv_text = f.read().strip()

        # Load prompt from file
        if not os.path.exists(REVIEW_PROMPT_FILE):
            raise HTTPException(status_code=500, detail="Review prompt file not found")

        with open(REVIEW_PROMPT_FILE, "r", encoding='utf-8') as f:
            prompt = f.read()

        # Combine prompt and CV text
        combined_input = f"{prompt}\n\nCV CONTENT:\n{cv_text}"

        # Call OpenAI
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": combined_input}
            ],
            max_completion_tokens=65000
        )

        ai_response = response.choices[0].message.content.strip()

        # Generate UUID and save response to file
        file_uuid = str(uuid.uuid4())
        response_file_path = os.path.join(DATA_DIR, f"{file_uuid}_response.txt")

        with open(response_file_path, "w", encoding='utf-8') as f:
            f.write(ai_response)

        # Return response
        return JSONResponse(content={
            "file_id": file_uuid,
            "response": ai_response,
            "response_file": f"{file_uuid}_response.txt",
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")





# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy", "message": "Resume review service is running"})

