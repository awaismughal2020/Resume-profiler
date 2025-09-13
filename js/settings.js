// Settings page functionality for Resume AI Platform

// Initialize Settings page
function loadSettingsValues() {
    // Load API settings
    const apiKey = localStorage.getItem('openai_api_key') || '';
    const gptModel = localStorage.getItem('gpt_model') || 'o1-mini';

    document.getElementById('api-key').value = apiKey;
    document.getElementById('gpt-model').value = gptModel;

    // Load prompt templates
    const questionsPrompt = localStorage.getItem('questions_prompt') || CONFIG.DEFAULT_QUESTIONS_PROMPT;
    const resumePrompt = localStorage.getItem('resume_prompt') || CONFIG.DEFAULT_RESUME_PROMPT;

    document.getElementById('questions-prompt-template').value = questionsPrompt;
    document.getElementById('resume-prompt-template').value = resumePrompt;

    // Initialize tabs
    initializeSettingsTabs();

    // Add event listeners
    document.getElementById('save-api-settings').addEventListener('click', saveApiSettings);
    document.getElementById('save-questions-prompt').addEventListener('click', saveQuestionsPrompt);
    document.getElementById('save-resume-prompt').addEventListener('click', saveResumePrompt);
    document.getElementById('clear-session-data').addEventListener('click', clearSessionData);
}

// Initialize settings tabs
function initializeSettingsTabs() {
    const tabButtons = document.querySelectorAll('.settings-tabs .tab-btn');
    const tabContents = document.querySelectorAll('.settings-section .tab-content');

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

// Save API settings
function saveApiSettings() {
    const apiKey = document.getElementById('api-key').value.trim();
    const gptModel = document.getElementById('gpt-model').value;

    // Save to localStorage
    localStorage.setItem('openai_api_key', apiKey);
    localStorage.setItem('gpt_model', gptModel);

    // Update CONFIG
    CONFIG.API_KEY = apiKey;
    CONFIG.GPT_MODEL = gptModel;

    window.utils.showToast('Success', 'API settings saved successfully', 'success');
}

// Save questions prompt
function saveQuestionsPrompt() {
    const promptTemplate = document.getElementById('questions-prompt-template').value.trim();

    if (!promptTemplate) {
        window.utils.showToast('Error', 'Prompt template cannot be empty', 'error');
        return;
    }

    // Save to localStorage
    localStorage.setItem('questions_prompt', promptTemplate);

    // Update CONFIG
    CONFIG.QUESTIONS_PROMPT = promptTemplate;

    window.utils.showToast('Success', 'Questions prompt template saved successfully', 'success');
}

// Save resume prompt
function saveResumePrompt() {
    const promptTemplate = document.getElementById('resume-prompt-template').value.trim();

    if (!promptTemplate) {
        window.utils.showToast('Error', 'Prompt template cannot be empty', 'error');
        return;
    }

    // Save to localStorage
    localStorage.setItem('resume_prompt', promptTemplate);

    // Update CONFIG
    CONFIG.RESUME_PROMPT = promptTemplate;

    window.utils.showToast('Success', 'Resume prompt template saved successfully', 'success');
}

// Clear session data
function clearSessionData() {
    if (confirm('Are you sure you want to clear all session data? This action cannot be undone.')) {
        // Reset session
        window.session.resetSession();

        window.utils.showToast('Success', 'Session data cleared successfully', 'success');
    }
}

// Initialize the settings page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if on settings page
    if (currentPage === 'settings') {
        loadSettingsValues();
    }
});
