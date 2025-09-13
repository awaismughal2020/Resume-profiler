// Authentication functionality for Resume AI Platform

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('authenticated') === 'true';
}

// Show authentication modal
function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'flex';
}

// Hide authentication modal
function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

// Handle login
function handleLogin() {
    const password = document.getElementById('password').value;
    const errorElement = document.getElementById('auth-error');

    // Clear previous error
    errorElement.textContent = '';
    errorElement.style.display = 'none';

    // Validate password
    if (!password) {
        errorElement.textContent = 'Please enter a password';
        errorElement.style.display = 'block';
        return;
    }

    // Check password against configured password
    if (password === CONFIG.DEFAULT_PASSWORD) {
        // Set authentication status
        localStorage.setItem('authenticated', 'true');

        // Hide modal
        hideAuthModal();

        // Initialize app
        initializeApp();
    } else {
        // Show error
        errorElement.textContent = 'Incorrect password. Please try again.';
        errorElement.style.display = 'block';
    }
}

// Handle logout
function handleLogout() {
    // Remove authentication status
    localStorage.removeItem('authenticated');

    // Show login modal
    showAuthModal();
}

// Initialize authentication
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
        showAuthModal();
    } else {
        hideAuthModal();
    }

    // Add event listeners
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });
});
