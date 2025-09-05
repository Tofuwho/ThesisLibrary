/**
 * Modal Handler Module
 * Manages authentication modal functionality
 * 
 * This module provides functions to:
 * - Show/hide login modal
 * - Handle modal state management
 * - Manage next parameter for post-login redirects
 */

/**
 * Shows the login modal with optional redirect URL
 * Adds the current page URL as a hidden input for post-login redirect
 * 
 * @param {string} nextUrl - URL to redirect to after successful login (optional)
 */
function showLoginModal(nextUrl) {
    console.log('Modal handler: Showing login modal with next URL:', nextUrl);
    
    // Get modal elements
    const loginModal = document.getElementById('authModal');
    const authContainer = document.getElementById('auth-container');
    const loginForm = document.getElementById('loginForm');
    
    if (loginModal) {
        // Show modal and prevent body scrolling
        loginModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Ensure login form is visible (not signup)
        if (authContainer) {
            authContainer.classList.remove('right-panel-active');
        }
        
        // Add next parameter to login form for post-login redirect
        if (nextUrl && loginForm) {
            // Remove any existing next input
            const existingNext = loginForm.querySelector('input[name="next"]');
            if (existingNext) {
                existingNext.remove();
            }
            
            // Create and add new next input
            const nextInput = document.createElement('input');
            nextInput.type = 'hidden';
            nextInput.name = 'next';
            nextInput.value = nextUrl;
            loginForm.appendChild(nextInput);
            
            console.log('Modal handler: Added next parameter to login form:', nextUrl);
        }
    } else {
        console.error('Modal handler: Login modal element not found!');
    }
}

/**
 * Hides the login modal and restores body scrolling
 */
function hideLoginModal() {
    console.log('Modal handler: Hiding login modal');
    
    const loginModal = document.getElementById('authModal');
    if (loginModal) {
        loginModal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Switches modal to signup form
 */
function showSignupForm() {
    console.log('Modal handler: Switching to signup form');
    
    const authContainer = document.getElementById('auth-container');
    if (authContainer) {
        authContainer.classList.add('right-panel-active');
    }
}

/**
 * Switches modal to login form
 */
function showLoginForm() {
    console.log('Modal handler: Switching to login form');
    
    const authContainer = document.getElementById('auth-container');
    if (authContainer) {
        authContainer.classList.remove('right-panel-active');
    }
}
