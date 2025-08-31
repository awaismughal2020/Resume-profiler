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


def parse_resume_review_v3(review_text: str) -> dict:
    """Enhanced parser for v3.1 prompt format"""

    structured_response = {
        "header_block": {},
        "priority_assessment": [],
        "actionable_improvements": {"immediate": [], "strategic": []},
        "practical_examples": [],
        "clarification_questions": [],
        "next_steps": {},
        "raw_response": review_text
    }

    try:
        # Extract header block first
        header_match = re.search(r'=== RESUME ASSESSMENT HEADER ===(.*?)=== END HEADER ===',
                                 review_text, re.DOTALL)
        if header_match:
            header_content = header_match.group(1)
            for line in header_content.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    structured_response["header_block"][key.strip().lower().replace(' ', '_')] = value.strip()

        # Extract priority assessment
        priority_pattern = r'### PRIORITY ASSESSMENT(.*?)(?=###|$)'
        priority_match = re.search(priority_pattern, review_text, re.DOTALL)
        if priority_match:
            priority_content = priority_match.group(1)
            critical_items = re.findall(r'\*\*(CRITICAL-\d+|HIGH-\d+)\*\*:\s*(.+?)(?=\*\*|$)',
                                        priority_content, re.DOTALL)
            for item_id, description in critical_items:
                structured_response["priority_assessment"].append({
                    "id": item_id,
                    "description": description.strip()
                })

        # Extract actionable improvements
        improvements_pattern = r'### ACTIONABLE IMPROVEMENTS(.*?)(?=###|$)'
        improvements_match = re.search(improvements_pattern, review_text, re.DOTALL)
        if improvements_match:
            improvements_content = improvements_match.group(1)

            # Extract immediate actions
            immediate_pattern = r'\*\*Immediate Actions\*\*.*?:(.*?)(?=\*\*Strategic|$)'
            immediate_match = re.search(immediate_pattern, improvements_content, re.DOTALL)
            if immediate_match:
                immediate_items = re.findall(r'[-*]\s*(.+)', immediate_match.group(1))
                structured_response["actionable_improvements"]["immediate"] = [
                    {"action": item.strip()} for item in immediate_items
                ]

            # Extract strategic enhancements
            strategic_pattern = r'\*\*Strategic Enhancements\*\*.*?:(.*?)(?=###|$)'
            strategic_match = re.search(strategic_pattern, improvements_content, re.DOTALL)
            if strategic_match:
                strategic_items = re.findall(r'[-*]\s*(.+)', strategic_match.group(1))
                structured_response["actionable_improvements"]["strategic"] = [
                    {"enhancement": item.strip()} for item in strategic_items
                ]

        # Extract clarification questions
        questions_pattern = r'### CLARIFICATION QUESTIONS(.*?)(?=###|$)'
        questions_match = re.search(questions_pattern, review_text, re.DOTALL)
        if questions_match:
            questions_content = questions_match.group(1)
            question_items = re.findall(r'(\d+)\.\s*(.+?)(?=\d+\.|$)', questions_content, re.DOTALL)
            for num, question in question_items:
                structured_response["clarification_questions"].append({
                    "number": int(num),
                    "question": question.strip()
                })

        return structured_response

    except Exception as e:
        print(f"Parser error: {e}")
        # Fallback to original parsing logic
        return parse_resume_review(review_text)

def parse_resume_review(review_text: str) -> dict:
    """Parse the structured review response into JSON sections with robust error handling"""

    # Initialize the structured response
    structured_response = {
        "resume_overview_assessment": {},
        "detailed_gap_analysis": {},
        "clarification_questions": [],
        "immediate_improvement_recommendations": [],
        "ats_optimization_suggestions": {},
        "special_considerations": {},
        "sensitivity_support_notes": "",
        "raw_response": review_text  # Always include for debugging
    }

    try:
        # Debug: Print first 1000 chars of response to understand format
        print("=== FIRST 1000 CHARS OF OPENAI RESPONSE ===")
        print(review_text[:1000])
        print("=== END DEBUG ===")

        # Try multiple section header patterns
        section_patterns = [
            r'### (.*?)\n',  # ### SECTION NAME
            r'##\s*(.*?)\n',  # ## SECTION NAME
            r'\*\*([A-Z\s&:]+)\*\*\n',  # **SECTION NAME**
            r'^([A-Z\s&:]{10,}):?\s*\n',  # SECTION NAME: (caps, 10+ chars)
            r'^\d+\.\s*([A-Z\s&:]+)\s*\n'  # 1. SECTION NAME
        ]

        sections_found = None
        pattern_used = None

        for i, pattern in enumerate(section_patterns):
            sections = re.split(pattern, review_text, flags=re.MULTILINE)
            if len(sections) >= 5:  # Need at least 2-3 sections
                sections_found = sections
                pattern_used = pattern
                print(f"SUCCESS: Using pattern {i + 1}: {pattern}")
                print(f"Found {len(sections)} sections")
                break

        if not sections_found:
            print("No section patterns matched, using fallback parsing...")
            return parse_fallback_comprehensive(review_text, structured_response)

        # Process sections
        current_section = ""
        current_content = ""

        for i, section in enumerate(sections_found):
            if i == 0:  # Skip first element (content before first header)
                continue

            if i % 2 == 1:  # Odd indices are section headers
                # Save previous section if exists
                if current_section and current_content:
                    structured_response = process_section_robust(
                        structured_response, current_section, current_content
                    )

                current_section = section.strip()
                current_content = ""
                print(f"Processing section: '{current_section}'")
            else:  # Even indices are section content
                current_content = section.strip()

        # Process final section
        if current_section and current_content:
            structured_response = process_section_robust(
                structured_response, current_section, current_content
            )

        # Validation check
        total_items = (
                len(structured_response.get("clarification_questions", [])) +
                len(structured_response.get("immediate_improvement_recommendations", [])) +
                len(structured_response.get("detailed_gap_analysis", {})) +
                len(structured_response.get("resume_overview_assessment", {}))
        )

        if total_items == 0:
            print("WARNING: No content parsed successfully, using comprehensive fallback")
            return parse_fallback_comprehensive(review_text, structured_response)

        print(f"SUCCESS: Parsed {total_items} total items")
        return structured_response

    except Exception as e:
        print(f"ERROR in parsing: {e}")
        return parse_fallback_comprehensive(review_text, structured_response)


def parse_fallback_comprehensive(review_text: str, structured_response: dict) -> dict:
    """Comprehensive fallback parsing when structured parsing fails"""

    print("Using comprehensive fallback parsing...")

    # Extract questions using multiple patterns
    question_patterns = [
        r'\d+\.\s*(.+?\?)',  # 1. Question?
        r'Q\d*[:\.]?\s*(.+?\?)',  # Q: Question?
        r'Question[:\s]*(.+?\?)',  # Question: ...?
        r'^[•\-\*]\s*(.+?\?)$',  # • Question?
        r'(?:Can you|Could you|What|How|Why|When|Where|Which|Do you|Have you|Are you|Will you|Would you)\s+[^?]*\?'
        # Natural questions
    ]

    questions = []
    for pattern in question_patterns:
        matches = re.findall(pattern, review_text, re.MULTILINE | re.IGNORECASE)
        for match in matches[:15]:  # Limit to 15 per pattern
            if isinstance(match, str) and len(match.strip()) > 10:
                questions.append({
                    "category": "Extracted",
                    "question": match.strip()
                })
        if questions:  # Use first successful pattern
            break

    # Extract recommendations
    rec_patterns = [
        r'(?:recommend|suggest|improve|should|need to|must|consider)\s+([^.!?]+[.!?])',
        r'^\d+\.\s*(.{20,200}[.!])$',  # Numbered items
        r'^[•\-\*]\s*(.{20,200}[.!])$',  # Bullet points
    ]

    recommendations = []
    for pattern in rec_patterns:
        matches = re.findall(pattern, review_text, re.MULTILINE | re.IGNORECASE)
        for match in matches[:10]:  # Limit to 10 per pattern
            if isinstance(match, str) and len(match.strip()) > 15:
                recommendations.append({
                    "recommendation": match.strip()
                })
        if recommendations:
            break

    # Extract scores if present
    score_patterns = [
        r'(?:score|rating)[:\s]*(\d+(?:\.\d+)?)\s*[/\\]\s*(\d+)',
        r'(\d+(?:\.\d+)?)\s*[/\\]\s*10',
        r'(?:Overall|Total|Final)[:\s]*(\d+(?:\.\d+)?)'
    ]

    scores = {}
    for pattern in score_patterns:
        matches = re.findall(pattern, review_text, re.IGNORECASE)
        if matches:
            scores["extracted_scores"] = matches
            break

    # Extract key phrases for overview
    overview_keywords = [
        "overall", "impression", "strength", "weakness", "gap",
        "improvement", "recommendation", "target", "role", "experience"
    ]

    overview_content = []
    sentences = re.split(r'[.!?]+', review_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30:
            for keyword in overview_keywords:
                if keyword.lower() in sentence.lower():
                    overview_content.append(sentence)
                    break

    # Populate structured response
    if questions:
        structured_response["clarification_questions"] = questions[:20]
        print(f"Extracted {len(questions)} questions")

    if recommendations:
        structured_response["immediate_improvement_recommendations"] = recommendations
        print(f"Extracted {len(recommendations)} recommendations")

    if overview_content:
        structured_response["resume_overview_assessment"]["extracted_summary"] = " ".join(overview_content[:3])
        print(f"Extracted overview content")

    if scores:
        structured_response["resume_overview_assessment"]["scores"] = scores

    # Add basic gap analysis from common terms
    gap_indicators = re.findall(r'(?:missing|lacking|absent|need|require|should add)\s+([^.!?]{10,50})',
                                review_text, re.IGNORECASE)
    if gap_indicators:
        structured_response["detailed_gap_analysis"]["identified_gaps"] = gap_indicators[:10]

    # Extract ATS-related content
    ats_content = re.findall(r'(?:ATS|applicant tracking|keyword|parsing)[^.!?]*[.!?]',
                             review_text, re.IGNORECASE)
    if ats_content:
        structured_response["ats_optimization_suggestions"]["extracted_ats_advice"] = " ".join(ats_content[:3])

    print(
        f"Fallback parsing complete - extracted items: questions={len(structured_response.get('clarification_questions', []))}, recommendations={len(structured_response.get('immediate_improvement_recommendations', []))}")

    return structured_response


def process_section_robust(structured_response: dict, section_name: str, content: str) -> dict:
    """Robust section processing with flexible matching"""

    section_lower = section_name.lower().strip()
    print(f"Processing section: '{section_name}' -> normalized: '{section_lower}'")

    # Flexible section matching
    if any(keyword in section_lower for keyword in ['overview', 'assessment', 'impression', 'summary']):
        # Parse overview - look for key-value patterns
        overview_data = {}

        # Try different subsection patterns
        subsection_patterns = [
            r'\*\*([^*:]+):\*\*\s*([^*]+?)(?=\*\*|$)',  # **Key:** Value
            r'([A-Z][^:\n]{5,30}):\s*([^\n]+)',  # Key: Value
            r'^([A-Z\s]{10,}):\s*(.+?)$'  # CAPS KEY: value
        ]

        for pattern in subsection_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for key, value in matches:
                clean_key = re.sub(r'[^\w\s]', '', key).lower().replace(' ', '_').strip()
                if clean_key and len(value.strip()) > 5:
                    overview_data[clean_key] = value.strip()

        # If no subsections found, treat entire content as summary
        if not overview_data and len(content.strip()) > 20:
            overview_data["general_assessment"] = content.strip()

        structured_response["resume_overview_assessment"].update(overview_data)
        print(f"Extracted {len(overview_data)} overview items")

    elif any(keyword in section_lower for keyword in ['gap', 'analysis', 'deficien']):
        # Parse gaps
        gap_items = []

        # Extract bullet points and numbered items
        gap_patterns = [
            r'^[•\-\*\+]\s*(.+)$',  # Bullet points
            r'^\d+\.\s*(.+)$',  # Numbered items
            r'^([A-Z][^:\n]{10,100}):(.+)$'  # Category: Description
        ]

        for pattern in gap_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    gap_items.append(f"{match[0].strip()}: {match[1].strip()}")
                else:
                    gap_items.append(match.strip())

        if gap_items:
            structured_response["detailed_gap_analysis"]["identified_gaps"] = gap_items
            print(f"Extracted {len(gap_items)} gap items")

    elif any(keyword in section_lower for keyword in ['question', 'clarification']):
        # Parse questions
        questions = []
        current_category = "General"

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for category headers
            if (line.startswith('**') and line.endswith(':**')) or line.isupper():
                current_category = re.sub(r'[*:]', '', line).strip()
                continue

            # Extract questions
            if re.match(r'^\d+\.\s*.+\?', line):
                question_text = re.sub(r'^\d+\.\s*', '', line).strip()
                questions.append({
                    "category": current_category,
                    "question": question_text
                })
            elif '?' in line and len(line) > 15:
                questions.append({
                    "category": current_category,
                    "question": line
                })

        structured_response["clarification_questions"].extend(questions)
        print(f"Extracted {len(questions)} questions")

    elif any(keyword in section_lower for keyword in ['recommendation', 'improvement', 'suggest']):
        # Parse recommendations
        recommendations = []

        rec_patterns = [
            r'^\d+\.\s*(.+)$',  # 1. Recommendation
            r'^[•\-\*]\s*(.+)$',  # • Recommendation
            r'\*\*([^*]+)\*\*:\s*(.+)$'  # **Title**: Description
        ]

        for pattern in rec_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    recommendations.append({
                        "title": match[0].strip(),
                        "description": match[1].strip()
                    })
                else:
                    recommendations.append({"recommendation": match.strip()})

        structured_response["immediate_improvement_recommendations"].extend(recommendations)
        print(f"Extracted {len(recommendations)} recommendations")

    elif any(keyword in section_lower for keyword in ['ats', 'optimization', 'keyword']):
        # Parse ATS suggestions
        structured_response["ats_optimization_suggestions"]["content"] = content.strip()
        print("Added ATS optimization content")

    elif any(keyword in section_lower for keyword in ['special', 'consideration', 'next']):
        # Parse special considerations
        structured_response["special_considerations"]["content"] = content.strip()
        print("Added special considerations content")

    elif any(keyword in section_lower for keyword in ['sensitivity', 'support']):
        structured_response["sensitivity_support_notes"] = content.strip()
        print("Added sensitivity notes")

    return structured_response


def process_section(structured_response: dict, section_name: str, content: str) -> dict:
    """Process individual sections and add to structured response"""

    section_lower = section_name.lower().replace(" ", "_")

    if "resume_overview_assessment" in section_lower:
        # Parse overview assessment
        lines = content.split('\n')
        current_key = ""
        current_content = []

        for line in lines:
            if line.startswith('**') and line.endswith(':**'):
                # Save previous key-value pair
                if current_key:
                    structured_response["resume_overview_assessment"][current_key] = '\n'.join(current_content).strip()

                # Start new key
                current_key = line.replace('**', '').replace(':', '').strip().lower().replace(" ", "_")
                current_content = []
            elif line.strip():
                current_content.append(line.strip())

        # Save last key-value pair
        if current_key:
            structured_response["resume_overview_assessment"][current_key] = '\n'.join(current_content).strip()

    elif "detailed_gap_analysis" in section_lower:
        # Parse gap analysis
        gap_sections = re.split(r'\*\*(.*?):\*\*', content)

        for i in range(1, len(gap_sections), 2):
            if i + 1 < len(gap_sections):
                gap_type = gap_sections[i].strip().lower().replace(" ", "_").replace("&", "and")
                gap_content = gap_sections[i + 1].strip()

                # Parse bullet points
                gap_items = []
                for line in gap_content.split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        gap_items.append(line[1:].strip())
                    elif line and not line.startswith('**'):
                        gap_items.append(line)

                structured_response["detailed_gap_analysis"][gap_type] = gap_items

    elif "clarification_questions" in section_lower:
        # Parse questions
        questions = []
        current_category = ""

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('**') and line.endswith(':**'):
                current_category = line.replace('**', '').replace(':', '').strip()
            elif re.match(r'^\d+\.', line):
                question_text = re.sub(r'^\d+\.\s*', '', line).strip()
                questions.append({
                    "category": current_category,
                    "question": question_text
                })

        structured_response["clarification_questions"] = questions

    elif "immediate_improvement_recommendations" in section_lower:
        # Parse recommendations
        recommendations = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):
                rec_text = re.sub(r'^\d+\.\s*', '', line).strip()
                # Split title and description if format is "**Title**: Description"
                if '**' in rec_text and ':**' in rec_text:
                    title_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', rec_text)
                    if title_match:
                        recommendations.append({
                            "title": title_match.group(1).strip(),
                            "description": title_match.group(2).strip()
                        })
                    else:
                        recommendations.append({"recommendation": rec_text})
                else:
                    recommendations.append({"recommendation": rec_text})
            elif line.startswith('-') and line[1:].strip():
                recommendations.append({"recommendation": line[1:].strip()})

        structured_response["immediate_improvement_recommendations"] = recommendations

    elif "ats_optimization_suggestions" in section_lower:
        # Parse ATS suggestions
        ats_sections = re.split(r'\*\*(.*?):\*\*', content)

        for i in range(1, len(ats_sections), 2):
            if i + 1 < len(ats_sections):
                suggestion_type = ats_sections[i].strip().lower().replace(" ", "_")
                suggestion_content = ats_sections[i + 1].strip()
                structured_response["ats_optimization_suggestions"][suggestion_type] = suggestion_content

    elif "special_considerations" in section_lower:
        # Parse special considerations
        special_sections = re.split(r'\*\*(.*?):\*\*', content)

        for i in range(1, len(special_sections), 2):
            if i + 1 < len(special_sections):
                consideration_type = special_sections[i].strip().lower().replace(" ", "_")
                consideration_content = special_sections[i + 1].strip()
                structured_response["special_considerations"][consideration_type] = consideration_content

    elif "sensitivity" in section_lower:
        structured_response["sensitivity_support_notes"] = content.strip()

    return structured_response


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

        # Call OpenAI for clarification questions
        raw_response = call_openai(review_prompt, extracted_text)

        # Parse the response into structured format
        structured_review = parse_resume_review(raw_response)

        # Save extracted text in file with UUID
        file_uuid = str(uuid.uuid4())

        # Save original extracted text
        original_file_path = os.path.join(DATA_DIR, f"{file_uuid}_original.txt")
        with open(original_file_path, "w", encoding='utf-8') as f:
            f.write(extracted_text)

        # Save the structured review as JSON
        review_json_path = os.path.join(DATA_DIR, f"{file_uuid}_review.json")
        with open(review_json_path, "w", encoding='utf-8') as f:
            json.dump(structured_review, f, indent=2, ensure_ascii=False)

        # Save the complete resume review as formatted text file
        review_profile_file_path = os.path.join(DATA_DIR, f"{file_uuid}_review_profile.txt")
        with open(review_profile_file_path, "w", encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPLETE RESUME REVIEW ASSESSMENT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"File ID: {file_uuid}\n")
            f.write(f"Review Date: {str(uuid.uuid1().time)}\n")
            f.write(f"Original Filename: {file.filename}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("ORIGINAL RESUME TEXT\n")
            f.write("=" * 80 + "\n")
            f.write(extracted_text)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("DETAILED REVIEW ASSESSMENT\n")
            f.write("=" * 80 + "\n")
            f.write(raw_response)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("STRUCTURED ANALYSIS SUMMARY\n")
            f.write("=" * 80 + "\n")

            # Write structured summary
            if structured_review.get("resume_overview_assessment"):
                f.write("\n### OVERVIEW ASSESSMENT ###\n")
                for key, value in structured_review["resume_overview_assessment"].items():
                    f.write(f"\n{key.upper().replace('_', ' ')}:\n")
                    f.write(f"{value}\n")

            if structured_review.get("clarification_questions"):
                f.write(
                    f"\n### CLARIFICATION QUESTIONS ({len(structured_review['clarification_questions'])} total) ###\n")
                for i, q in enumerate(structured_review["clarification_questions"], 1):
                    f.write(f"\n{i}. [{q.get('category', 'General')}] {q.get('question', '')}\n")

            if structured_review.get("immediate_improvement_recommendations"):
                f.write(
                    f"\n### IMPROVEMENT RECOMMENDATIONS ({len(structured_review['immediate_improvement_recommendations'])} items) ###\n")
                for i, rec in enumerate(structured_review["immediate_improvement_recommendations"], 1):
                    if isinstance(rec, dict):
                        if rec.get('title') and rec.get('description'):
                            f.write(f"\n{i}. {rec['title']}: {rec['description']}\n")
                        else:
                            f.write(f"\n{i}. {rec.get('recommendation', 'N/A')}\n")
                    else:
                        f.write(f"\n{i}. {rec}\n")

        # Create file information summary
        file_info = {
            "file_uuid": file_uuid,
            "original_filename": file.filename,
            "files_created": {
                "original_text": f"{file_uuid}_original.txt",
                "review_json": f"{file_uuid}_review.json",
                "review_profile_file": f"{file_uuid}_review_profile.txt"
            },
            "review_summary": {
                "questions_count": len(structured_review.get("clarification_questions", [])),
                "recommendations_count": len(structured_review.get("immediate_improvement_recommendations", [])),
                "gap_analysis_sections": len(structured_review.get("detailed_gap_analysis", {})),
                "has_overview_assessment": bool(structured_review.get("resume_overview_assessment"))
            }
        }

        return JSONResponse(content={
            "file": file_uuid,
            "review_profile_file": f"{file_uuid}_review_profile.txt",
            "resume_review": structured_review,
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


# Get file info endpoint
@app.get("/file-info/{file_uuid}")
async def get_file_info(file_uuid: str):
    """Get information about a processed file"""
    try:
        original_file_path = os.path.join(DATA_DIR, f"{file_uuid}_original.txt")
        review_json_path = os.path.join(DATA_DIR, f"{file_uuid}_review.json")
        review_profile_path = os.path.join(DATA_DIR, f"{file_uuid}_review_profile.txt")
        improved_resume_path = os.path.join(DATA_DIR, f"{file_uuid}_improved_resume.txt")

        info = {
            "file_uuid": file_uuid,
            "files": {
                "original_text": {
                    "exists": os.path.exists(original_file_path),
                    "filename": f"{file_uuid}_original.txt"
                },
                "review_json": {
                    "exists": os.path.exists(review_json_path),
                    "filename": f"{file_uuid}_review.json"
                },
                "review_profile_file": {
                    "exists": os.path.exists(review_profile_path),
                    "filename": f"{file_uuid}_review_profile.txt"
                },
                "improved_resume": {
                    "exists": os.path.exists(improved_resume_path),
                    "filename": f"{file_uuid}_improved_resume.txt"
                }
            }
        }

        # Add review summary if review exists
        if os.path.exists(review_json_path):
            with open(review_json_path, "r", encoding='utf-8') as f:
                review_data = json.load(f)
            info["review_summary"] = {
                "questions_count": len(review_data.get("clarification_questions", [])),
                "recommendations_count": len(review_data.get("immediate_improvement_recommendations", [])),
                "gap_analysis_sections": len(review_data.get("detailed_gap_analysis", {})),
                "has_assessment": bool(review_data.get("resume_overview_assessment"))
            }

        # Add file sizes and generation metadata
        for file_type, file_info in info["files"].items():
            if file_info["exists"]:
                file_path = os.path.join(DATA_DIR, file_info["filename"])
                file_info["size_bytes"] = os.path.getsize(file_path)

        # Add generation metadata if available
        generation_metadata_path = os.path.join(DATA_DIR, f"{file_uuid}_generation_metadata.json")
        if os.path.exists(generation_metadata_path):
            with open(generation_metadata_path, "r", encoding='utf-8') as f:
                generation_data = json.load(f)
            info["generation_info"] = {
                "timestamp": generation_data.get("generation_timestamp"),
                "questions_answered": generation_data.get("questions_count", 0),
                "has_improved_resume": info["files"]["improved_resume"]["exists"]
            }
            info["files"]["generation_metadata"] = {
                "exists": True,
                "filename": f"{file_uuid}_generation_metadata.json",
                "size_bytes": os.path.getsize(generation_metadata_path)
            }

        return JSONResponse(content=info)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file info: {str(e)}")


# Download file endpoint
@app.get("/download/{file_uuid}/{file_type}")
async def download_file(file_uuid: str, file_type: str):
    """Download a specific file by UUID and type"""
    try:
        file_mapping = {
            "original": f"{file_uuid}_original.txt",
            "review_json": f"{file_uuid}_review.json",
            "review_profile": f"{file_uuid}_review_profile.txt",
            "improved_resume": f"{file_uuid}_improved_resume.txt",
            "generation_metadata": f"{file_uuid}_generation_metadata.json"
        }

        if file_type not in file_mapping:
            raise HTTPException(status_code=400, detail="Invalid file type")

        filename = file_mapping[file_type]
        file_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()

        return JSONResponse(content={
            "file_uuid": file_uuid,
            "file_type": file_type,
            "filename": filename,
            "content": content,
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")