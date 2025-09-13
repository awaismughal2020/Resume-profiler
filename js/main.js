// Main JavaScript file for Resume AI Platform

// Global variables
let currentPage = 'dashboard';
let sessionData = {
    sessionId: null,
    cvUploaded: false,
    analysisComplete: false,
    questionsGenerated: false,
    enhancementComplete: false,
    cvText: null,
    analysisText: null,
    questionsText: null,
    enhancedResume: null,
    answers: {}
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Check for authentication
    if (!isAuthenticated()) {
        showAuthModal();
    } else {
        hideAuthModal();
        initializeApp();
    }

    // Initialize the auth form
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });

    // Initialize navigation
    initializeNavigation();
});

// Authentication functions
function isAuthenticated() {
    return localStorage.getItem('authenticated') === 'true';
}

function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'flex';
}

function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function handleLogin() {
    const password = document.getElementById('password').value;

    if (password === CONFIG.DEFAULT_PASSWORD) {
        localStorage.setItem('authenticated', 'true');
        hideAuthModal();
        initializeApp();
    } else {
        document.getElementById('auth-error').textContent = 'Incorrect password. Please try again.';
        document.getElementById('auth-error').style.display = 'block';
    }
}

// Initialize application after authentication
function initializeApp() {
    // Load session data from localStorage if available
    loadSessionData();

    // Update UI based on session data
    updateSessionInfo();
    updateDashboardStats();

    // Initialize API settings
    initializeApiSettings();
}

// Navigation functions
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            navigateToPage(page);
        });
    });

    // Initialize dashboard action buttons
    const actionButtons = document.querySelectorAll('.step-action');
    actionButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const target = button.getAttribute('data-target');
            if (target) {
                navigateToPage(target);
            }
        });
    });

    // Navigate to stored page or default to dashboard
    const storedPage = localStorage.getItem('currentPage');
    if (storedPage) {
        navigateToPage(storedPage);
    } else {
        navigateToPage('dashboard');
    }
}

function navigateToPage(page) {
    // Update active nav item
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Show active page
    const pages = document.querySelectorAll('.page');
    pages.forEach(pageEl => {
        if (pageEl.id === `${page}-page`) {
            pageEl.classList.add('active');
        } else {
            pageEl.classList.remove('active');
        }
    });

    // Store current page
    currentPage = page;
    localStorage.setItem('currentPage', page);

    // Initialize page-specific functionality
    switch (page) {
        case 'dashboard':
            updateDashboardStats();
            updateSessionActions();
            break;
        case 'analyzer':
            prepareAnalyzerPage();
            break;
        case 'enhancement':
            prepareEnhancementPage();
            break;
        case 'settings':
            loadSettingsValues();
            break;
    }
}

// Session data functions
function loadSessionData() {
    const savedSession = localStorage.getItem('sessionData');
    if (savedSession) {
        try {
            sessionData = JSON.parse(savedSession);
        } catch (error) {
            console.error('Error parsing session data', error);
            sessionData = {
                sessionId: null,
                cvUploaded: false,
                analysisComplete: false,
                questionsGenerated: false,
                enhancementComplete: false,
                cvText: null,
                analysisText: null,
                questionsText: null,
                enhancedResume: null,
                answers: {}
            };
        }
    }

    // Generate new session ID if none exists
    if (!sessionData.sessionId) {
        sessionData.sessionId = generateSessionId();
        saveSessionData();
    }
}

function saveSessionData() {
    localStorage.setItem('sessionData', JSON.stringify(sessionData));
    updateSessionInfo();
    updateDashboardStats();
}

function updateSessionInfo() {
    document.getElementById('session-id').textContent = sessionData.sessionId || 'Not Started';

    const statusElement = document.getElementById('session-status');
    if (sessionData.enhancementComplete) {
        statusElement.textContent = 'Complete';
        statusElement.className = 'value status-badge active';
    } else if (sessionData.analysisComplete) {
        statusElement.textContent = 'In Progress';
        statusElement.className = 'value status-badge pending';
    } else if (sessionData.cvUploaded) {
        statusElement.textContent = 'Started';
        statusElement.className = 'value status-badge pending';
    } else {
        statusElement.textContent = 'Inactive';
        statusElement.className = 'value status-badge';
    }
}

function updateDashboardStats() {
    document.getElementById('cv-status').textContent =
        sessionData.cvUploaded ? 'Uploaded' : 'Not Uploaded';

    document.getElementById('analysis-status').textContent =
        sessionData.analysisComplete ? 'Complete' :
        (sessionData.cvUploaded ? 'Ready' : 'Not Started');

    document.getElementById('enhancement-status').textContent =
        sessionData.enhancementComplete ? 'Complete' :
        (sessionData.questionsGenerated ? 'Ready' : 'Not Started');
}

function updateSessionActions() {
    const actionsContainer = document.getElementById('session-actions');

    if (sessionData.enhancementComplete) {
        actionsContainer.innerHTML = `
            <h2>Resume Ready!</h2>
            <p>Your enhanced resume has been generated and is ready to use.</p>
            <div class="form-actions">
                <button class="btn btn-secondary" id="view-resume">View Resume</button>
                <button class="btn btn-primary" id="start-new">Start New Session</button>
            </div>
        `;

        document.getElementById('view-resume').addEventListener('click', () => {
            navigateToPage('enhancement');
        });

        document.getElementById('start-new').addEventListener('click', resetSession);
    } else if (sessionData.questionsGenerated) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have generated questions based on your CV analysis. Continue to the Enhancement page to complete the process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-enhancement">Continue to Enhancement</button>
            </div>
        `;

        document.getElementById('continue-enhancement').addEventListener('click', () => {
            navigateToPage('enhancement');
        });
    } else if (sessionData.analysisComplete) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have completed the CV analysis. Generate questions to continue the enhancement process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-questions">Generate Questions</button>
            </div>
        `;

        document.getElementById('continue-questions').addEventListener('click', () => {
            navigateToPage('analyzer');
            // Scroll to questions section
            const questionsSection = document.querySelector('.questions-generation');
            if (questionsSection) {
                questionsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    } else if (sessionData.cvUploaded) {
        actionsContainer.innerHTML = `
        } else if (sessionData.cvUploaded) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have uploaded your CV. Continue to the Analyzer page to analyze your resume.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-analysis">Continue to Analysis</button>
            </div>
        `;

        document.getElementById('continue-analysis').addEventListener('click', () => {
            navigateToPage('analyzer');
        });
    } else {
        actionsContainer.innerHTML = `
            <h2>Start Your Session</h2>
            <p>Upload your resume to begin the analysis and enhancement process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="start-upload">Upload Resume</button>
            </div>
        `;

        document.getElementById('start-upload').addEventListener('click', () => {
            navigateToPage('analyzer');
        });
    }
}

function resetSession() {
    if (confirm('Are you sure you want to start a new session? All current data will be lost.')) {
        sessionData = {
            sessionId: generateSessionId(),
            cvUploaded: false,
            analysisComplete: false,
            questionsGenerated: false,
            enhancementComplete: false,
            cvText: null,
            analysisText: null,
            questionsText: null,
            enhancedResume: null,
            answers: {}
        };

        saveSessionData();
        showToast('Success', 'New session started', 'success');
        navigateToPage('dashboard');
    }
}

// Utility functions
function generateSessionId() {
    return Math.random().toString(36).substring(2, 10);
}

function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    document.getElementById('loading-message').textContent = message;
    overlay.classList.add('visible');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('visible');
}

function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toastId = `toast-${Date.now()}`;

    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" data-toast-id="${toastId}">×</button>
    `;

    toastContainer.appendChild(toast);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        dismissToast(toastId);
    }, 5000);

    // Add click event to close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        dismissToast(toastId);
    });
}

function dismissToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.add('hide');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// API Settings
function initializeApiSettings() {
    // Load API key from localStorage
    const apiKey = localStorage.getItem('openai_api_key') || '';
    const gptModel = localStorage.getItem('gpt_model') || 'o1-mini';

    // Store in CONFIG
    CONFIG.API_KEY = apiKey;
    CONFIG.GPT_MODEL = gptModel;
}

// Initialize prompt templates
function loadPromptTemplates() {
    // Try to load from localStorage, or use defaults
    const questionsPrompt = localStorage.getItem('questions_prompt') || CONFIG.DEFAULT_QUESTIONS_PROMPT;
    const resumePrompt = localStorage.getItem('resume_prompt') || CONFIG.DEFAULT_RESUME_PROMPT;

    // Store in CONFIG
    CONFIG.QUESTIONS_PROMPT = questionsPrompt;
    CONFIG.RESUME_PROMPT = resumePrompt;
}

// Helper function to download text as file
function downloadTextAsFile(text, filename) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 0);
}

// Parse questions from text
function parseQuestionsFromText(text) {
    const questions = [];
    const lines = text.split('\n');
    let currentQuestion = '';

    for (const line of lines) {
        const trimmedLine = line.trim();

        if (!trimmedLine) continue;

        // Look for questions with question# prefix
        if (trimmedLine.startsWith('question#')) {
            if (currentQuestion) {
                questions.push(currentQuestion.trim());
            }
            currentQuestion = trimmedLine.replace('question#', '').trim();
        } else if (currentQuestion && !trimmedLine.startsWith('#') && !trimmedLine.startsWith('**') && !trimmedLine.startsWith('-')) {
            // Continue building the current question
            currentQuestion += ' ' + trimmedLine;
        } else if (trimmedLine.includes('?') && trimmedLine.length > 30 && !trimmedLine.startsWith('**') && !trimmedLine.startsWith('#')) {
            // Standalone question
            const cleanedLine = trimmedLine.replace('question#', '').trim();
            if (cleanedLine) {
                questions.push(cleanedLine);
            }
        }
    }

    // Add the last question
    if (currentQuestion) {
        questions.push(currentQuestion.trim());
    }

    // Clean up questions
    return questions.map(q => {
        // Remove numbering and clean up
        q = q.replace(/^\d+\.\s*/, '');
        q = q.replace(/\*\*/g, '').trim();
        return q;
    }).filter(q => q.length > 20 && q.includes('?'));
}

// Export functions that will be used by other modules
window.utils = {
    showLoading,
    hideLoading,
    showToast,
    downloadTextAsFile,
    parseQuestionsFromText
};

window.session = {
    getData: () => sessionData,
    updateData: (newData) => {
        sessionData = { ...sessionData, ...newData };
        saveSessionData();
    },
    resetSession
};