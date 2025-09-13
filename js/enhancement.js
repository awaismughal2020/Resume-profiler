// Enhancement page functionality for Resume AI Platform

// Initialize Enhancement page
function prepareEnhancementPage() {
    const sessionData = window.session.getData();

    // Initialize step navigation
    initializeSteps();

    // Load data from session if available
    if (sessionData.questionsGenerated && sessionData.questionsText) {
        document.getElementById('questions-input').value = sessionData.questionsText;
    }

    if (sessionData.cvUploaded && sessionData.cvText) {
        document.getElementById('cv-text').value = sessionData.cvText;
    }

    if (sessionData.analysisComplete && sessionData.analysisText) {
        document.getElementById('cv-analysis').value = sessionData.analysisText;
    }

    // If resume is already enhanced, go to step 3
    if (sessionData.enhancementComplete && sessionData.enhancedResume) {
        goToStep(3);
        document.getElementById('enhanced-resume').value = sessionData.enhancedResume;
        updateResumeStats();
    }

    // Add event listeners
    document.getElementById('continue-to-questions').addEventListener('click', handleContinueToQuestions);
    document.getElementById('back-to-input').addEventListener('click', () => goToStep(1));
    document.getElementById('generate-resume').addEventListener('click', handleGenerateResume);

    // Add download button listeners
    if (document.getElementById('download-resume')) {
        document.getElementById('download-resume').addEventListener('click', () => {
            const enhancedResume = sessionData.enhancedResume;
            window.utils.downloadTextAsFile(enhancedResume, `enhanced_resume_${sessionData.sessionId}.txt`);
        });
    }

    if (document.getElementById('download-qa-data')) {
        document.getElementById('download-qa-data').addEventListener('click', () => {
            const qaData = {
                sessionId: sessionData.sessionId,
                timestamp: new Date().toISOString(),
                questions: Object.keys(sessionData.answers).map(question => ({
                    question,
                    answer: sessionData.answers[question]
                }))
            };

            const jsonStr = JSON.stringify(qaData, null, 2);
            window.utils.downloadTextAsFile(jsonStr, `qa_data_${sessionData.sessionId}.json`);
        });
    }

    if (document.getElementById('start-new-session')) {
        document.getElementById('start-new-session').addEventListener('click', window.session.resetSession);
    }
}

// Initialize step navigation
function initializeSteps() {
    const steps = document.querySelectorAll('.step');
    const stepPanes = document.querySelectorAll('.step-pane');

    steps.forEach(step => {
        step.addEventListener('click', () => {
            const stepNum = parseInt(step.getAttribute('data-step'));

            // Only allow clicking on completed steps
            if (step.classList.contains('completed') || stepNum === 1) {
                goToStep(stepNum);
            }
        });
    });
}

// Go to specific step
function goToStep(stepNum) {
    const steps = document.querySelectorAll('.step');
    const stepPanes = document.querySelectorAll('.step-pane');

    // Update step indicators
    steps.forEach(step => {
        const num = parseInt(step.getAttribute('data-step'));
        step.classList.remove('active');
        if (num < stepNum) {
            step.classList.add('completed');
        }
    });

    // Set active step
    steps[stepNum - 1].classList.add('active');

    // Show active pane
    stepPanes.forEach(pane => pane.classList.remove('active'));
    stepPanes[stepNum - 1].classList.add('active');
}

// Handle continue to questions button
function handleContinueToQuestions() {
    const questionsInput = document.getElementById('questions-input').value.trim();
    const cvText = document.getElementById('cv-text').value.trim();
    const cvAnalysis = document.getElementById('cv-analysis').value.trim();

    // Validate inputs
    if (!questionsInput) {
        window.utils.showToast('Error', 'Please provide the generated questions', 'error');
        return;
    }

    if (!cvText) {
        window.utils.showToast('Error', 'Please provide the original CV text', 'error');
        return;
    }

    // Save to session data
    window.session.updateData({
        questionsText: questionsInput,
        cvText: cvText,
        analysisText: cvAnalysis,
        questionsGenerated: true
    });

    // Parse questions and generate form
    const questions = window.utils.parseQuestionsFromText(questionsInput);

    if (questions.length === 0) {
        window.utils.showToast('Error', 'No valid questions found. Please check the input format', 'error');
        return;
    }

    generateQuestionForm(questions);
    goToStep(2);
}

// Generate question form
function generateQuestionForm(questions) {
    const formContainer = document.getElementById('questions-form');
    const sessionData = window.session.getData();

    // Clear previous form
    formContainer.innerHTML = '';

    // Add each question
    questions.forEach((question, index) => {
        const questionId = `question-${index}`;
        const savedAnswer = sessionData.answers[question] || '';

        const questionItem = document.createElement('div');
        questionItem.className = 'question-item';
        questionItem.innerHTML = `
            <h3>Question ${index + 1}:</h3>
            <p>${question}</p>
            <div class="form-group">
                <textarea id="${questionId}" placeholder="Your answer...">${savedAnswer}</textarea>
            </div>
        `;

        formContainer.appendChild(questionItem);

        // Add event listener to save answer on change
        document.getElementById(questionId).addEventListener('input', (e) => {
            const answers = { ...sessionData.answers };
            answers[question] = e.target.value;
            window.session.updateData({ answers });
        });
    });
}

// Handle generate resume button
async function handleGenerateResume() {
    const sessionData = window.session.getData();

    // Validate inputs
    if (!sessionData.cvText) {
        window.utils.showToast('Error', 'CV text is missing', 'error');
        return;
    }

    // Check if any questions are answered
    const answeredQuestions = Object.values(sessionData.answers).filter(answer => answer.trim().length > 0);

    if (answeredQuestions.length === 0) {
        if (!confirm('You haven\'t answered any questions. This may result in a resume with minimal improvements. Do you want to continue?')) {
            return;
        }
    }

    window.utils.showLoading('Generating enhanced resume...');

    // Call API
    const result = await window.api.generateEnhancedResume(
        sessionData.cvText,
        sessionData.analysisText || '',
        sessionData.answers,
        (status, progress) => {
            document.getElementById('loading-message').textContent = status;
        }
    );

    window.utils.hideLoading();

    if (result.success) {
        // Update session data
        window.session.updateData({
            enhancementComplete: true,
            enhancedResume: result.data
        });

        // Show enhanced resume
        document.getElementById('enhanced-resume').value = result.data;

        // Update resume stats
        updateResumeStats();

        // Go to step 3
        goToStep(3);

        window.utils.showToast('Success', 'Enhanced resume generated successfully', 'success');
    } else {
        window.utils.showToast('Error', result.error || 'Failed to generate enhanced resume', 'error');
    }
}

// Update resume stats
function updateResumeStats() {
    const sessionData = window.session.getData();

    // Calculate questions answered
    const totalQuestions = Object.keys(sessionData.answers).length;
    const answeredQuestions = Object.values(sessionData.answers).filter(answer => answer.trim().length > 0).length;

    document.getElementById('questions-answered').textContent = `${answeredQuestions}/${totalQuestions}`;

    // Calculate improvement score (simplified)
    const improvementScore = Math.min(Math.floor(20 + (answeredQuestions / totalQuestions) * 80), 100);
    document.getElementById('improvement-score').textContent = `${improvementScore}%`;

    // Set generation date
    document.getElementById('generation-date').textContent = new Date().toLocaleString();
}

// Initialize the enhancement page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if on enhancement page
    if (currentPage === 'enhancement') {
        prepareEnhancementPage();
    }
});
