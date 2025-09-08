import streamlit as st
import os
import uuid
import re
from datetime import datetime
from pathlib import Path
import tempfile
# PDF reading imports
import PyPDF2
import pdfplumber
# OpenAI and analysis imports
from openai import OpenAI
from dotenv import load_dotenv
import json
# Load environment variables
load_dotenv()
# Configure page
st.set_page_config(
    page_title="CV Analyzer Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'extracted_cv_path' not in st.session_state:
    st.session_state.extracted_cv_path = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'questions_results' not in st.session_state:
    st.session_state.questions_results = None
# Ensure directories exist
os.makedirs("resume", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("prompts", exist_ok=True)
# Create default questions prompt file if it doesn't exist
GENERATE_QUESTIONS_PROMPT_FILE = os.path.join("prompts", "generate_questions_prompt.txt")
if not os.path.exists(GENERATE_QUESTIONS_PROMPT_FILE):
    default_questions_prompt = """# Interview Questions Generation
Based on the CV content and comprehensive analysis, generate targeted interview questions that will help employers assess the candidate effectively.
## Requirements:
- Generate questions that test claimed skills and experiences
- Focus on areas where the CV lacks detail or evidence
- Include both technical and behavioral questions
- Provide questions that validate or challenge weak areas identified in the analysis
- Create questions that allow the candidate to demonstrate their actual capabilities
## Output Format:
```
COMPREHENSIVE INTERVIEW QUESTIONS
Technical Skills Validation Questions:
[Generate 8-12 questions that test the technical skills claimed in the CV]
Experience Verification Questions:
[Generate 6-10 questions that probe the depth of work experience claims]
Project Deep-Dive Questions:
[Generate 5-8 questions that explore project details and technical implementations]
Behavioral and Soft Skills Questions:
[Generate 6-8 questions that assess leadership, communication, and problem-solving abilities]
Gap Analysis Questions:
[Generate 4-6 questions specifically targeting weak areas or gaps identified in the analysis]
Scenario-Based Questions:
[Generate 5-7 situational questions that test practical application of skills]
Red Flag Investigation Questions:
[Generate 3-5 questions that address any inconsistencies or concerns from the CV analysis]
Questions by Difficulty Level:
ENTRY LEVEL (Easy):
[3-5 basic questions to establish baseline competency]
INTERMEDIATE (Medium):
[5-7 questions that test practical application and experience]
ADVANCED (Hard):
[4-6 challenging questions for senior positions or specialist roles]
Interview Strategy Recommendations:
- Suggested interview flow and question sequencing
- Key areas to focus on based on the role level
- Warning signs to watch for in responses
- Follow-up question strategies for each major area
```
Generate comprehensive questions that will thoroughly evaluate this candidate's actual capabilities versus their CV claims."""
    with open(GENERATE_QUESTIONS_PROMPT_FILE, "w", encoding='utf-8') as f:
        f.write(default_questions_prompt)
# Password protection function
# Password protection function
def check_password():
    """Returns True if the user entered the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Only check password if something was actually entered
        if st.session_state["password"]:
            if st.session_state["password"] == os.getenv("CV_ANALYZER_PASSWORD", "Abc123!@#7"):
                st.session_state["authenticated"] = True
                del st.session_state["password"]  # Don't store the password
            else:
                st.session_state["authentication_failed"] = True
        # Clear the password field if empty
        elif not st.session_state["password"]:
            st.session_state.pop("authentication_failed", None)

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

        # Only show error if authentication actually failed (not on initial load)
        if st.session_state.get("authentication_failed", False):
            st.error("Incorrect password. Please try again.")

    return False

# PDF Reading Functions
def read_pdf_with_pdfplumber(pdf_file):
    """Read PDF using pdfplumber - better formatting and table extraction"""
    try:
        text_content = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
                # Extract tables if any
                tables = page.extract_tables()
                if tables:
                    for i, table in enumerate(tables, 1):
                        text_content += f"\nTable {i} from page {page_num}:\n"
                        for row in table:
                            text_content += "\t".join(str(cell) if cell else "" for cell in row) + "\n"
        return text_content
    except Exception as e:
        st.error(f"Error reading PDF with pdfplumber: {e}")
        return None
def read_pdf_with_pypdf2(pdf_file):
    """Read PDF using PyPDF2 - basic text extraction"""
    try:
        text_content = ""
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
        return text_content
    except Exception as e:
        st.error(f"Error reading PDF with PyPDF2: {e}")
        return None
def clean_and_format_text(text):
    """Clean and format the extracted text"""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)
# CV Analyzer Class (Based on FastAPI version)
class CVAnalyzer:
    def __init__(self, gpt_model="o1-mini", api_key=None):
        self.gpt_model = gpt_model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        # Load questions prompt from file
        try:
            with open(GENERATE_QUESTIONS_PROMPT_FILE, "r", encoding='utf-8') as f:
                questions_prompt = f.read()
        except FileNotFoundError:
            questions_prompt = "Generate comprehensive interview questions based on the CV analysis."
        self.prompt_templates = {
            'skills_analysis': """
# Skills Comprehensive Analysis
Analyze ONLY the skills section of the provided CV. You must analyze every single skill individually with complete detail. No shortcuts, no placeholders allowed.
## Requirements:
- Identify ALL skill categories in the CV
- Analyze each individual skill with:
  * Evidence in work experience (specific roles where demonstrated)
  * Evidence in projects (specific projects using this skill)
  * Educational foundation support
  * Proficiency indicators present or absent
  * Application context from CV
  * Validation strength assessment
## Output Format:
```
SKILLS COMPREHENSIVE ANALYSIS
Total Skills Categories: [Count]
Total Individual Skills: [Count]
[For each skill category:]
CATEGORY: [Exact category name from CV]
SKILL: [Individual skill name]
CV Location: [Where mentioned]
Work Evidence: [Specific roles demonstrating this skill or "Not demonstrated"]
Project Evidence: [Specific projects using this skill or "Not demonstrated"]
Educational Support: [Academic foundation or "Not established"]
Proficiency Level: [Any level claimed or "Not specified in CV"]
Application Context: [How skill is used or "Not specified in CV"]
Validation Status: [Strong/Moderate/Weak/None with reasoning]
[Continue for EVERY skill in EVERY category]
Skills Evidence Summary:
- Well-Supported Skills: [Count and list]
- Partially Supported Skills: [Count and list]
- Unsupported Skills: [Count and list]
- Missing Industry Standard Tools: [What's absent for experience level]
```
Complete this analysis for ALL skills before stopping.
""",
            'experience_analysis': """
# Work Experience Forensic Analysis
Analyze ONLY the work experience section. You must analyze every position individually with complete responsibility breakdown. No shortcuts allowed.
## Requirements:
- Analyze each employment position individually
- Break down every responsibility statement
- Identify quantitative gaps systematically
- Map skills validation for each role
- Assess timeline consistency
## Output Format:
```
WORK EXPERIENCE COMPREHENSIVE ANALYSIS
Total Positions: [Count]
[For each position:]
POSITION: [Job Title] at [Company] ([Dates])
Duration: [Calculated length]
Industry Context: [Determined field or "Cannot determine from CV"]
Location: [Specified or "Not specified in CV"]
Responsibility Breakdown:
Responsibility 1: [Exact text from CV]
- Action Verbs: [Leadership/action words used]
- Scope Elements: [Scale/size mentions or "Not specified"]
- Quantitative Data: [Numbers/percentages or "None stated"]
- Technology References: [Tools/systems mentioned]
- Outcome Descriptions: [Results stated or "Not specified"]
- Skills Demonstrated: [Which CV skills this validates]
- Missing Quantification: [Expected metrics absent]
[Continue for ALL responsibilities under this position]
Quantitative Gaps Summary:
- Financial Data Missing: [Budget, revenue, cost information absent]
- Performance Metrics Missing: [Achievement, target, efficiency data absent]
- Scale Indicators Missing: [Team size, project scope, user base data absent]
- Quality Measures Missing: [Accuracy, reliability, satisfaction data absent]
- Timeline Data Missing: [Duration, deadline, delivery information absent]
Skills Validation for This Position:
- Demonstrated Skills: [CV skills proven by this position]
- Undemonstrated Skills: [CV skills lacking evidence in this role]
[Repeat for ALL positions]
Timeline Consistency Analysis:
- Employment Sequence: [Chronological verification]
- Gap Analysis: [Any employment gaps with duration]
- Date Consistency: [Verification across CV sections]
```
Complete this analysis for ALL positions before stopping.
""",
            'projects_analysis': """
# Projects Comprehensive Examination
Analyze ONLY the projects mentioned in the CV. You must analyze every project individually with complete technical and business breakdown.
## Requirements:
- Identify ALL projects mentioned anywhere in CV
- Provide comprehensive technical implementation analysis
- Assess business value and impact
- Document quantitative outcomes present and missing
- Validate skills demonstration through projects
## Output Format:
```
PROJECTS COMPREHENSIVE ANALYSIS
Total Projects: [Count]
[For each project:]
PROJECT: [Exact project name]
CV Location: [Where mentioned in CV]
Description: [Complete description from CV]
Project Context:
- Business Domain: [Industry/application area or "Not specified in CV"]
- Timeline: [Duration/dates mentioned or "Not specified in CV"]
- Team Role: [Position/responsibility or "Not specified in CV"]
- Budget/Scale: [Resource scope or "Not specified in CV"]
Technical Implementation Analysis:
- Technologies Used: [Complete list from CV or "Not specified in CV"]
- Architecture Approach: [Design methodology or "Not specified in CV"]
- System Integration: [Connections described or "Not specified in CV"]
- Performance Requirements: [Speed/scale needs or "Not specified in CV"]
- Security Implementation: [Safety measures or "Not specified in CV"]
- Development Methodology: [Process approach or "Not specified in CV"]
Business Value Analysis:
- Problem Solved: [Issue addressed or "Not specified in CV"]
- User Benefits: [Value delivered or "Not specified in CV"]
- Business Impact: [Organizational effect or "Not specified in CV"]
- Innovation Elements: [Creative aspects or "Not specified in CV"]
- Market Relevance: [Industry significance or "Not specified in CV"]
Quantitative Outcomes Analysis:
- User Metrics: [Adoption, usage data or "Not specified in CV"]
- Performance Data: [Speed, efficiency improvements or "Not specified in CV"]
- Business Results: [Cost, revenue impact or "Not specified in CV"]
- Quality Measures: [Accuracy, reliability data or "Not specified in CV"]
- Delivery Metrics: [Timeline, milestone data or "Not specified in CV"]
- Scalability Results: [Growth capacity or "Not specified in CV"]
Skills Validation Analysis:
- Technical Skills Proven: [CV skills this project demonstrates]
- Soft Skills Evidenced: [Leadership, communication shown]
- Problem-Solving Demonstrated: [Analytical capabilities shown]
- Innovation Displayed: [Creative thinking evidenced]
- Undemonstrated Claims: [CV skills not supported by this project]
Critical Missing Details:
- Most Important Quantitative Gaps: [Priority measurements absent]
- Technical Specification Gaps: [Missing technical details]
- Business Impact Gaps: [Missing value metrics]
[Repeat for ALL projects]
```
Complete this analysis for ALL projects before stopping.
""",
            'education_analysis': """
# Education and Academic Background Analysis
Analyze education, academic achievements, and learning background comprehensively.
## Requirements:
- Analyze each degree/certification individually
- Assess academic achievements and research
- Evaluate professional relevance
- Identify missing academic details
## Output Format:
```
EDUCATION AND ACADEMIC ANALYSIS
[For each educational credential:]
DEGREE: [Institution] - [Degree] - [Year]
Recognition Level: [Institution standing assessment]
Field Relevance: [Professional alignment with career]
Academic Achievements: [Honors, GPA, thesis details or "Not specified in CV"]
Research Work: [Thesis, projects, publications or "Not specified in CV"]
Relevant Coursework: [Specific courses or "Not specified in CV"]
Professional Value: [How education validates career claims]
Missing Academic Details: [Standard information absent]
[For each certification:]
CERTIFICATION: [Title] - [Issuer] - [Date]
Industry Recognition: [Credential value assessment]
Professional Relevance: [Career alignment]
Work Application Evidence: [How certification appears in experience]
Missing Details: [Validity, renewal, credential ID gaps]
Academic Development Assessment:
- Educational Foundation Strength: [Assessment]
- Professional Alignment: [How education supports career]
- Continuing Education Evidence: [Ongoing learning demonstration]
- Academic Gaps: [Missing standard educational information]
```
""",
            'integration_analysis': """
# Integration and Comprehensive Assessment
Using previous analyses, provide final integration, cross-validation, and comprehensive recommendations.
## Requirements:
- Cross-validate findings across all sections
- Identify overarching patterns and gaps
- Provide prioritized improvement recommendations
- Create final comprehensive assessment
## Output Format:
```
INTEGRATION AND FINAL ASSESSMENT
Cross-Validation Analysis:
- Skills-Experience Alignment: [How well skills match work evidence]
- Skills-Projects Alignment: [How well skills match project evidence]
- Experience-Education Alignment: [Career progression logic]
- Timeline Consistency: [Date and progression verification]
Overarching Patterns:
- Quantification Consistency: [Overall metrics presence assessment]
- Professional Narrative: [Career story coherence]
- Evidence Quality: [Overall validation strength]
Priority Enhancement Recommendations:
CRITICAL (Address Immediately):
1. [Most important gap with specific recommendation]
2. [Second most critical issue with solution]
3. [Third priority with implementation suggestion]
IMPORTANT (Address Next):
1. [Significant improvement with specific action]
2. [Next priority enhancement with details]
3. [Additional important upgrade with guidance]
BENEFICIAL (Address When Possible):
1. [Professional enhancement opportunity]
2. [Additional improvement suggestion]
3. [Long-term development recommendation]
Final Professional Assessment:
- Overall Presentation Quality: [Comprehensive evaluation]
- Career Advancement Readiness: [Assessment for target roles]
- Competitive Positioning: [Market competitiveness evaluation]
- Success Implementation Plan: [Next steps for improvement]
```
""",
            'questions_prompt': questions_prompt
        }
    def detect_cv_structure(self, cv_text):
        """Analyze CV to determine what sections are present"""
        structure = {}
        # Skills detection
        skills_patterns = [
            r'(technical\s+skills|programming|languages|technologies)',
            r'(skills|competenc|proficienc)',
            r'(python|javascript|java|aws|machine\s+learning)',
        ]
        structure['has_skills'] = any(re.search(pattern, cv_text, re.IGNORECASE) for pattern in skills_patterns)
        # Experience detection
        experience_patterns = [
            r'(work\s+experience|employment|professional\s+experience)',
            r'(software\s+engineer|developer|lead|manager)',
            r'(responsibilities|developed|led|managed)',
        ]
        structure['has_experience'] = any(re.search(pattern, cv_text, re.IGNORECASE) for pattern in experience_patterns)
        # Projects detection
        projects_patterns = [
            r'(projects|portfolio|key\s+projects)',
            r'(developed\s+a|built\s+a|created\s+a)',
            r'(github|portfolio)',
        ]
        structure['has_projects'] = any(re.search(pattern, cv_text, re.IGNORECASE) for pattern in projects_patterns)
        # Education detection
        education_patterns = [
            r'(education|academic|degree|university|college)',
            r'(bachelor|master|phd|bs|ms|ba|ma)',
            r'(graduated|graduation)',
        ]
        structure['has_education'] = any(re.search(pattern, cv_text, re.IGNORECASE) for pattern in education_patterns)
        # Certification detection
        cert_patterns = [
            r'(certification|certified|credential)',
            r'(aws\s+certified|microsoft\s+certified|cisco)',
        ]
        structure['has_certifications'] = any(re.search(pattern, cv_text, re.IGNORECASE) for pattern in cert_patterns)
        return structure
    def plan_analysis_passes(self, cv_structure):
        """Determine which analysis passes are needed based on CV content"""
        passes = []
        if cv_structure['has_skills']:
            passes.append('skills_analysis')
        if cv_structure['has_experience']:
            passes.append('experience_analysis')
        if cv_structure['has_projects']:
            passes.append('projects_analysis')
        if cv_structure['has_education'] or cv_structure['has_certifications']:
            passes.append('education_analysis')
        # Always include integration pass
        passes.append('integration_analysis')
        return passes
    def call_openai_analysis(self, prompt, cv_text, analysis_type, previous_analyses=None):
        """Make OpenAI API call for specific analysis type"""
        context = f"CV CONTENT:\n{cv_text}"
        if previous_analyses and analysis_type == 'integration_analysis':
            context += f"\n\nPREVIOUS ANALYSES:\n{previous_analyses}"
        combined_input = f"{prompt}\n\n{context}"
        response = self.client.chat.completions.create(
            model=self.gpt_model,
            messages=[{"role": "user", "content": combined_input}],
            max_completion_tokens=15000
        )
        return response.choices[0].message.content.strip()
    def compile_final_report(self, session_uuid, analyses, cv_structure):
        """Compile all analyses into comprehensive final report"""
        report_sections = []
        # Header
        report_sections.append(f"""
COMPREHENSIVE CV ANALYSIS REPORT
Session ID: {session_uuid}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
GPT Model Used: {self.gpt_model}
CV Structure Detected: {', '.join([k.replace('has_', '').title() for k, v in cv_structure.items() if v])}
Analysis Passes Completed: {len(analyses)}
================================================================================
""")
        # Add each analysis section
        for analysis_type, content in analyses.items():
            section_title = analysis_type.replace('_', ' ').title()
            report_sections.append(f"""
{section_title.upper()}
================================================================================
{content}
""")
        report_sections.append(
            "================================================================================\nEND OF COMPREHENSIVE ANALYSIS\n================================================================================")
        return '\n'.join(report_sections)
    def analyze_cv(self, cv_file_path, session_uuid):
        """Main analysis function matching FastAPI version"""
        # Read CV text
        if not os.path.exists(cv_file_path):
            raise FileNotFoundError(f"CV file not found: {cv_file_path}")
        with open(cv_file_path, "r", encoding='utf-8') as f:
            cv_text = f.read().strip()
        # Step 1: Detect CV structure
        cv_structure = self.detect_cv_structure(cv_text)
        # Step 2: Plan analysis passes
        analysis_passes = self.plan_analysis_passes(cv_structure)
        # Step 3: Execute analysis passes
        analyses = {}
        previous_analyses_text = ""
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, pass_type in enumerate(analysis_passes):
            status_text.text(f"Executing {pass_type.replace('_', ' ').title()}...")
            progress_bar.progress((i + 1) / len(analysis_passes))
            if pass_type == 'integration_analysis':
                # For integration, include previous analyses
                result = self.call_openai_analysis(
                    self.prompt_templates[pass_type],
                    cv_text,
                    pass_type,
                    previous_analyses_text
                )
            else:
                result = self.call_openai_analysis(
                    self.prompt_templates[pass_type],
                    cv_text,
                    pass_type
                )
            analyses[pass_type] = result
            previous_analyses_text += f"\n\n{pass_type.upper()}:\n{result}"
            # Save intermediate result
            with open(os.path.join("data", f"{session_uuid}_{pass_type}.txt"), "w", encoding='utf-8') as f:
                f.write(result)
        # Step 4: Compile final comprehensive report
        final_report = self.compile_final_report(session_uuid, analyses, cv_structure)
        # Save final report
        final_file_path = os.path.join("data", f"{session_uuid}_comprehensive_analysis.txt")
        with open(final_file_path, "w", encoding='utf-8') as f:
            f.write(final_report)
        status_text.text("Analysis complete!")
        progress_bar.progress(1.0)
        return {
            "session_id": session_uuid,
            "cv_structure_detected": cv_structure,
            "analysis_passes_completed": analysis_passes,
            "comprehensive_analysis": final_report,
            "individual_analyses": analyses,
            "final_file_path": final_file_path,
            "success": True
        }
    def generate_questions(self, cv_path, analysis_path, session_id):
        """Generate questions matching FastAPI version signature"""
        try:
            # Read CV text
            with open(cv_path, "r", encoding='utf-8') as f:
                cv_text = f.read().strip()
            # Read analysis text
            with open(analysis_path, "r", encoding='utf-8') as f:
                analysis_text = f.read()
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("Generating interview questions...")
            progress_bar.progress(0.3)
            # Combine prompt, CV text, and analysis
            combined_input = f"{self.prompt_templates['questions_prompt']}\n\nCV CONTENT:\n{cv_text}\n\nCV REVIEW:\n{analysis_text}"
            progress_bar.progress(0.6)
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "user", "content": combined_input}
                ],
                max_completion_tokens=65000
            )
            ai_response = response.choices[0].message.content.strip()
            progress_bar.progress(0.9)
            # Save response to questions file
            questions_file_path = os.path.join("data", f"{session_id}_questions.txt")
            with open(questions_file_path, "w", encoding='utf-8') as f:
                f.write(ai_response)
            status_text.text("Questions generated successfully!")
            progress_bar.progress(1.0)
            return {
                "response": ai_response,
                "response_file": f"{session_id}_questions.txt",
                "success": True
            }
        except Exception as e:
            raise Exception(f"Error generating questions: {str(e)}")
# Streamlit UI
def main():
    # Check password before showing the main app
    if not check_password():
        return
    st.title("CV Analyzer Pro")
    st.markdown("---")
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        # OpenAI API Key
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if not api_key:
            st.warning("Please provide your OpenAI API key")
        # GPT Model selection (default to o1-mini as in FastAPI)
        gpt_model = st.selectbox(
            "GPT Model",
            options=["o1-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview"],
            index=0
        )
        st.markdown("---")
        st.header("Analysis Status")
        if st.session_state.current_session_id:
            st.success(f"Session: {st.session_state.current_session_id[:8]}...")
        else:
            st.info("No active session")
    # Main content area
    col1, col2 = st.columns([1, 1])
    with col1:
        st.header("Upload CV")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            # Generate random ID
            random_id = str(uuid.uuid4())[:8]
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            # Extract text
            st.info("Extracting text from PDF...")
            # Try pdfplumber first
            text_content = read_pdf_with_pdfplumber(tmp_file_path)
            if not text_content:
                st.warning("pdfplumber failed, trying PyPDF2...")
                text_content = read_pdf_with_pypdf2(tmp_file_path)
            if text_content:
                # Clean and format text
                cleaned_text = clean_and_format_text(text_content)
                # Save extracted text with naming convention matching FastAPI
                extracted_file_path = f"resume/cv{random_id}_extracted.txt"
                with open(extracted_file_path, "w", encoding='utf-8') as f:
                    f.write(cleaned_text)
                st.success(f"Text extracted successfully!")
                st.info(f"Saved as: {extracted_file_path}")
                st.info(f"Characters: {len(cleaned_text)}")
                # Store in session state
                st.session_state.extracted_cv_path = extracted_file_path
                st.session_state.current_session_id = random_id
                # Preview extracted text
                with st.expander("Preview Extracted Text"):
                    st.text_area("CV Content",
                                 value=cleaned_text[:2000] + "..." if len(cleaned_text) > 2000 else cleaned_text,
                                 height=300)
            else:
                st.error("Failed to extract text from PDF")
            # Clean up temporary file
            os.unlink(tmp_file_path)
    with col2:
        st.header("Prompt Templates")
        if api_key:
            analyzer = CVAnalyzer(gpt_model=gpt_model, api_key=api_key)
            # Create tabs for different prompts - INCLUDING QUESTIONS GENERATION
            tabs = st.tabs(["Skills", "Experience", "Projects", "Education", "Integration", "Questions"])
            with tabs[0]:
                st.subheader("Skills Analysis Prompt")
                analyzer.prompt_templates['skills_analysis'] = st.text_area(
                    "Skills Analysis",
                    value=analyzer.prompt_templates['skills_analysis'],
                    height=300,
                    key="skills_prompt"
                )
            with tabs[1]:
                st.subheader("Experience Analysis Prompt")
                analyzer.prompt_templates['experience_analysis'] = st.text_area(
                    "Experience Analysis",
                    value=analyzer.prompt_templates['experience_analysis'],
                    height=300,
                    key="experience_prompt"
                )
            with tabs[2]:
                st.subheader("Projects Analysis Prompt")
                analyzer.prompt_templates['projects_analysis'] = st.text_area(
                    "Projects Analysis",
                    value=analyzer.prompt_templates['projects_analysis'],
                    height=300,
                    key="projects_prompt"
                )
            with tabs[3]:
                st.subheader("Education Analysis Prompt")
                analyzer.prompt_templates['education_analysis'] = st.text_area(
                    "Education Analysis",
                    value=analyzer.prompt_templates['education_analysis'],
                    height=300,
                    key="education_prompt"
                )
            with tabs[4]:
                st.subheader("Integration Analysis Prompt")
                analyzer.prompt_templates['integration_analysis'] = st.text_area(
                    "Integration Analysis",
                    value=analyzer.prompt_templates['integration_analysis'],
                    height=300,
                    key="integration_prompt"
                )
            with tabs[5]:
                st.subheader("Interview Questions Generation Prompt")
                st.info("Customize how interview questions are generated based on CV analysis")
                # Load current questions prompt from file
                try:
                    with open(GENERATE_QUESTIONS_PROMPT_FILE, "r", encoding='utf-8') as f:
                        current_questions_prompt = f.read()
                except:
                    current_questions_prompt = analyzer.prompt_templates['questions_prompt']
                updated_questions_prompt = st.text_area(
                    "Generate Questions Prompt - Fully Editable",
                    value=current_questions_prompt,
                    height=300,
                    key="questions_prompt",
                    help="Edit this prompt to customize the type and style of interview questions generated"
                )
                # Save prompt to file when changed
                if updated_questions_prompt != current_questions_prompt:
                    with open(GENERATE_QUESTIONS_PROMPT_FILE, "w", encoding='utf-8') as f:
                        f.write(updated_questions_prompt)
                    analyzer.prompt_templates['questions_prompt'] = updated_questions_prompt
    # Analysis section
    st.markdown("---")
    st.header("Run Analysis")
    col3, col4 = st.columns([1, 2])
    with col3:
        analyze_button = st.button("Analyze CV", type="primary",
                                   disabled=not (st.session_state.extracted_cv_path and api_key))
        if not st.session_state.extracted_cv_path:
            st.warning("Please upload and extract a CV first")
        elif not api_key:
            st.warning("Please provide OpenAI API key")
    with col4:
        if analyze_button and st.session_state.extracted_cv_path and api_key:
            try:
                analyzer = CVAnalyzer(gpt_model=gpt_model, api_key=api_key)
                # Update prompts from UI
                analyzer.prompt_templates['skills_analysis'] = st.session_state.skills_prompt
                analyzer.prompt_templates['experience_analysis'] = st.session_state.experience_prompt
                analyzer.prompt_templates['projects_analysis'] = st.session_state.projects_prompt
                analyzer.prompt_templates['education_analysis'] = st.session_state.education_prompt
                analyzer.prompt_templates['integration_analysis'] = st.session_state.integration_prompt
                if 'questions_prompt' in st.session_state:
                    analyzer.prompt_templates['questions_prompt'] = st.session_state.questions_prompt
                st.info("Starting analysis...")
                # Run analysis
                results = analyzer.analyze_cv(st.session_state.extracted_cv_path, st.session_state.current_session_id)
                st.session_state.analysis_results = results
                st.success("Analysis completed successfully!")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
    # Results section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.header("Analysis Results")
        results = st.session_state.analysis_results
        # Display summary
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("Session ID", results['session_id'][:8])
        with col6:
            st.metric("Analysis Passes", len(results['analysis_passes_completed']))
        with col7:
            detected_sections = [k.replace('has_', '') for k, v in results['cv_structure_detected'].items() if v]
            st.metric("CV Sections Found", len(detected_sections))
        # Display comprehensive analysis only
        st.subheader("Comprehensive Analysis Report")
        # Create expandable sections for better readability
        with st.expander("View Full Analysis Report", expanded=True):
            st.text_area(
                "Comprehensive Analysis",
                value=results['comprehensive_analysis'],
                height=600,
                key="full_analysis_display"
            )
        # Download button for the report
        st.download_button(
            label="Download Analysis Report",
            data=results['comprehensive_analysis'],
            file_name=f"cv_analysis_{results['session_id'][:8]}.txt",
            mime="text/plain"
        )
    # Question Generation Section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.header("Interview Questions Generation")
        st.write(
            "Generate targeted interview questions based on the CV analysis to help evaluate the candidate effectively.")
        col_q1, col_q2 = st.columns([1, 2])
        with col_q1:
            generate_questions_button = st.button(
                "Generate Interview Questions",
                type="secondary",
                disabled=not (st.session_state.analysis_results and api_key)
            )
            if not st.session_state.analysis_results:
                st.warning("Complete CV analysis first")
            elif not api_key:
                st.warning("Please provide OpenAI API key")
        with col_q2:
            if generate_questions_button and st.session_state.analysis_results and api_key:
                try:
                    analyzer = CVAnalyzer(gpt_model=gpt_model, api_key=api_key)
                    st.info("Generating interview questions...")
                    # Use the comprehensive analysis file path
                    analysis_file_path = st.session_state.analysis_results['final_file_path']
                    # Generate questions using FastAPI method signature
                    questions_results = analyzer.generate_questions(
                        st.session_state.extracted_cv_path,
                        analysis_file_path,
                        st.session_state.current_session_id
                    )
                    st.session_state.questions_results = questions_results
                    st.success("Interview questions generated successfully!")
                except Exception as e:
                    st.error(f"Question generation failed: {str(e)}")
    # Questions Results Display
    if st.session_state.get('questions_results'):
        st.subheader("Generated Interview Questions")
        # Create expandable sections for better readability
        with st.expander("View Interview Questions", expanded=True):
            st.text_area(
                "Interview Questions",
                value=st.session_state.questions_results['response'],
                height=600,
                key="questions_display"
            )
        # Download button for questions
        st.download_button(
            label="Download Interview Questions",
            data=st.session_state.questions_results['response'],
            file_name=f"interview_questions_{st.session_state.current_session_id[:8]}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
