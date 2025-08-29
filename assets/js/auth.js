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
  const loginBtn = document.getElementById('loginButton');
  const loginModal = document.getElementById('authModal');
  const closeBtn = document.getElementById('closeModal');
  const authContainer = document.getElementById('auth-container');

  if (loginModal) {
    loginModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (loginBtn && loginModal) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.classList.add('active');
      document.body.style.overflow = 'hidden';
      if (authContainer) authContainer.classList.remove('right-panel-active');
    });
  }

  if (closeBtn && loginModal) {
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        loginModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

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

  // === AJAX LOGIN ===
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(loginForm);
      const submitButton = loginForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
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
