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
    // Prevent any default form submission
    signupForm.setAttribute('novalidate', 'novalidate'); // Disable HTML5 validation, we'll handle it in JS
    
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const user_id = document.getElementById('signup-id')?.value?.trim();
      const email = document.getElementById('signup-email')?.value?.trim();
      const password = document.getElementById('signup-password')?.value;
      const signupMessage = document.getElementById('signupMessage');
      const submitButton = signupForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;

      // Clear previous messages
      if (signupMessage) {
        signupMessage.textContent = '';
        signupMessage.className = 'error-msg';
        signupMessage.style.display = 'none';
      }

      // Validate inputs
      if (!user_id || !email || !password) {
        if (signupMessage) {
          signupMessage.textContent = 'Please fill in all fields.';
          signupMessage.style.display = 'block';
          signupMessage.style.color = 'red';
        }
        return;
      }

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Creating Account...';
      }

      try {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
          throw new Error('CSRF token not found');
        }

        const response = await fetch(signupForm.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ id: user_id, email, password })
        });

        const data = await response.json();

        if (data.success) {
          if (data.requires_verification) {
            // Show verification form
            showVerificationForm(user_id);
            if (signupMessage) {
              signupMessage.textContent = data.message || 'Account created! Please verify your email.';
              signupMessage.style.color = 'green';
              signupMessage.style.display = 'block';
            }
            showSuccessMessage(data.message || 'Account created! Please verify your email.');
          } else {
            authContainer.classList.remove('right-panel-active');
            if (signupMessage) {
              signupMessage.textContent = 'Account created successfully! Please sign in.';
              signupMessage.style.color = 'green';
              signupMessage.style.display = 'block';
            }
            showSuccessMessage('Account created successfully! Please sign in.');
            signupForm.reset();
          }
        } else {
          // Handle JSON error
          const errorMessage = data.error || (data.errors && data.errors['__all__'] ? data.errors['__all__'][0] : 'Unknown error');
          if (signupMessage) {
            signupMessage.textContent = errorMessage;
            signupMessage.style.color = 'red';
            signupMessage.style.display = 'block';
          }
          const errors = data.errors || { '__all__': [data.error || 'Unknown error'] };
          displaySignupErrors(errors);
        }
      } catch (error) {
        console.error('Signup error:', error);
        const errorMsg = error.message || 'An error occurred. Please try again.';
        if (signupMessage) {
          signupMessage.textContent = errorMsg;
          signupMessage.style.color = 'red';
          signupMessage.style.display = 'block';
        }
        displaySignupErrors({ '__all__': [errorMsg] });
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
      return false;
    });
  }

  // === VERIFICATION FORM HANDLING ===
  const verifyForm = document.getElementById('verifyForm');
  const verifyContainer = document.getElementById('verifyContainer');
  const backToSignupBtn = document.getElementById('backToSignup');
  
  function showVerificationForm(userId) {
    // Hide signup and login forms, show verification form
    const signupContainer = document.querySelector('.sign-up-container');
    const loginContainer = document.querySelector('.sign-in-container');
    
    if (signupContainer) signupContainer.style.display = 'none';
    if (loginContainer) loginContainer.style.display = 'none';
    if (verifyContainer) {
      verifyContainer.style.display = 'block';
      document.getElementById('verify-id').value = userId;
    }
  }

  function hideVerificationForm() {
    const signupContainer = document.querySelector('.sign-up-container');
    const loginContainer = document.querySelector('.sign-in-container');
    
    if (signupContainer) signupContainer.style.display = 'block';
    if (loginContainer) loginContainer.style.display = 'block';
    if (verifyContainer) verifyContainer.style.display = 'none';
  }

  if (backToSignupBtn) {
    backToSignupBtn.addEventListener('click', () => {
      hideVerificationForm();
      authContainer.classList.add('right-panel-active');
    });
  }

  if (verifyForm) {
    verifyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const user_id = document.getElementById('verify-id').value;
      const code = document.getElementById('verify-code').value;
      const submitButton = verifyForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      const verifyMessage = document.getElementById('verifyMessage');

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Verifying...';
      }

      if (verifyMessage) {
        verifyMessage.textContent = '';
        verifyMessage.className = 'error-msg';
      }

      try {
        const response = await fetch(verifyForm.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          },
          body: JSON.stringify({ id: user_id, code })
        });

        const data = await response.json();

        if (data.success) {
          if (verifyMessage) {
            verifyMessage.textContent = data.message || 'Email verified successfully!';
            verifyMessage.className = 'success-msg';
            verifyMessage.style.color = 'green';
          }
          // Hide verification form and show login
          setTimeout(() => {
            hideVerificationForm();
            authContainer.classList.remove('right-panel-active');
            showSuccessMessage('Email verified! You can now log in.');
          }, 2000);
        } else {
          if (verifyMessage) {
            verifyMessage.textContent = data.error || 'Verification failed. Please try again.';
            verifyMessage.className = 'error-msg';
            verifyMessage.style.color = 'red';
          }
        }
      } catch (error) {
        console.error('Verification error:', error);
        if (verifyMessage) {
          verifyMessage.textContent = 'An error occurred. Please try again.';
          verifyMessage.className = 'error-msg';
          verifyMessage.style.color = 'red';
        }
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
