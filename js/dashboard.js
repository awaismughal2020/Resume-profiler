// Dashboard functionality for Resume AI Platform

// Update dashboard stats
function updateDashboardStats() {
    const sessionData = window.session.getData();

    // Update CV status
    document.getElementById('cv-status').textContent =
        sessionData.cvUploaded ? 'Uploaded' : 'Not Uploaded';

    // Update analysis status
    document.getElementById('analysis-status').textContent =
        sessionData.analysisComplete ? 'Complete' :
        (sessionData.cvUploaded ? 'Ready' : 'Not Started');

    // Update enhancement status
    document.getElementById('enhancement-status').textContent =
        sessionData.enhancementComplete ? 'Complete' :
        (sessionData.questionsGenerated ? 'Ready' : 'Not Started');

    // Update session actions
    updateSessionActions();
}

// Update session actions on dashboard
function updateSessionActions() {
    const sessionData = window.session.getData();
    const actionsContainer = document.getElementById('session-actions');

    if (!actionsContainer) return;

    if (sessionData.enhancementComplete) {
        actionsContainer.innerHTML = `
            <h2>Resume Ready!</h2>
            <p>Your enhanced resume has been generated and is ready to use.</p>
            <div class="form-actions">
                <button class="btn btn-secondary" id="view-resume-btn">View Resume</button>
                <button class="btn btn-primary" id="start-new-btn">Start New Session</button>
            </div>
        `;

        document.getElementById('view-resume-btn').addEventListener('click', () => {
            window.location.hash = '#enhancement';
            navigateToPage('enhancement');
        });

        document.getElementById('start-new-btn').addEventListener('click', window.session.resetSession);
    } else if (sessionData.questionsGenerated) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have generated questions based on your CV analysis. Continue to the Enhancement page to complete the process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-enhancement-btn">Continue to Enhancement</button>
            </div>
        `;

        document.getElementById('continue-enhancement-btn').addEventListener('click', () => {
            window.location.hash = '#enhancement';
            navigateToPage('enhancement');
        });
    } else if (sessionData.analysisComplete) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have completed the CV analysis. Generate questions to continue the enhancement process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-questions-btn">Generate Questions</button>
            </div>
        `;

        document.getElementById('continue-questions-btn').addEventListener('click', () => {
            window.location.hash = '#analyzer';
            navigateToPage('analyzer');

            // Scroll to questions section after a short delay
            setTimeout(() => {
                const questionsSection = document.querySelector('.questions-generation');
                if (questionsSection) {
                    questionsSection.scrollIntoView({ behavior: 'smooth' });
                }
            }, 500);
        });
    } else if (sessionData.cvUploaded) {
        actionsContainer.innerHTML = `
            <h2>Continue Your Session</h2>
            <p>You have uploaded your CV. Continue to the Analyzer page to analyze your resume.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="continue-analysis-btn">Continue to Analysis</button>
            </div>
        `;

        document.getElementById('continue-analysis-btn').addEventListener('click', () => {
            window.location.hash = '#analyzer';
            navigateToPage('analyzer');
        });
    } else {
        actionsContainer.innerHTML = `
            <h2>Start Your Session</h2>
            <p>Upload your resume to begin the analysis and enhancement process.</p>
            <div class="form-actions">
                <button class="btn btn-primary" id="start-upload-btn">Upload Resume</button>
            </div>
        `;

        document.getElementById('start-upload-btn').addEventListener('click', () => {
            window.location.hash = '#analyzer';
            navigateToPage('analyzer');
        });
    }
}

// Initialize example buttons
function initializeExampleButton() {
    const viewExamplesBtn = document.getElementById('view-examples');

    if (viewExamplesBtn) {
        viewExamplesBtn.addEventListener('click', () => {
            // Example view logic here
            window.utils.showToast('Examples', 'Resume examples functionality would be shown here', 'info');
        });
    }
}

// Initialize dashboard page
document.addEventListener('DOMContentLoaded', () => {
    initializeExampleButton();

    // Update dashboard stats initially if on dashboard page
    if (currentPage === 'dashboard') {
        updateDashboardStats();
    }
});
