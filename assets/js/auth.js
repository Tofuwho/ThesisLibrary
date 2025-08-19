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

  if (loginBtn && loginModal) {
    loginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginModal.classList.add('active'); // Use class for modal
      document.body.style.overflow = 'hidden';
    });
  }

  if (closeBtn && loginModal) {
    closeBtn.addEventListener('click', () => {
      loginModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  // === LOGIN SUBMIT HANDLER ===
  // Let login form submit normally (server handles redirect/messages)

  // === SIGNUP SUBMIT HANDLER ===
  // Let signup form submit normally
});

