import streamlit as st
import os
import uuid
import json
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
# Configure page
st.set_page_config(
    page_title="CV Enhancement - Q&A Interface",
    layout="wide"
)
# Authentication
def check_password():
    """Returns True if the user entered the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("CV_ANALYZER_PASSWORD", "Abc123!@#7"):
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["authenticated"] = False
    # Return True if already authenticated
    if st.session_state.get("authenticated", False):
        return True
    # Show password input
    st.markdown(
        """
        <div style='text-align: center; padding: 50px;'>
            <h1>Resume Analyzer</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter password"
        )
        if st.session_state.get("authenticated") == False:
            st.error("Incorrect password. Please try again.")
    return False

# Check authentication first
if not check_password():
    st.stop()
# Initialize session state
if 'qa_session_id' not in st.session_state:
    st.session_state.qa_session_id = str(uuid.uuid4())[:8]
if 'questions_list' not in st.session_state:
    st.session_state.questions_list = []
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'enhanced_resume' not in st.session_state:
    st.session_state.enhanced_resume = None
# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("prompts", exist_ok=True)
# Create default resume generation prompt if it doesn't exist
GENERATE_RESUME_PROMPT_FILE = os.path.join("prompts", "generate_resume_prompt.txt")
if not os.path.exists(GENERATE_RESUME_PROMPT_FILE):
    default_resume_prompt = """# Enhanced Resume Generation
Based on the comprehensive CV analysis and detailed question-answer responses, generate an improved, professional resume that addresses gaps and strengthens weak areas.
## Requirements:
- Use the original CV as the foundation
- Incorporate insights from the comprehensive analysis
- Integrate specific details from question-answer responses
- Address identified gaps and weaknesses
- Enhance quantification and impact statements
- Maintain professional formatting and structure
- Ensure consistency across all sections
## Output Format:
Generate a complete, professional resume with:
**CONTACT INFORMATION**
[Enhanced contact details with professional summary]
**PROFESSIONAL SUMMARY**
[3-4 lines highlighting key strengths, experience level, and value proposition based on analysis and Q&A responses]
**CORE COMPETENCIES**
[Enhanced skills section with evidence-based categorization and proficiency levels]
**PROFESSIONAL EXPERIENCE**
[For each position, include:]
- Enhanced job titles and company descriptions
- Quantified achievements and responsibilities with specific metrics from Q&A
- Impact statements with measurable outcomes
- Technology stack and methodologies used
- Leadership and collaboration examples
**KEY PROJECTS & ACHIEVEMENTS**
[Enhanced project descriptions with:]
- Specific technologies and approaches used
- Quantified outcomes and business impact from Q&A responses
- Team size and role clarification
- Technical challenges overcome
- Performance metrics and results
**EDUCATION & CERTIFICATIONS**
[Enhanced education section with:]
- Academic achievements and honors from Q&A
- Relevant coursework and research
- Professional certifications with validity dates
- Continuing education and professional development
**TECHNICAL SKILLS**
[Categorized by proficiency level based on Q&A responses:]
- Expert Level: [Skills with 5+ years experience]
- Advanced Level: [Skills with 3-5 years experience]
- Intermediate Level: [Skills with 1-3 years experience]
Generate a polished, ATS-friendly resume that positions the candidate competitively while maintaining authenticity and addressing all identified gaps."""
    with open(GENERATE_RESUME_PROMPT_FILE, "w", encoding='utf-8') as f:
        f.write(default_resume_prompt)
def parse_questions_from_text(questions_text):
    """Parse questions from the input text"""
    questions = []
    lines = questions_text.split('\n')
    current_question = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Look for questions with question# prefix
        if line.startswith('question#'):
            if current_question:
                questions.append(current_question.strip())
            current_question = line.replace('question#', '').strip()
        elif current_question and not line.startswith('#') and not line.startswith('**') and not line.startswith('-'):
            # Continue building the current question
            current_question += " " + line
        elif '?' in line and len(line) > 30 and not line.startswith('**') and not line.startswith('#'):
            # Standalone question
            cleaned_line = line.replace('question#', '').strip()
            if cleaned_line:
                questions.append(cleaned_line)
    # Add the last question
    if current_question:
        questions.append(current_question.strip())
    # Clean up questions
    cleaned_questions = []
    for q in questions:
        # Remove numbering and clean up
        q = re.sub(r'^\d+\.\s*', '', q)
        q = q.replace('**', '').strip()
        if len(q) > 20 and '?' in q:
            cleaned_questions.append(q)
    return cleaned_questions
def generate_enhanced_resume(cv_text, analysis_text, qa_data, generate_resume_prompt, api_key, gpt_model="o1-mini"):
    """Generate enhanced resume using OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        # Format Q&A responses
        qa_text = "\n\nDETAILED QUESTION-ANSWER RESPONSES:\n"
        for i, (question, answer) in enumerate(qa_data.items(), 1):
            qa_text += f"\nQ{i}: {question}\nA{i}: {answer}\n"
        # Combine all inputs
        combined_input = f"{generate_resume_prompt}\n\nORIGINAL CV:\n{cv_text}\n\nCOMPREHENSIVE ANALYSIS:\n{analysis_text}{qa_text}"
        # Call OpenAI
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[{"role": "user", "content": combined_input}],
            max_completion_tokens=65000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error generating resume: {str(e)}")
# Main Interface
st.title("CV Enhancement - Question & Answer Interface")
st.markdown("---")
# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    # API Key
    api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    # Model selection
    gpt_model = st.selectbox(
        "GPT Model",
        ["o1-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="Select the OpenAI model for resume generation"
    )
    st.markdown("---")
    st.header("Session Info")
    st.write(f"**Session ID:** {st.session_state.qa_session_id}")
    # Logout button

# Main content area
col1, col2 = st.columns([1, 1])
with col1:
    st.header("Input Data")
    # Questions input
    st.subheader("Generated Questions")
    questions_input = st.text_area(
        "Paste the generated questions here:",
        value="""**CV Clarification Form - Awais Khan Mughal**  
**Position Applied For:** AI Team Lead
### Section 1: Work Experience Clarification
- **Position: AI Team Lead at DroxLabs (April 2025 – Present)**
  - question#For your role as AI Team Lead at DroxLabs from April 2025 to Present: Please clarify the start date of your tenure, as the provided dates appear to be in the future relative to the current date.
  - question#For your role as AI Team Lead at DroxLabs from April 2025 to Present: What is the size of your team, including direct reports and total team members under your leadership?
  - question#For your role as AI Team Lead at DroxLabs from April 2025 to Present: What was the annual budget allocated for your projects, and how did you distribute this budget across different initiatives?
- **Position: Principal Software Engineer - AI at Ciklum (April 2021 - May 2025)**
  - question#For your role as Principal Software Engineer - AI at Ciklum from April 2021 to May 2025: How many projects did you manage simultaneously, and what was the typical team size for each project?
  - question#For your role as Principal Software Engineer - AI at Ciklum from April 2021 to May 2025: What was the total budget you managed, and what were the key financial responsibilities in this role?
### Section 2: Education and Certification Verification
- **Master of Science in Data Science**
  - question#For your Master of Science in Data Science from Shaheed Zulfikar Ali Bhutto Institute of Science and Technology, Islamabad, 2021: What was your GPA or degree classification, and did you receive any academic honors or distinctions?
### Section 3: Skills and Technical Competency Assessment
- **Unsupported Skills**
  - question#For the skill TypeSense listed in your resume: Can you provide specific examples or projects where you utilized TypeSense, including the context and outcomes?
  - question#For the skill Redis Cache listed in your resume: Can you describe any projects or roles where you implemented Redis Cache, detailing how it was used and the benefits it provided?
### Section 4: Projects and Achievements Context
- **GovDoc**
  - question#For your project GovDoc at DroxLabs: How many government contracts have been analyzed using GovDoc, and what improvements in analysis speed or accuracy have been achieved?
### Section 5: Additional Context and Clarification
- question#Can you explain the one-month overlap between your roles at Ciklum (ending May 2025) and DroxLabs (starting April 2025), and clarify the correct dates for your tenure at DroxLabs?""",
        height=300,
        help="Paste the full generated questions text here"
    )
    # CV Text input
    st.subheader("Original CV Text")
    cv_text = st.text_area(
        "Paste the original CV text:",
        height=200,
        placeholder="Paste the extracted CV text here..."
    )
    # Analysis input
    st.subheader("CV Analysis")
    analysis_text = st.text_area(
        "Paste the comprehensive CV analysis:",
        height=200,
        placeholder="Paste the comprehensive analysis text here..."
    )
    # Generate Resume Prompt
    st.subheader("Generate Resume Prompt")
    # Load existing prompt
    try:
        with open(GENERATE_RESUME_PROMPT_FILE, "r", encoding='utf-8') as f:
            existing_prompt = f.read()
    except:
        existing_prompt = ""
    generate_resume_prompt = st.text_area(
        "Customize the resume generation prompt:",
        value=existing_prompt,
        height=300,
        help="Modify this prompt to customize how the enhanced resume is generated"
    )
    # Save prompt button
    if st.button("Save Prompt"):
        try:
            with open(GENERATE_RESUME_PROMPT_FILE, "w", encoding='utf-8') as f:
                f.write(generate_resume_prompt)
            st.success("Prompt saved successfully!")
        except Exception as e:
            st.error(f"Error saving prompt: {str(e)}")
with col2:
    st.header("Question-Answer Form")
    if questions_input:
        # Parse questions
        parsed_questions = parse_questions_from_text(questions_input)
        st.session_state.questions_list = parsed_questions
        if parsed_questions:
            st.success(f"Found {len(parsed_questions)} questions to answer")
            # Display questions with answer fields
            with st.form("qa_form"):
                answers = {}
                for i, question in enumerate(parsed_questions, 1):
                    st.markdown(f"**Question {i}:**")
                    st.write(question)
                    answer = st.text_area(
                        f"Answer {i}:",
                        height=100,
                        key=f"answer_{i}",
                        placeholder="Provide detailed answer with specific numbers, dates, and examples... (Optional - can be left empty)"
                    )
                    answers[question] = answer
                    st.markdown("---")
                # Submit button
                submitted = st.form_submit_button("Generate Enhanced Resume", type="primary")
                if submitted:
                    # Validate inputs
                    if not api_key:
                        st.error("Please provide OpenAI API key")
                    elif not cv_text:
                        st.error("Please provide original CV text")
                    elif not analysis_text:
                        st.error("Please provide CV analysis")
                    elif not generate_resume_prompt:
                        st.error("Please provide generate resume prompt")
                    else:
                        try:
                            with st.spinner("Generating enhanced resume..."):
                                # Generate enhanced resume
                                enhanced_resume = generate_enhanced_resume(
                                    cv_text, analysis_text, answers, generate_resume_prompt, api_key, gpt_model
                                )
                                st.session_state.enhanced_resume = enhanced_resume
                                st.session_state.answers = answers
                                # Save structured data
                                structured_data = {
                                    "session_id": st.session_state.qa_session_id,
                                    "cv_text": cv_text,
                                    "analysis_text": analysis_text,
                                    "generate_resume_prompt": generate_resume_prompt,
                                    "questions": [
                                        {"question": q, "answer": a}
                                        for q, a in answers.items()
                                    ],
                                    "enhanced_resume": enhanced_resume,
                                    "model_used": gpt_model,
                                    "timestamp": datetime.now().isoformat()
                                }
                                # Save to file
                                output_file = os.path.join("data",
                                                           f"{st.session_state.qa_session_id}_enhanced_cv.json")
                                with open(output_file, "w", encoding='utf-8') as f:
                                    json.dump(structured_data, f, indent=2, ensure_ascii=False)
                                st.success("Enhanced resume generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating resume: {str(e)}")
        else:
            st.warning("No questions found. Please check the input format.")
    else:
        st.info("Please paste the generated questions in the left panel to begin.")
# Results section
if st.session_state.enhanced_resume:
    st.markdown("---")
    st.header("Enhanced Resume")
    # Display metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        answered_questions = sum(1 for a in st.session_state.answers.values() if a.strip())
        st.metric("Questions Answered", f"{answered_questions}/{len(st.session_state.answers)}")
    with col_m2:
        st.metric("Session ID", st.session_state.qa_session_id)
    with col_m3:
        st.metric("Model Used", gpt_model)
    with col_m4:
        st.metric("Characters", len(st.session_state.enhanced_resume))
    # Display resume
    st.text_area(
        "Generated Enhanced Resume:",
        value=st.session_state.enhanced_resume,
        height=600,
        key="enhanced_resume_display"
    )
    # Download options
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="Download Enhanced Resume",
            data=st.session_state.enhanced_resume,
            file_name=f"enhanced_resume_{st.session_state.qa_session_id}.txt",
            mime="text/plain"
        )
    with col_d2:
        # Create structured JSON for download
        if st.session_state.answers:
            structured_json = {
                "session_id": st.session_state.qa_session_id,
                "questions": [
                    {"question": q, "answer": a}
                    for q, a in st.session_state.answers.items()
                ],
                "enhanced_resume": st.session_state.enhanced_resume,
                "model_used": gpt_model,
                "timestamp": datetime.now().isoformat()
            }
            st.download_button(
                label="Download Q&A Data (JSON)",
                data=json.dumps(structured_json, indent=2, ensure_ascii=False),
                file_name=f"qa_data_{st.session_state.qa_session_id}.json",
                mime="application/json"
            )
    # Reset button
    if st.button("Start New Session"):
        for key in ['qa_session_id', 'questions_list', 'answers', 'enhanced_resume']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.qa_session_id = str(uuid.uuid4())[:8]
        st.rerun()
# Footer
