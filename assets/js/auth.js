/**
 * Authentication Module (Refactored for Single-Card Modal)
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

document.addEventListener('DOMContentLoaded', () => {
    const authModal = document.getElementById('authModal');
    const closeModal = document.getElementById('closeModal');
    const loginButton = document.getElementById('loginButton');

    // Form Switching Logic
    window.switchForm = function(targetId) {
        document.querySelectorAll('.auth-form-box').forEach(box => {
            box.classList.remove('active');
        });
        const target = document.getElementById(targetId);
        if (target) target.classList.add('active');
    };

    // Attach listeners to all switch-form links/buttons
    document.querySelectorAll('.switch-form').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            switchForm(el.getAttribute('data-target'));
        });
    });

    // Opening/Closing Modal
    if (loginButton) {
        loginButton.addEventListener('click', (e) => {
            e.preventDefault();
            authModal.classList.add('active');
            switchForm('loginBox');
            document.body.style.overflow = 'hidden';
        });
    }

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            authModal.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    window.onclick = function(event) {
        if (event.target == authModal) {
            authModal.classList.remove('active');
            document.body.style.overflow = '';
        }
    };

    // === AJAX LOGIN ===
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Authenticating...';

            try {
                const response = await fetch(loginForm.action, {
                    method: 'POST',
                    body: new FormData(loginForm),
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken() }
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect_url || '/';
                } else {
                    displayFormError('loginMessage', data.errors || { '__all__': ['Invalid credentials'] });
                }
            } catch (err) {
                displayFormError('loginMessage', { '__all__': ['Connection error. Please try again.'] });
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }

    // === AJAX SIGNUP ===
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = signupForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            const payload = {
                id: document.getElementById('signup-id').value,
                email: document.getElementById('signup-email').value
            };

            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';

            try {
                const response = await fetch(signupForm.action, {
                    method: 'POST',
                    body: JSON.stringify(payload),
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest', 
                        'X-CSRFToken': getCSRFToken() 
                    }
                });
                const data = await response.json();
                if (data.success) {
                    if (data.requires_verification) {
                        document.getElementById('verify-id').value = data.id;
                        switchForm('verifyBox');
                    } else {
                        switchForm('loginBox');
                        alert('Account exists. Please log in.');
                    }
                } else {
                    displayFormError('signupMessage', data.errors || { '__all__': [data.error] });
                }
            } catch (err) {
                displayFormError('signupMessage', { '__all__': ['Request failed.'] });
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }

    // === FORGOT PASSWORD ===
    const forgotForm = document.getElementById('forgotPasswordForm');
    if (forgotForm) {
        forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = forgotForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Requesting...';

            try {
                const response = await fetch(forgotForm.action, {
                    method: 'POST',
                    body: new FormData(forgotForm),
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken() }
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('reset-id').value = document.getElementById('forgot-id').value;
                    switchForm('resetBox');
                    const msg = document.getElementById('resetPasswordMessage');
                    msg.textContent = data.message;
                    msg.style.color = '#27ae60';
                } else {
                    displayFormError('forgotPasswordMessage', { '__all__': [data.error] });
                }
            } catch (err) {
                displayFormError('forgotPasswordMessage', { '__all__': ['Error processing request'] });
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Reset Code';
            }
        });
    }

    // === RESET PASSWORD ===
    const resetForm = document.getElementById('resetPasswordForm');
    if (resetForm) {
        resetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = resetForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            try {
                const response = await fetch(resetForm.action, {
                    method: 'POST',
                    body: new FormData(resetForm),
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken() }
                });
                const data = await response.json();
                if (data.success) {
                    switchForm('loginBox');
                    alert('Password updated successfully!');
                } else {
                    displayFormError('resetPasswordMessage', { '__all__': [data.error] });
                }
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // === VERIFY ACCOUNT ===
    const verifyForm = document.getElementById('verifyForm');
    if (verifyForm) {
        verifyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('verify-id').value;
            const code = document.getElementById('verify-code').value;

            try {
                const response = await fetch(verifyForm.action, {
                    method: 'POST',
                    body: JSON.stringify({ id, code }),
                    headers: { 
                        'Content-Type': 'application/json', 
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCSRFToken() 
                    }
                });
                const data = await response.json();
                if (data.success) {
                    if (data.requires_password_setup) {
                        document.getElementById('activate-id').value = data.id;
                        document.getElementById('activate-code').value = data.code;
                        switchForm('activateBox');
                    } else {
                        switchForm('loginBox');
                        alert('Verified! Please log in.');
                    }
                } else {
                    displayFormError('verifyMessage', { '__all__': [data.error] });
                }
            } catch (err) { }
        });
    }

    // === ACTIVATE ACCOUNT (Final step) ===
    const activationForm = document.getElementById('activationForm');
    if (activationForm) {
        activationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const pwd = document.getElementById('activate-password').value;
            const confirm = document.getElementById('activate-confirm').value;

            if (pwd !== confirm) {
                displayFormError('activationMessage', { '__all__': ['Passwords do not match.'] });
                return;
            }

            const payload = {
                id: document.getElementById('activate-id').value,
                code: document.getElementById('activate-code').value,
                password: pwd
            };

            const submitBtn = activationForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            try {
                const actionUrl = activationForm.getAttribute('action');
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: JSON.stringify(payload),
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCSRFToken()
                    }
                });
                
                const data = await response.json();

                if (data.success) {
                    switchForm('loginBox');
                    alert('Account activated! You can now log in.');
                } else {
                    const errorMsg = data.error || (data.errors ? Object.values(data.errors).flat()[0] : 'Activation failed');
                    displayFormError('activationMessage', { '__all__': [errorMsg] });
                }
            } catch (err) {
                console.error('Activation Error:', err);
                displayFormError('activationMessage', { '__all__': ['Network error. Please check your connection.'] });
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // Helper: Display errors
    function displayFormError(msgId, errors) {
        const el = document.getElementById(msgId);
        if (!el) return;
        let combined = [];
        Object.keys(errors).forEach(k => combined.push(...errors[k]));
        el.textContent = combined[0];
        el.style.color = '#d63031';
        el.style.display = 'block';
    }
});