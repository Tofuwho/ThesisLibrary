document.addEventListener('DOMContentLoaded', () => {
  // LOGIN
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Set a breakpoint here
      const formData = new FormData(loginForm);

      const res = await fetch('auth/login.php', {
        method: 'POST',
        body: formData
      });

      const text = await res.text();
      if (text.trim() === 'success') {
        window.location.href = 'landing.php';
      } else {
        document.getElementById('loginMessage').textContent = text;
      }
    });
  }

  // SIGNUP
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Set a breakpoint here
      const formData = new FormData(signupForm);

      const res = await fetch('auth/signup.php', {
        method: 'POST',
        body: formData
      });

      const text = await res.text();
      if (text.trim() === 'success') {
        window.location.href = 'landing.php';
      } else {
        document.getElementById('signupMessage').textContent = text;
      }
    });
  }
});
