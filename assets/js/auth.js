/**
 * Authentication Module
 * Handles user authentication, login/logout, and form submissions
 * * This module provides:
 * - CSRF token management
 * - Modal event handling (desktop & mobile) via CSS CLASSES ONLY
 * - AJAX form submissions for login/signup
 * - Error handling and user feedback
 * - Verification form logic
 */

/**
 * Retrieves CSRF token from cookies for Django CSRF protection
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
 */
document.addEventListener('DOMContentLoaded', () => {
  // Get DOM elements for modal functionality
  const loginBtn = document.getElementById('loginButton');
  const loginModal = document.getElementById('authModal');
  const closeBtn = document.getElementById('closeModal');
  const authContainer = document.getElementById('auth-container');
  const verifyContainer = document.getElementById('verifyContainer');
  const activationContainer = document.getElementById('activationContainer');
  const activationForm = document.getElementById('activationForm');

  // === 1. SETUP MOBILE-ONLY TOGGLES ===
  if (window.innerWidth <= 768) {
    setupMobileModalToggles();
  }

  // Resize listener to add/remove mobile toggles
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (window.innerWidth <= 768) {
        setupMobileModalToggles();
      } else {
        cleanupMobileModalToggles();
      }
    }, 250);
  });

  // === 2. CORE MODAL LISTENERS ===

  // Initialize modal state - ensure it's hidden on page load
  if (loginModal) {
    loginModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Handle login button clicks (opens modal)
  if (loginBtn && loginModal) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showLoginModal();
    });
  }

  /**
   * Global function to show login modal
   * @param {string} nextUrl - Optional URL to redirect to after successful login
   */
  window.showLoginModal = function (nextUrl) {
    if (!loginModal) return;

    loginModal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Reset to login state
    if (authContainer) {
      authContainer.classList.remove('right-panel-active');
      authContainer.classList.remove('show-verify');
    }

    // If nextUrl is provided, we can handle it (optional implementation)
    if (nextUrl) {
      console.log('Login required for:', nextUrl);
      // You could set a hidden field in the login form or use a URL parameter
    }
  };

  /**
   * Global function to hide login modal
   */
  window.hideLoginModal = function () {
    if (loginModal) {
      loginModal.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

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

  // Handle modal panel switching between login and signup forms (DESKTOP)
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

  // === 3. AJAX FORM HANDLING ===

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

  // === AJAX SIGNUP ===
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.setAttribute('novalidate', 'novalidate');

    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const user_id = document.getElementById('signup-id')?.value?.trim();
      const email = document.getElementById('signup-email')?.value?.trim();
      const password = document.getElementById('signup-password')?.value;
      const signupMessage = document.getElementById('signupMessage');
      const submitButton = signupForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;

      if (signupMessage) {
        signupMessage.textContent = '';
        signupMessage.style.display = 'none';
      }
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
        if (!csrfToken) throw new Error('CSRF token not found');

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
            showVerificationForm(user_id);
            if (signupMessage) {
              signupMessage.textContent = data.message || 'Account created! Please verify your email.';
              signupMessage.style.color = 'green';
              signupMessage.style.display = 'block';
            }
          } else if (data.requires_activation) {
            // Show Activation Form for Premade Accounts
            showActivationForm(data.id, data.email);
            const activationMsg = document.getElementById('activationMessage');
            if (activationMsg) {
              activationMsg.textContent = data.message;
              activationMsg.style.color = 'green';
              activationMsg.style.display = 'block';
            }
            if (signupMessage) {
              signupMessage.textContent = data.message;
              signupMessage.style.color = 'green';
              signupMessage.style.display = 'block';
            }
          } else {
            authContainer.classList.remove('right-panel-active');
            const successMsg = data.message || 'Account created successfully! Please sign in.';
            if (signupMessage) {
              signupMessage.textContent = successMsg;
              signupMessage.style.color = 'green';
              signupMessage.style.display = 'block';
            }
            showSuccessMessage(successMsg);
            signupForm.reset();
          }
        } else {
          const errorMessage = data.error || (data.errors && data.errors['__all__'] ? data.errors['__all__'][0] : 'Unknown error');
          if (signupMessage) {
            signupMessage.textContent = errorMessage;
            signupMessage.style.color = 'red';
            signupMessage.style.display = 'block';
          }
          displaySignupErrors(data.errors || { '__all__': [data.error || 'Unknown error'] });
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

  // === 4. VERIFICATION FORM HANDLING ===
  // === FORGOT PASSWORD HANDLING ===
  const forgotPasswordLink = document.getElementById('forgotPasswordLink');
  const forgotPasswordContainer = document.getElementById('forgotPasswordContainer');
  const resetPasswordContainer = document.getElementById('resetPasswordContainer');
  const backToLoginBtn = document.getElementById('backToLogin');
  const backToForgotBtn = document.getElementById('backToForgot');

  if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', (e) => {
      e.preventDefault();
      // Hide login form and show forgot password form
      document.querySelector('.sign-in-container').style.display = 'none';
      if (forgotPasswordContainer) {
        forgotPasswordContainer.style.display = 'block';
      }
    });
  }

  if (backToLoginBtn) {
    backToLoginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      // Show login form and hide forgot password form
      document.querySelector('.sign-in-container').style.display = 'block';
      if (forgotPasswordContainer) {
        forgotPasswordContainer.style.display = 'none';
      }
      if (resetPasswordContainer) {
        resetPasswordContainer.style.display = 'none';
      }
    });
  }

  if (backToForgotBtn) {
    backToForgotBtn.addEventListener('click', (e) => {
      e.preventDefault();
      // Show forgot password form and hide reset password form
      if (forgotPasswordContainer) {
        forgotPasswordContainer.style.display = 'block';
      }
      if (resetPasswordContainer) {
        resetPasswordContainer.style.display = 'none';
      }
    });
  }

  // === FORGOT PASSWORD FORM ===
  const forgotPasswordForm = document.getElementById('forgotPasswordForm');
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(forgotPasswordForm);
      const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      const messageEl = document.getElementById('forgotPasswordMessage');

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Sending...';
      }

      try {
        const response = await fetch(forgotPasswordForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });

        let data;
        try {
          data = await response.json();
        } catch (jsonError) {
          console.error('Failed to parse JSON response:', jsonError);
          if (messageEl) {
            messageEl.textContent = 'An error occurred. Please try again.';
            messageEl.style.color = 'red';
            messageEl.style.display = 'block';
          }
          return;
        }

        if (data.success) {
          if (messageEl) {
            messageEl.textContent = data.message || 'Password reset code has been sent to your email.';
            messageEl.style.color = 'green';
            messageEl.style.display = 'block';
          }
          // Show reset password form
          if (forgotPasswordContainer) {
            forgotPasswordContainer.style.display = 'none';
          }
          if (resetPasswordContainer) {
            resetPasswordContainer.style.display = 'block';
            // Pre-fill the ID field
            const resetIdField = document.getElementById('reset-id');
            if (resetIdField) {
              resetIdField.value = document.getElementById('forgot-id').value;
            }
          }
        } else {
          if (messageEl) {
            messageEl.textContent = data.error || 'An error occurred. Please try again.';
            messageEl.style.color = 'red';
            messageEl.style.display = 'block';
          }
        }
      } catch (error) {
        console.error('Forgot password error:', error);
        if (messageEl) {
          messageEl.textContent = 'An error occurred. Please try again.';
          messageEl.style.color = 'red';
          messageEl.style.display = 'block';
        }
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  // === RESET PASSWORD FORM ===
  const resetPasswordForm = document.getElementById('resetPasswordForm');
  if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(resetPasswordForm);
      const submitButton = resetPasswordForm.querySelector('button[type="submit"]');
      const originalText = submitButton?.textContent;
      const messageEl = document.getElementById('resetPasswordMessage');

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Resetting...';
      }

      try {
        const response = await fetch(resetPasswordForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });
        const data = await response.json();

        if (data.success) {
          if (messageEl) {
            messageEl.textContent = data.message || 'Password reset successfully! You can now log in.';
            messageEl.style.color = 'green';
            messageEl.style.display = 'block';
          }
          // Close modal and redirect to login after 2 seconds
          setTimeout(() => {
            if (loginModal) {
              loginModal.classList.remove('active');
              document.body.style.overflow = '';
            }
            // Reset forms
            if (forgotPasswordContainer) forgotPasswordContainer.style.display = 'none';
            if (resetPasswordContainer) resetPasswordContainer.style.display = 'none';
            document.querySelector('.sign-in-container').style.display = 'block';
            resetPasswordForm.reset();
          }, 2000);
        } else {
          if (messageEl) {
            messageEl.textContent = data.error || 'An error occurred. Please try again.';
            messageEl.style.color = 'red';
            messageEl.style.display = 'block';
          }
        }
      } catch (error) {
        console.error('Reset password error:', error);
        if (messageEl) {
          messageEl.textContent = 'An error occurred. Please try again.';
          messageEl.style.color = 'red';
          messageEl.style.display = 'block';
        }
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText;
        }
      }
    });
  }

  const verifyForm = document.getElementById('verifyForm');
  const backToSignupBtn = document.getElementById('backToSignup');


  //⚠️ FIXED VERIFICATION FUNCTIONS (Verify on Right) ⚠️
  function showVerificationForm(userId) {
    // This function now ONLY adds classes. CSS does the rest.
    if (authContainer) {
      // === THIS IS THE FIX ===
      // We ADD right-panel-active to show the right panel
      authContainer.classList.add('right-panel-active');
      authContainer.classList.add('show-verify'); // Show the verify form
    }
    if (verifyContainer) {
      document.getElementById('verify-id').value = userId;
    }
  }

  function hideVerificationForm() {
    // This function now ONLY removes classes.
    if (authContainer) {
      authContainer.classList.remove('show-verify');
    }
  }

  function showActivationForm(userId, email) {
    const signUpContainer = document.querySelector('.sign-up-container');
    if (authContainer) {
      authContainer.classList.add('right-panel-active');
      authContainer.classList.add('show-activation');
    }
    if (signUpContainer) {
      signUpContainer.style.display = 'none';
    }
    if (activationContainer) {
      activationContainer.style.display = 'block';
      const idField = document.getElementById('activate-id');
      if (idField) idField.value = userId;
    }
    if (verifyContainer) {
      verifyContainer.style.display = 'none';
    }
  }

  function hideActivationForm() {
    const signUpContainer = document.querySelector('.sign-up-container');
    if (authContainer) {
      authContainer.classList.remove('show-activation');
    }
    if (signUpContainer) {
      signUpContainer.style.display = 'flex';
    }
    if (activationContainer) {
      activationContainer.style.display = 'none';
    }
  }

  const backToSignupActivate = document.getElementById('backToSignupFromActivate');
  if (backToSignupActivate) {
    backToSignupActivate.addEventListener('click', () => {
      hideActivationForm();
    });
  }

  if (activationForm) {
    activationForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const userId = document.getElementById('activate-id').value;
      const password = document.getElementById('activate-password').value;
      const confirm = document.getElementById('activate-confirm').value;
      const messageEl = document.getElementById('activationMessage');
      const submitBtn = activationForm.querySelector('button[type="submit"]');

      if (password !== confirm) {
        if (messageEl) {
          messageEl.textContent = 'Passwords do not match.';
          messageEl.style.display = 'block';
        }
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Activating...';
      }

      try {
        const response = await fetch(signupForm.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({
            id: userId,
            password: password,
            action: 'activate_premade'
          })
        });
        const data = await response.json();
        if (data.success) {
          if (messageEl) {
            messageEl.textContent = data.message;
            messageEl.style.color = 'green';
            messageEl.style.display = 'block';
          }
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          if (messageEl) {
            messageEl.textContent = data.error || 'Activation failed.';
            messageEl.style.color = 'red';
            messageEl.style.display = 'block';
          }
        }
      } catch (error) {
        console.error('Activation error:', error);
        if (messageEl) {
          messageEl.textContent = 'An error occurred during activation.';
          messageEl.style.display = 'block';
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Set Password & Activate';
        }
      }
    });
  }

  if (backToSignupBtn) {
    backToSignupBtn.addEventListener('click', () => {
      hideVerificationForm(); // Hide verify
      authContainer.classList.add('right-panel-active'); // Show signup
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
          setTimeout(() => {
            hideVerificationForm(); // Hide verify
            authContainer.classList.remove('right-panel-active'); // Show login
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

  // === 5. HELPER FUNCTIONS (Error/Success/Mobile Toggles) ===

  function displayLoginErrors(errors) {
    clearErrors('loginForm');
    Object.keys(errors).forEach(field => {
      errors[field].forEach(message => showFieldError('loginForm', field, message));
    });
  }

  function displaySignupErrors(errors) {
    clearErrors('signupForm');
    Object.keys(errors).forEach(field => {
      errors[field].forEach(message => showFieldError('signupForm', field, message));
    });
  }

  function clearErrors(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.querySelectorAll('.error-message').forEach(el => el.remove());
  }

  function showFieldError(formId, fieldName, message) {
    const form = document.getElementById(formId);
    if (!form) return;
    if (fieldName === '__all__' || fieldName === 'non_field_errors') {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message alert alert-danger';
      errorDiv.textContent = message;
      form.insertBefore(errorDiv, form.firstChild);
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

  function cleanupMobileModalToggles() {
    const toggles = document.querySelectorAll('.mobile-auth-toggle');
    toggles.forEach(toggle => {
      toggle.remove();
    });
  }

  function setupMobileModalToggles() {
    const signInContainer = document.querySelector('.sign-in-container');
    const signUpContainer = document.querySelector('.sign-up-container');
    const authContainer = document.getElementById('auth-container');

    if (!signInContainer || !signUpContainer || !authContainer) return;
    if (signInContainer.querySelector('.mobile-auth-toggle')) return; // Already exists

    // Create "Don't have an account?" toggle for login form
    const loginToggle = document.createElement('div');
    loginToggle.className = 'mobile-auth-toggle';
    loginToggle.innerHTML = `
          <p>Don't have an account?</p>
          <button type="button" id="mobileSignUpBtn">Sign Up</button>
      `;
    signInContainer.querySelector('form').appendChild(loginToggle);

    // Create "Already have an account?" toggle for signup form
    const signupToggle = document.createElement('div');
    signupToggle.className = 'mobile-auth-toggle';
    signupToggle.innerHTML = `
          <p>Already have an account?</p>
          <button type="button" id="mobileSignInBtn">Sign In</button>
      `;
    signUpContainer.querySelector('form').appendChild(signupToggle);

    // Add event listeners
    const mobileSignUpBtn = document.getElementById('mobileSignUpBtn');
    const mobileSignInBtn = document.getElementById('mobileSignInBtn');

    if (mobileSignUpBtn) {
      mobileSignUpBtn.addEventListener('click', (e) => {
        e.preventDefault();
        authContainer.classList.add('right-panel-active');
      });
    }

    if (mobileSignInBtn) {
      mobileSignInBtn.addEventListener('click', (e) => {
        e.preventDefault();
        authContainer.classList.remove('right-panel-active');
      });
    }
  }
});