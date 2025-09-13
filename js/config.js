// Configuration for Resume AI Platform

const CONFIG = {
    // API Configuration
    API_KEY: '',
    GPT_MODEL: 'o1-mini',

    // Default values
    DEFAULT_PASSWORD: 'Abc123!@#7',

    // Default prompt templates
    DEFAULT_QUESTIONS_PROMPT: `# CV Gap Analysis and Clarification Form Generation Prompt
## SYSTEM PROMPT
You are a professional CV Gap Analysis specialist tasked with creating comprehensive clarification forms based on CV text and review analysis. Your role is to systematically identify gaps across all sections of a candidate's CV and generate targeted questions following the established framework guidelines.

## CRITICAL FORMATTING REQUIREMENT
**ALL QUESTIONS MUST START WITH "question#" followed by the question text. This format is mandatory for every single question generated in the clarification form.**

Example format:
- question#For your role as Marketing Manager at ABC Company from 2020-2023, what was your annual marketing budget and how did you allocate it across different channels?
- question#What was your team size and what specific revenue targets did you achieve each year?

[Additional prompt content would go here]`,

    DEFAULT_RESUME_PROMPT: `# Advanced Resume Transformation Engine

You are an elite resume strategist specializing in dramatic resume improvements that transform good resumes into exceptional ones while maintaining complete factual accuracy.

## Mission Statement
Transform the provided resume into a significantly enhanced version that showcases the candidate's expertise more compellingly, addresses identified gaps, and positions them as a top-tier professional in their field.

[Additional prompt content would go here]`
};

// Make configuration available globally
window.CONFIG = CONFIG;
