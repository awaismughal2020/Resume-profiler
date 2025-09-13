// Utility functions for Resume AI Platform

// Show loading overlay
function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    document.getElementById('loading-message').textContent = message;
    overlay.classList.add('visible');
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('visible');
}

// Show toast notification
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

// Dismiss toast notification
function dismissToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.add('hide');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Download text as file
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

// Format date to readable string
function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(date).toLocaleDateString(undefined, options);
}

// Generate random ID
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let id = '';
    for (let i = 0; i < length; i++) {
        id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return id;
}

// Sanitize HTML to prevent XSS
function sanitizeHtml(html) {
    const tempDiv = document.createElement('div');
    tempDiv.textContent = html;
    return tempDiv.innerHTML;
}

// Extract filename from path
function getFilenameFromPath(path) {
    return path.split('\\').pop().split('/').pop();
}

// Validate email address
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Truncate text with ellipsis
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Export utility functions to global scope
window.utils = {
    showLoading,
    hideLoading,
    showToast,
    dismissToast,
    downloadTextAsFile,
    parseQuestionsFromText,
    formatDate,
    generateId,
    sanitizeHtml,
    getFilenameFromPath,
    isValidEmail,
    truncateText
};
