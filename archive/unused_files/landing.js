document.addEventListener('DOMContentLoaded', function () {
  const openModalBtn = document.getElementById('openModal');
  const authModal = document.getElementById('authModal');
  const closeModalBtn = document.getElementById('closeModal');
  const authContainer = document.getElementById('auth-container');
  const signUpBtn = document.getElementById('signUp');
  const signInBtn = document.getElementById('signIn');
  const exploreBtn = document.getElementById('exploreBtn');

  // Open modal when login button is clicked
  if (openModalBtn) {
    openModalBtn.addEventListener('click', () => {
      authModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }

  // Close modal when close button is clicked
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      authModal.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  // Close modal if click outside auth-container
  if (authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) {
        authModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  }

  // Toggle to sign up panel
  if (signUpBtn) {
    signUpBtn.addEventListener('click', () => {
      authContainer.classList.add('right-panel-active');
    });
  }

  // Toggle to sign in panel
  if (signInBtn) {
    signInBtn.addEventListener('click', () => {
      authContainer.classList.remove('right-panel-active');
    });
  }

  // Explore button logic
  if (exploreBtn) {
    exploreBtn.addEventListener('click', (event) => {
      event.preventDefault();  // <-- ADD THIS to stop form submission/page reload
      
      if (isLoggedIn) {
        window.location.href = 'index.php';
      } else {
        authModal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  }  

  // Header scroll effect
  window.addEventListener('scroll', function () {
    const header = document.querySelector('.landing-header');
    if (header) {
      header.style.boxShadow =
        window.scrollY > 50
          ? '0 2px 20px rgba(0, 0, 0, 0.2)'
          : '0 2px 10px rgba(0, 0, 0, 0.1)';
    }
  });
});
