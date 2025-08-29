function getCSRFToken() {
  // Try to get the CSRF token from the cookie (Django default)
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

document.addEventListener('DOMContentLoaded', () => {
  // === OPEN LOGIN MODAL ON BUTTON CLICK ===
  const loginBtn = document.getElementById('loginButton');
  const loginModal = document.getElementById('authModal');
  const closeBtn = document.getElementById('closeModal');
  const authContainer = document.getElementById('auth-container');

  // Ensure modal is hidden on page load
  if (loginModal) {
    loginModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (loginBtn && loginModal) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.classList.add('active');
      document.body.style.overflow = 'hidden';
      // Reset to login form when opening modal
      if (authContainer) {
        authContainer.classList.remove('right-panel-active');
      }
    });
  }

  if (closeBtn && loginModal) {
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  // Close modal when clicking outside
  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        loginModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

  // === OVERLAY PANEL SWITCHING ===
  const signUpBtn = document.getElementById('signUp');
  const signInBtn = document.getElementById('signIn');

  if (signUpBtn && authContainer) {
    signUpBtn.addEventListener('click', (e) => {
      e.preventDefault();
      authContainer.classList.add('right-panel-active');
    });
  }

  if (signInBtn && authContainer) {
    signInBtn.addEventListener('click', (e) => {
      e.preventDefault();
      authContainer.classList.remove('right-panel-active');
    });
  }

  // === AJAX LOGIN SUBMIT HANDLER ===
  const loginForm = document.getElementById('loginForm'); // Make sure your login form has this ID
  
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Prevent normal form submission
      
      const formData = new FormData(loginForm);
      const submitButton = loginForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      
      // Show loading state
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
          // Login successful - redirect or close modal
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            window.location.reload(); // or redirect to dashboard
          }
        } else {
          // Login failed - show errors in modal
          displayLoginErrors(data.errors || {});
        }
        
      } catch (error) {
        console.error('Login error:', error);
        displayLoginErrors({
          '__all__': ['An error occurred. Please try again.']
        });
      } finally {
        // Reset button state
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  // === AJAX SIGNUP SUBMIT HANDLER ===
  const signupForm = document.getElementById('signupForm'); // Make sure your signup form has this ID
  
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Prevent normal form submission
      
      const formData = new FormData(signupForm);
      const submitButton = signupForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      
      // Show loading state
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Creating Account...';
      }
      
      try {
        const response = await fetch(signupForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Signup successful
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            // Switch to login panel and show success message
            authContainer.classList.remove('right-panel-active');
            showSuccessMessage('Account created successfully! Please sign in.');
          }
        } else {
          // Signup failed - show errors in modal
          displaySignupErrors(data.errors || {});
        }
        
      } catch (error) {
        console.error('Signup error:', error);
        displaySignupErrors({
          '__all__': ['An error occurred. Please try again.']
        });
      } finally {
        // Reset button state
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  // === HELPER FUNCTIONS ===
  function displayLoginErrors(errors) {
    // Clear previous errors
    clearErrors('loginForm');
    
    // Display new errors
    Object.keys(errors).forEach(field => {
      const errorMessages = Array.isArray(errors[field]) ? errors[field] : [errors[field]];
      errorMessages.forEach(message => {
        showFieldError('loginForm', field, message);
      });
    });
  }
  
  function displaySignupErrors(errors) {
    // Clear previous errors
    clearErrors('signupForm');
    
    // Display new errors
    Object.keys(errors).forEach(field => {
      const errorMessages = Array.isArray(errors[field]) ? errors[field] : [errors[field]];
      errorMessages.forEach(message => {
        showFieldError('signupForm', field, message);
      });
    });
  }
  
  function clearErrors(formId) {
    const form = document.getElementById(formId);
    if (form) {
      // Remove existing error messages
      const errorElements = form.querySelectorAll('.error-message');
      errorElements.forEach(el => el.remove());
      
      // Remove error classes from fields
      const errorFields = form.querySelectorAll('.error');
      errorFields.forEach(el => el.classList.remove('error'));
    }
  }
  
  function showFieldError(formId, fieldName, message) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    let fieldElement = null;
    
    if (fieldName === '__all__' || fieldName === 'non_field_errors') {
      // General form errors - show at the top of the form
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message alert alert-danger';
      errorDiv.textContent = message;
      form.insertBefore(errorDiv, form.firstChild);
    } else {
      // Field-specific errors
      fieldElement = form.querySelector(`[name="${fieldName}"]`);
      
      if (fieldElement) {
        fieldElement.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-danger small';
        errorDiv.textContent = message;
        
        // Insert error message after the field
        fieldElement.parentNode.insertBefore(errorDiv, fieldElement.nextSibling);
      }
    }
  }
  
  function showSuccessMessage(message) {
    // You can customize this based on your UI
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message alert alert-success';
    successDiv.textContent = message;
    
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.insertBefore(successDiv, loginForm.firstChild);
      
      // Remove success message after 5 seconds
      setTimeout(() => {
        successDiv.remove();
      }, 5000);
    }
  }
});