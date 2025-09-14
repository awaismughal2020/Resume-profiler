from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid
import tempfile
from pathlib import Path
import uvicorn
from pydantic import BaseModel
from typing import Optional
import json

# Import your existing CVAnalyzer class
from streamlit_app import CVAnalyzer, read_pdf_with_pdfplumber, read_pdf_with_pypdf2, clean_and_format_text

# Create FastAPI app
app = FastAPI(
    title="CV Analyzer API",
    description="API for CV Analysis and Enhancement",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs("resume", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("prompts", exist_ok=True)

# Global CVAnalyzer instance
cv_analyzer = None


def get_cv_analyzer(api_key: str = None, model: str = "o1-mini"):
    """Get CVAnalyzer instance"""
    global cv_analyzer
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    if not cv_analyzer or (api_key and cv_analyzer.client.api_key != api_key):
        cv_analyzer = CVAnalyzer(gpt_model=model, api_key=api_key)
    return cv_analyzer


# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    model: str = "o1-mini"


class QuestionsRequest(BaseModel):
    model: str = "o1-mini"
    cv_path: str
    analysis_path: str
    session_id: str


class AuthRequest(BaseModel):
    password: str


# Authentication
@app.post("/api/auth")
async def authenticate(auth_request: AuthRequest):
    """Authenticate user"""
    correct_password = os.getenv("CV_ANALYZER_PASSWORD", "Abc123!@#7")
    if auth_request.password == correct_password:
        return {"authenticated": True}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cv-analyzer-api"}


# Upload and extract CV
@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload PDF and extract text"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Generate session ID
    session_id = str(uuid.uuid4())[:8]

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Extract text using your existing functions
        text_content = read_pdf_with_pdfplumber(tmp_file_path)
        if not text_content:
            text_content = read_pdf_with_pypdf2(tmp_file_path)

        if not text_content:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")

        # Clean and format text
        cleaned_text = clean_and_format_text(text_content)

        # Save extracted text
        extracted_file_path = f"resume/cv{session_id}_extracted.txt"
        with open(extracted_file_path, "w", encoding='utf-8') as f:
            f.write(cleaned_text)

        # Clean up temporary file
        os.unlink(tmp_file_path)

        return {
            "session_id": session_id,
            "extracted_cv_path": extracted_file_path,
            "text_preview": cleaned_text,
            "character_count": len(cleaned_text),
            "success": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


# Analyze CV
@app.post("/api/analyze-cv/{session_id}")
async def analyze_cv(session_id: str, request: AnalysisRequest):
    """Analyze CV using your existing CVAnalyzer"""
    try:
        # Get CVAnalyzer instance
        api_key = os.getenv('OPENAI_API_KEY')

        analyzer = get_cv_analyzer(api_key, request.model)

        # Path to extracted CV
        cv_path = f"resume/cv{session_id}_extracted.txt"

        if not os.path.exists(cv_path):
            raise HTTPException(status_code=404, detail="CV file not found. Please upload first.")

        # Run analysis using your existing method
        results = analyzer.analyze_cv(cv_path, session_id)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# Generate questions
@app.post("/api/generate-questions")
async def generate_questions(request: QuestionsRequest):
    """Generate questions using your existing method"""
    try:
        # Get CVAnalyzer instance
        api_key = os.getenv('OPENAI_API_KEY')
        analyzer = get_cv_analyzer(api_key, request.model)

        # Generate questions using your existing method
        results = analyzer.generate_questions(
            request.cv_path,
            request.analysis_path,
            request.session_id
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


# Get analysis results
@app.get("/api/analysis/{session_id}")
async def get_analysis(session_id: str):
    """Get analysis results for a session"""
    analysis_file = f"data/{session_id}_comprehensive_analysis.txt"

    if not os.path.exists(analysis_file):
        raise HTTPException(status_code=404, detail="Analysis not found")

    with open(analysis_file, "r", encoding='utf-8') as f:
        content = f.read()

    return {"content": content, "session_id": session_id}


# Get questions results
@app.get("/api/questions/{session_id}")
async def get_questions(session_id: str):
    """Get questions results for a session"""
    questions_file = f"data/{session_id}_questions.txt"

    if not os.path.exists(questions_file):
        raise HTTPException(status_code=404, detail="Questions not found")

    with open(questions_file, "r", encoding='utf-8') as f:
        content = f.read()

    return {"content": content, "session_id": session_id}


# Enhanced resume generation (for the second app)
class EnhancedResumeRequest(BaseModel):
    model: str = "o1-mini"
    cv_text: str
    analysis_text: str
    qa_data: dict
    generate_resume_prompt: str


@app.post("/api/generate-enhanced-resume")
async def generate_enhanced_resume(request: EnhancedResumeRequest):
    """Generate enhanced resume based on Q&A responses"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        analyzer = get_cv_analyzer(api_key, request.model)

        # Format Q&A responses
        qa_text = "\n\nDETAILED QUESTION-ANSWER RESPONSES:\n"
        for i, (question, answer) in enumerate(request.qa_data.items(), 1):
            qa_text += f"\nQ{i}: {question}\nA{i}: {answer}\n"

        # Combine all inputs
        combined_input = f"{request.generate_resume_prompt}\n\nORIGINAL CV:\n{request.cv_text}\n\nCOMPREHENSIVE ANALYSIS:\n{request.analysis_text}{qa_text}"

        # Call OpenAI
        response = analyzer.client.chat.completions.create(
            model=analyzer.gpt_model,
            messages=[{"role": "user", "content": combined_input}],
            max_completion_tokens=65000
        )

        enhanced_resume = response.choices[0].message.content.strip()

        # Generate session ID
        session_id = str(uuid.uuid4())[:8]

        # Save results
        structured_data = {
            "session_id": session_id,
            "cv_text": request.cv_text,
            "analysis_text": request.analysis_text,
            "generate_resume_prompt": request.generate_resume_prompt,
            "qa_data": request.qa_data,
            "enhanced_resume": enhanced_resume,
            "model_used": request.model,
            "timestamp": str(uuid.uuid4())
        }

        # Save to file
        output_file = os.path.join("data", f"{session_id}_enhanced_cv.json")
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)

        return {
            "enhanced_resume": enhanced_resume,
            "session_id": session_id,
            "success": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating resume: {str(e)}")


# Serve static files (optional, if you want to serve HTML from the same container)
# app.mount("/static", StaticFiles(directory="web"), name="static")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEV_MODE", "false").lower() == "true"
    )
