function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

document.addEventListener('DOMContentLoaded', () => {
  // LOGIN
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(loginForm);

      const res = await fetch('/auth/login/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken()
        },
        body: formData
      });

      const data = await res.json();
      if (data.success) {
        window.location.href = '/';
      } else {
        document.getElementById('loginMessage').textContent = data.error || 'Login failed.';
      }
    });
  }

  // SIGNUP
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(signupForm);

      const res = await fetch('/auth/signup/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken()
        },
        body: formData
      });

      const data = await res.json();
      if (data.success) {
        window.location.href = '/';
      } else {
        document.getElementById('signupMessage').textContent = data.error || 'Signup failed.';
      }
    });
  }
});
