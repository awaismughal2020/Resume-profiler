# Resume Enhancement AI – Prompt Engineering Project  

## Overview  
An AI-powered resume enhancement platform that leverages **prompt engineering** to analyze, review, and professionally rewrite resumes. The system is designed with **two core prompts**:  

1. **Resume Analysis & Question Generation** – provides structured feedback and identifies missing information.  
2. **Resume Rewrite & Optimization** – generates a polished, ATS-friendly, and industry-standard resume.  

---

## System Components  

### 1. Resume Analysis & Question Generation (`review_prompt.txt`)  
- Analyzes uploaded resume content  
- Identifies gaps, weaknesses, and improvement areas  
- Generates **structured feedback with priorities**  
- Creates **clarification questions** for missing information  
- Returns output in **JSON format** with:  
  - `review` (feedback summary)  
  - `questions` (array of clarification questions)  

### 2. Resume Rewrite & Optimization (`generate_prompt.txt`)  
- Takes input: **original resume + review analysis + user answers**  
- Produces an **ATS-optimized, professional resume**  
- Systematically addresses identified gaps  
- Implements improvement recommendations  
- Delivers a **polished, industry-standard resume document**  

---

## API Endpoints  

### `POST /review-profile`  
- **Input:** Resume PDF file  
- **Output:** Structured review + clarification questions  

### `POST /generate-profile`  
- **Input:** `file_id` + `review_file_id` + answered questions  
- **Output:** Improved resume content  

---

## Key Features  
- **ATS optimization** with keyword integration  
- **Gap analysis** and systematic improvements  
- **Professional formatting** and document structure  
- **Industry-specific customizations**  
- **Achievement quantification** for stronger impact  
- **Cultural and geographic adaptations**  

---

## Usage  

1. **Upload resume PDF** to `/review-profile`  
2. **Review structured feedback & answer questions**  
3. **Submit inputs** to `/generate-profile` for optimized resume  

