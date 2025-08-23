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
  const loginBtn = document.getElementById('loginButton'); // ID of button in header
  const loginModal = document.getElementById('authModal'); // Updated to match HTML
  const closeBtn = document.getElementById('closeModal'); // Updated to match HTML
  const authContainer = document.getElementById('auth-container');

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

  // === LOGIN SUBMIT HANDLER ===
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(loginForm);

      try {
        const res = await fetch('/auth/login/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCSRFToken()
          },
          body: formData
        });
        let data;
        try {
          data = await res.json();
        } catch (jsonErr) {
          console.error('Failed to parse JSON:', jsonErr);
          document.getElementById('loginMessage').textContent = 'Server error. Please try again.';
          return;
        }
        console.log('Login response:', data);
        if (data.success) {
          window.location.href = '/';
        } else {
          document.getElementById('loginMessage').textContent = data.error || 'Login failed.';
        }
      } catch (err) {
        console.error('Login request failed:', err);
        document.getElementById('loginMessage').textContent = 'Network error. Please try again.';
      }
    });
  }

  // === SIGNUP SUBMIT HANDLER ===
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(signupForm);

      try {
        const res = await fetch('/auth/signup/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCSRFToken()
          },
          body: formData
        });
        let data;
        try {
          data = await res.json();
        } catch (jsonErr) {
          console.error('Failed to parse JSON:', jsonErr);
          document.getElementById('signupMessage').textContent = 'Server error. Please try again.';
          return;
        }
        console.log('Signup response:', data);
        if (data.success) {
          window.location.href = '/';
        } else {
          document.getElementById('signupMessage').textContent = data.error || 'Signup failed.';
        }
      } catch (err) {
        console.error('Signup request failed:', err);
        document.getElementById('signupMessage').textContent = 'Network error. Please try again.';
      }
    });
  }
});

