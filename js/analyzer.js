// Analyzer page functionality for Resume AI Platform

// Initialize Analyzer page
function prepareAnalyzerPage() {
    // Initialize file upload
    initializeFileUpload();

    // Initialize tabs
    initializeAnalysisTabs();

    // Initialize analysis section if data exists
    if (window.session.getData().analysisComplete) {
        showAnalysisResults();
    }

    // Initialize questions section if data exists
    if (window.session.getData().questionsGenerated) {
        showQuestionsResults();
    }

    // Initialize analyze button
    document.getElementById('analyze-cv').addEventListener('click', handleAnalyzeCV);

    // Initialize generate questions button
    document.getElementById('generate-questions').addEventListener('click', handleGenerateQuestions);

    // Initialize download buttons
    document.getElementById('download-analysis').addEventListener('click', () => {
        const analysisText = window.session.getData().analysisText;
        window.utils.downloadTextAsFile(analysisText, `cv_analysis_${window.session.getData().sessionId}.txt`);
    });

    if (document.getElementById('download-questions')) {
        document.getElementById('download-questions').addEventListener('click', () => {
            const questionsText = window.session.getData().questionsText;
            window.utils.downloadTextAsFile(questionsText, `cv_questions_${window.session.getData().sessionId}.txt`);
        });
    }

    // Initialize continue to enhancement button
    if (document.getElementById('continue-enhancement')) {
        document.getElementById('continue-enhancement').addEventListener('click', () => {
            navigateToPage('enhancement');
        });
    }
}

// Initialize file upload functionality
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileUpload = document.getElementById('file-upload');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const removeFile = document.getElementById('remove-file');
    const textPreviewContainer = document.getElementById('text-preview-container');
    const textPreview = document.getElementById('text-preview');
    const editText = document.getElementById('edit-text');

    // Check if CV is already uploaded
    const sessionData = window.session.getData();
    if (sessionData.cvUploaded && sessionData.cvText) {
        // Show file info with placeholder data
        fileInfo.style.display = 'flex';
        uploadArea.style.display = 'none';
        fileName.textContent = 'Resume.pdf';
        fileSize.textContent = 'Text loaded from session';

        // Show text preview
        textPreviewContainer.style.display = 'block';
        textPreview.value = sessionData.cvText;
    }

    // File drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('active');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('active');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('active');

        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileUpload.click();
    });

    fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Remove file
    removeFile.addEventListener('click', () => {
        fileInfo.style.display = 'none';
        uploadArea.style.display = 'block';
        textPreviewContainer.style.display = 'none';
        fileUpload.value = '';
        textPreview.value = '';
    });

    // Edit text
    editText.addEventListener('click', () => {
        textPreview.readOnly = !textPreview.readOnly;
        editText.textContent = textPreview.readOnly ? 'Edit Text' : 'Done Editing';
    });
}

// Handle file upload
function handleFileUpload(file) {
    if (file.type !== 'application/pdf') {
        window.utils.showToast('Error', 'Please upload a PDF file', 'error');
        return;
    }

    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const uploadArea = document.getElementById('upload-area');
    const textPreviewContainer = document.getElementById('text-preview-container');
    const textPreview = document.getElementById('text-preview');

    // Show file info
    fileInfo.style.display = 'flex';
    uploadArea.style.display = 'none';
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    // Read file (in a real app, this would send to backend for PDF parsing)
    window.utils.showLoading('Extracting text from PDF...');

    setTimeout(() => {
        // This simulates PDF text extraction
        // In a real app, you would send the file to a backend service
        simulatePdfExtraction(file, (extractedText) => {
            window.utils.hideLoading();

            // Show text preview
            textPreviewContainer.style.display = 'block';
            textPreview.value = extractedText;

            // Save to session data
            window.session.updateData({
                cvUploaded: true,
                cvText: extractedText
            });

            window.utils.showToast('Success', 'CV text extracted successfully', 'success');
        });
    }, 1500);
}

// Simulate PDF extraction (would be a real backend service in production)
function simulatePdfExtraction(file, callback) {
    // This is a mockup - in a real app you would use a PDF parser library
    // or send the file to a backend service

    // For demo, we'll use a FileReader to get the first few bytes
    // then generate mock text based on the file size
    const reader = new FileReader();
    reader.onload = function(e) {
        // Generate mock CV text based on file size to simulate different CVs
        const extractedText = generateMockCvText(file.size);
        callback(extractedText);
    };

    // Read the first few bytes
    const blob = file.slice(0, 4);
    reader.readAsArrayBuffer(blob);
}

// Generate mock CV text based on file size
function generateMockCvText(fileSize) {
    // Use file size to seed a simple random variation
    const seed = fileSize % 1000;

    // Choose a template based on seed
    let template;
    if (seed < 300) {
        template = `
JOHN DOE
Software Engineer
New York, NY | john.doe@email.com | (123) 456-7890

SKILLS
- Programming Languages: JavaScript, Python, Java, C++
- Web Technologies: HTML5, CSS3, React, Angular, Node.js
- Databases: MongoDB, MySQL, PostgreSQL
- Tools: Git, Docker, AWS, Kubernetes

EXPERIENCE

SOFTWARE ENGINEER | XYZ COMPANY | 2020 - PRESENT
- Developed responsive web applications using React and Node.js
- Implemented RESTful APIs and microservices architecture
- Collaborated with cross-functional teams to deliver high-quality software
- Improved application performance by 30% through code optimization

JUNIOR DEVELOPER | ABC CORPORATION | 2018 - 2020
- Assisted in the development of web applications using Angular
- Wrote unit tests and performed code reviews
- Participated in agile development processes
- Contributed to the company's internal tool development

EDUCATION

BACHELOR OF SCIENCE IN COMPUTER SCIENCE | UNIVERSITY OF TECHNOLOGY | 2018
- GPA: 3.8/4.0
- Relevant coursework: Data Structures, Algorithms, Software Engineering

PROJECTS

PERSONAL PORTFOLIO WEBSITE
- Developed a responsive portfolio website using React and CSS Grid
- Implemented smooth scrolling and animations for enhanced user experience

E-COMMERCE PLATFORM
- Built a full-stack e-commerce platform with user authentication and payment processing
- Utilized React, Node.js, and MongoDB for development
`;
    } else if (seed < 600) {
        template = `
JANE SMITH
Data Scientist
San Francisco, CA | jane.smith@email.com | (987) 654-3210

SKILLS
- Programming: Python, R, SQL
- Machine Learning: TensorFlow, PyTorch, scikit-learn
- Data Analysis: Pandas, NumPy, Matplotlib, Tableau
- Big Data: Spark, Hadoop, Hive

EXPERIENCE

SENIOR DATA SCIENTIST | DATA INNOVATIONS INC | 2019 - PRESENT
- Led a team of 3 data scientists in developing predictive models
- Implemented machine learning algorithms for customer segmentation
- Created data visualizations for executive presentations
- Improved forecast accuracy by 25% through model optimization

DATA ANALYST | TECH SOLUTIONS LLC | 2017 - 2019
- Analyzed large datasets to identify business trends and opportunities
- Created automated reporting systems using Python and SQL
- Collaborated with product teams to implement data-driven features
- Conducted A/B testing to optimize user experience

EDUCATION

MASTER OF SCIENCE IN DATA SCIENCE | CALIFORNIA INSTITUTE OF TECHNOLOGY | 2017
- GPA: 3.9/4.0
- Thesis: "Predictive Modeling for E-commerce Customer Behavior"

BACHELOR OF SCIENCE IN STATISTICS | UNIVERSITY OF CALIFORNIA | 2015
- GPA: 3.7/4.0

PROJECTS

CUSTOMER CHURN PREDICTION
- Developed a machine learning model to predict customer churn with 85% accuracy
- Implemented feature engineering and model selection techniques

SENTIMENT ANALYSIS DASHBOARD
- Created a real-time dashboard for social media sentiment analysis
- Used natural language processing and visualization tools
`;
    } else {
        template = `
ROBERT JOHNSON
Product Manager
Boston, MA | robert.johnson@email.com | (456) 789-0123

SKILLS
- Product Management: Roadmapping, User Stories, Agile Methodologies
- Business Analysis: Market Research, Competitive Analysis, User Interviews
- Tools: JIRA, Confluence, Asana, Figma, Google Analytics
- Technical: HTML/CSS, Basic JavaScript, SQL

EXPERIENCE

SENIOR PRODUCT MANAGER | INNOVATIVE TECH | 2018 - PRESENT
- Led the development and launch of 5 new product features
- Conducted user research and created product requirements
- Collaborated with engineering and design teams to deliver solutions
- Increased user engagement by 40% through strategic feature implementation

PRODUCT ANALYST | GLOBAL SOLUTIONS | 2016 - 2018
- Analyzed user behavior data to identify improvement opportunities
- Created product specifications and user stories
- Assisted in sprint planning and backlog prioritization
- Conducted competitive analysis to inform product strategy

EDUCATION

MBA, PRODUCT MANAGEMENT | HARVARD BUSINESS SCHOOL | 2016
- GPA: 3.8/4.0
- Concentration: Technology Management

BACHELOR OF ARTS IN BUSINESS | BOSTON UNIVERSITY | 2014
- GPA: 3.6/4.0

PROJECTS

MOBILE APP REDESIGN
- Led the redesign of a mobile application resulting in 30% increase in user retention
- Conducted user testing and implemented feedback iteratively

PRODUCT LAUNCH STRATEGY
- Developed go-to-market strategy for a new SaaS product
- Created marketing materials and coordinated with sales teams
`;
    }

    return template.trim();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize analysis tabs
function initializeAnalysisTabs() {
    const tabButtons = document.querySelectorAll('.result-tabs .tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// Handle analyze CV
async function handleAnalyzeCV() {
    const textPreview = document.getElementById('text-preview');
    const cvText = textPreview.value.trim();

    if (!cvText) {
        window.utils.showToast('Error', 'Please upload a CV or enter CV text', 'error');
        return;
    }

    // Show analysis section
    document.getElementById('analysis-section').style.display = 'block';
    document.getElementById('analysis-progress').style.display = 'block';
    document.getElementById('analysis-results').style.display = 'none';

    // Update progress bar
    updateProgressBar(0, 'Starting analysis...');

    // Call API
    const result = await window.api.analyzeCV(cvText, (status, progress) => {
        updateProgressBar(progress, status);
    });

    if (result.success) {
        // Update session data
        window.session.updateData({
            analysisComplete: true,
            analysisText: result.data
        });

        // Show results
        showAnalysisResults();

        window.utils.showToast('Success', 'CV analysis completed successfully', 'success');
    } else {
        window.utils.showToast('Error', result.error || 'Failed to analyze CV', 'error');
    }
}

// Update progress bar
function updateProgressBar(progress, status) {
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');

    progressBar.style.width = `${progress}%`;
    progressStatus.textContent = status;
}

// Show analysis results
function showAnalysisResults() {
    const sessionData = window.session.getData();
    const analysisText = sessionData.analysisText;

    // Hide progress, show results
    document.getElementById('analysis-progress').style.display = 'none';
    document.getElementById('analysis-results').style.display = 'block';

    // Update full analysis content
    document.getElementById('full-analysis-content').value = analysisText;

    // Parse analysis to get summary info
    const summaryData = parseAnalysisSummary(analysisText);

    // Update summary stats
    document.getElementById('analyzed-sections').textContent = summaryData.sectionCount;
    document.getElementById('identified-gaps').textContent = summaryData.gapCount;
    document.getElementById('enhancement-score').textContent = summaryData.enhancementScore;

    // Update specific tabs with formatted content
    updateAnalysisTabs(analysisText);
}

// Parse analysis summary data
function parseAnalysisSummary(analysisText) {
    // In a real app, you would parse the analysis text to extract meaningful stats
    // For demo purposes, we'll generate some basic stats

    // Count sections
    const sectionCount = (analysisText.match(/ANALYSIS/g) || []).length;

    // Count gaps (missing elements)
    const gapCount = (analysisText.match(/Missing|missing|Not specified|absent/g) || []).length;

    // Calculate enhancement score (inverse of gap percentage, max 100)
    const textLength = analysisText.length;
    const gapPercentage = Math.min(gapCount / (textLength / 100), 100);
    const enhancementScore = Math.max(0, Math.floor(100 - gapPercentage)) + '%';

    return {
        sectionCount,
        gapCount,
        enhancementScore
    };
}

// Update analysis tabs with formatted content
function updateAnalysisTabs(analysisText) {
    // Extract and format skills analysis
    const skillsMatch = analysisText.match(/SKILLS ANALYSIS[\s\S]*?(?=EXPERIENCE ANALYSIS|EDUCATION ANALYSIS|PROJECTS ANALYSIS|INTEGRATION ANALYSIS|=====)/);
    if (skillsMatch) {
        const skillsHTML = formatAnalysisSection(skillsMatch[0]);
        document.getElementById('skills-analysis-content').innerHTML = skillsHTML;
    }

    // Extract and format experience analysis
    const experienceMatch = analysisText.match(/EXPERIENCE ANALYSIS[\s\S]*?(?=SKILLS ANALYSIS|EDUCATION ANALYSIS|PROJECTS ANALYSIS|INTEGRATION ANALYSIS|=====)/);
    if (experienceMatch) {
        const experienceHTML = formatAnalysisSection(experienceMatch[0]);
        document.getElementById('experience-analysis-content').innerHTML = experienceHTML;
    }

    // Extract and format education analysis
    const educationMatch = analysisText.match(/EDUCATION ANALYSIS[\s\S]*?(?=SKILLS ANALYSIS|EXPERIENCE ANALYSIS|PROJECTS ANALYSIS|INTEGRATION ANALYSIS|=====)/);
    if (educationMatch) {
        const educationHTML = formatAnalysisSection(educationMatch[0]);
        document.getElementById('education-analysis-content').innerHTML = educationHTML;
    }

    // Extract recommendations
    const recommendationsMatch = analysisText.match(/CRITICAL \(Address Immediately\):[\s\S]*?BENEFICIAL \(Address When Possible\):[\s\S]*?(?=Final Professional Assessment|=====)/);
    if (recommendationsMatch) {
        const recommendationsHTML = formatRecommendations(recommendationsMatch[0]);
        document.getElementById('recommendations-content').innerHTML = recommendationsHTML;
    }
}

// Format analysis section for display
function formatAnalysisSection(sectionText) {
    // Replace section headers with styled headers
    let formatted = sectionText.replace(/([A-Z\s]+)(\n=+)/g, '<h3>$1</h3>');

    // Replace subsection headers
    formatted = formatted.replace(/([A-Z\s]+):(?=\n)/g, '<h4>$1:</h4>');

    // Style categories and skills
    formatted = formatted.replace(/CATEGORY: ([^\n]+)/g, '<div class="category"><strong>CATEGORY:</strong> $1</div>');
    formatted = formatted.replace(/SKILL: ([^\n]+)/g, '<div class="skill"><strong>SKILL:</strong> $1</div>');

    // Style validation status
    formatted = formatted.replace(/(Validation Status: Strong)/g, '<span class="validation strong">$1</span>');
    formatted = formatted.replace(/(Validation Status: Moderate)/g, '<span class="validation moderate">$1</span>');
    formatted = formatted.replace(/(Validation Status: Weak)/g, '<span class="validation weak">$1</span>');
    formatted = formatted.replace(/(Validation Status: None)/g, '<span class="validation none">$1</span>');

    // Convert to paragraphs and preserve line breaks
    formatted = '<p>' + formatted.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';

    return formatted;
}

// Format recommendations for display
function formatRecommendations(recommendationsText) {
    // Split into sections
    const sections = recommendationsText.split(/\n[A-Z]+ \(Address [^)]+\):/);
    const headers = recommendationsText.match(/[A-Z]+ \(Address [^)]+\):/g) || [];

    let html = '<div class="recommendations">';

    // Combine headers with content
    for (let i = 0; i < headers.length; i++) {
        const headerClass = headers[i].includes('CRITICAL') ? 'critical' :
                           headers[i].includes('IMPORTANT') ? 'important' : 'beneficial';

        html += `<div class="recommendation-section ${headerClass}">`;
        html += `<h4>${headers[i]}</h4>`;

        // Format list items
        const content = sections[i + 1] || '';
        const items = content.match(/\d+\. [^\n]+/g) || [];

        if (items.length) {
            html += '<ul>';
            items.forEach(item => {
                html += `<li>${item.replace(/^\d+\. /, '')}</li>`;
            });
            html += '</ul>';
        }

        html += '</div>';
    }

    html += '</div>';
    return html;
}

// Handle generate questions
async function handleGenerateQuestions() {
    const sessionData = window.session.getData();

    if (!sessionData.analysisComplete || !sessionData.analysisText) {
        window.utils.showToast('Error', 'Please complete CV analysis first', 'error');
        return;
    }

    window.utils.showLoading('Generating questions...');

    // Call API
    const result = await window.api.generateQuestions(
        sessionData.cvText,
        sessionData.analysisText,
        (status, progress) => {
            document.getElementById('loading-message').textContent = status;
        }
    );

    window.utils.hideLoading();

    if (result.success) {
        // Update session data
        window.session.updateData({
            questionsGenerated: true,
            questionsText: result.data
        });

        // Show questions results
        showQuestionsResults();

        window.utils.showToast('Success', 'Questions generated successfully', 'success');
    } else {
        window.utils.showToast('Error', result.error || 'Failed to generate questions', 'error');
    }
}

// Show questions results
function showQuestionsResults() {
    const sessionData = window.session.getData();
    const questionsText = sessionData.questionsText;

    // Show questions results section
    document.getElementById('questions-results').style.display = 'block';

    // Update questions content
    document.getElementById('questions-content').value = questionsText;

    // Add event listeners to buttons if not already added
    if (!document.getElementById('download-questions').getAttribute('data-initialized')) {
        document.getElementById('download-questions').addEventListener('click', () => {
            window.utils.downloadTextAsFile(questionsText, `cv_questions_${sessionData.sessionId}.txt`);
        });
        document.getElementById('download-questions').setAttribute('data-initialized', 'true');
    }

    if (!document.getElementById('continue-enhancement').getAttribute('data-initialized')) {
        document.getElementById('continue-enhancement').addEventListener('click', () => {
            navigateToPage('enhancement');
        });
        document.getElementById('continue-enhancement').setAttribute('data-initialized', 'true');
    }
}

// Initialize the analyzer page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if on analyzer page
    if (currentPage === 'analyzer') {
        prepareAnalyzerPage();
    }
});
