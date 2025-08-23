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
  // Let login form submit normally (server handles redirect/messages)

  // === SIGNUP SUBMIT HANDLER ===
  // Let signup form submit normally
});

