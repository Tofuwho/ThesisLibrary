/**
 * Authentication Module
 * Handles user authentication, login/logout, and form submissions
 * 
 * This module provides:
 * - CSRF token management
 * - Modal event handling
 * - AJAX form submissions for login/signup
 * - Error handling and user feedback
 */

/**
 * Retrieves CSRF token from cookies for Django CSRF protection
 * Required for all POST requests to Django backend
 * 
 * @returns {string} CSRF token value or empty string if not found
 */
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i].trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

/**
 * Initialize authentication module when DOM is loaded
 * Sets up event listeners for modal interactions and form submissions
 */
document.addEventListener('DOMContentLoaded', () => {
  // Get DOM elements for modal functionality
  const loginBtn = document.getElementById('loginButton');
  const loginModal = document.getElementById('authModal');
  const closeBtn = document.getElementById('closeModal');
  const authContainer = document.getElementById('auth-container');

  // Initialize modal state - ensure it's hidden on page load
  if (loginModal) {
    loginModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Handle login button clicks (opens modal)
  if (loginBtn && loginModal) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.classList.add('active');
      document.body.style.overflow = 'hidden';
      if (authContainer) authContainer.classList.remove('right-panel-active');
    });
  }

  // Handle close button clicks (closes modal)
  if (closeBtn && loginModal) {
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  // Handle clicks outside modal content (closes modal)
  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        loginModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

  // Handle modal panel switching between login and signup forms
  const signUpBtn = document.getElementById('signUp');
  const signInBtn = document.getElementById('signIn');

  // Switch to signup form when signup button is clicked
  if (signUpBtn && authContainer) {
    signUpBtn.addEventListener('click', (e) => {
      e.preventDefault();
      authContainer.classList.add('right-panel-active');
    });
  }

  // Switch to login form when signin button is clicked
  if (signInBtn && authContainer) {
    signInBtn.addEventListener('click', (e) => {
      e.preventDefault();
      authContainer.classList.remove('right-panel-active');
    });
  }

  // === AJAX LOGIN FORM HANDLING ===
  /**
   * Handles login form submission via AJAX
   * Prevents page reload and provides user feedback during authentication
   */
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Prevent default form submission
      
      // Prepare form data and UI feedback
      const formData = new FormData(loginForm);
      const submitButton = loginForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      
      // Disable button and show loading state
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Signing In...';
      }

      try {
        const response = await fetch(loginForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });

        const data = await response.json();

        if (data.success) {
          if (data.redirect_url) window.location.href = data.redirect_url;
          else window.location.reload();
        } else {
          displayLoginErrors(data.errors || {});
        }
      } catch (error) {
        console.error('Login error:', error);
        displayLoginErrors({ '__all__': ['An error occurred. Please try again.'] });
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  // === AJAX SIGNUP (FORM + JSON POST) ===
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('signup-username').value;
      const email = document.getElementById('signup-email').value;
      const password = document.getElementById('signup-password').value;
      const submitButton = signupForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Creating Account...';
      }

      try {
        const response = await fetch(signupForm.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          },
          body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (data.success) {
          authContainer.classList.remove('right-panel-active');
          showSuccessMessage('Account created successfully! Please sign in.');
          signupForm.reset();
        } else {
          // Handle JSON error
          const errors = data.errors || { '__all__': [data.error || 'Unknown error'] };
          displaySignupErrors(errors);
        }
      } catch (error) {
        console.error('Signup error:', error);
        displaySignupErrors({ '__all__': ['An error occurred. Please try again.'] });
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  // === Helper Functions ===
  function displayLoginErrors(errors) {
    clearErrors('loginForm');
    Object.keys(errors).forEach(field => {
      const errorMessages = Array.isArray(errors[field]) ? errors[field] : [errors[field]];
      errorMessages.forEach(message => showFieldError('loginForm', field, message));
    });
  }

  function displaySignupErrors(errors) {
    clearErrors('signupForm');
    Object.keys(errors).forEach(field => {
      const errorMessages = Array.isArray(errors[field]) ? errors[field] : [errors[field]];
      errorMessages.forEach(message => showFieldError('signupForm', field, message));
    });
  }

  function clearErrors(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.querySelectorAll('.error-message').forEach(el => el.remove());
    form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
  }

  function showFieldError(formId, fieldName, message) {
    const form = document.getElementById(formId);
    if (!form) return;
    if (fieldName === '__all__' || fieldName === 'non_field_errors') {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message alert alert-danger';
      errorDiv.textContent = message;
      form.insertBefore(errorDiv, form.firstChild);
    } else {
      const fieldElement = form.querySelector(`[name="${fieldName}"]`);
      if (fieldElement) {
        fieldElement.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger small';
        errorDiv.textContent = message;
        fieldElement.parentNode.insertBefore(errorDiv, fieldElement.nextSibling);
      }
    }
  }

  function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message alert alert-success';
    successDiv.textContent = message;
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.insertBefore(successDiv, loginForm.firstChild);
      setTimeout(() => successDiv.remove(), 5000);
    }
  }
});
