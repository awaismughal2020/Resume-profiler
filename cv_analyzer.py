import uuid
import os
import re
from datetime import datetime
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


class CVAnalyzer:
    def __init__(self):
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
"""
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

        response = client.chat.completions.create(
            model="o1-mini",
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


# Initialize analyzer
cv_analyzer = CVAnalyzer()


@app.get("/review-profile-adaptive")
async def review_profile_adaptive():
    """Adaptive multi-pass CV analysis that adjusts to CV content"""
    try:
        # Read CV text
        cv_file_path = "resume/cv2_extracted.txt"
        if not os.path.exists(cv_file_path):
            raise HTTPException(status_code=404, detail="CV file not found")

        with open(cv_file_path, "r", encoding='utf-8') as f:
            cv_text = f.read().strip()

        # Generate session UUID
        session_uuid = str(uuid.uuid4())

        # Step 1: Detect CV structure
        cv_structure = cv_analyzer.detect_cv_structure(cv_text)
        print(f"CV Structure detected: {cv_structure}")

        # Step 2: Plan analysis passes
        analysis_passes = cv_analyzer.plan_analysis_passes(cv_structure)
        print(f"Analysis passes planned: {analysis_passes}")

        # Step 3: Execute analysis passes
        analyses = {}
        previous_analyses_text = ""

        for pass_type in analysis_passes:
            print(f"Executing {pass_type}...")

            if pass_type == 'integration_analysis':
                # For integration, include previous analyses
                result = cv_analyzer.call_openai_analysis(
                    cv_analyzer.prompt_templates[pass_type],
                    cv_text,
                    pass_type,
                    previous_analyses_text
                )
            else:
                result = cv_analyzer.call_openai_analysis(
                    cv_analyzer.prompt_templates[pass_type],
                    cv_text,
                    pass_type
                )

            analyses[pass_type] = result
            previous_analyses_text += f"\n\n{pass_type.upper()}:\n{result}"

            # Save intermediate result
            with open(os.path.join(DATA_DIR, f"{session_uuid}_{pass_type}.txt"), "w", encoding='utf-8') as f:
                f.write(result)

        # Step 4: Compile final comprehensive report
        final_report = cv_analyzer.compile_final_report(session_uuid, analyses, cv_structure)

        # Save final report
        final_file_path = os.path.join(DATA_DIR, f"{session_uuid}_comprehensive_analysis.txt")
        with open(final_file_path, "w", encoding='utf-8') as f:
            f.write(final_report)

        return JSONResponse(content={
            "session_id": session_uuid,
            "cv_structure_detected": cv_structure,
            "analysis_passes_completed": analysis_passes,
            "comprehensive_analysis": final_report,
            "individual_analyses": analyses,
            "files_created": [f"{session_uuid}_{pass_type}.txt" for pass_type in analysis_passes] + [
                f"{session_uuid}_comprehensive_analysis.txt"],
            "success": True
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in adaptive analysis: {str(e)}")


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy", "message": "Adaptive CV analysis service is running"})


# Keep original endpoint for backward compatibility
@app.get("/review-profile")
async def review_profile():
    """Original single-pass review (kept for compatibility)"""
    return await review_profile_adaptive()
