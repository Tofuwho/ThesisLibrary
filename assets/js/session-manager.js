/**
 * Session Manager
 * Handles session persistence and CSRF token refresh when device wakes from sleep
 * 
 * This script ensures that:
 * 1. CSRF tokens are refreshed when the page regains focus
 * 2. Sessions are validated after sleep/wake events
 * 3. Users are notified if their session expires
 */

(function() {
    let lastActiveTime = Date.now();
    let isPageHidden = false;
    const INACTIVITY_THRESHOLD = 30 * 60 * 1000; // 30 minutes in milliseconds
    const SESSION_CHECK_INTERVAL = 5 * 60 * 1000; // Check session every 5 minutes

    /**
     * Refresh CSRF token from the server
     * This is called when the page regains focus to ensure token is valid
     */
    function refreshCSRFToken() {
        // Django sets CSRF token in cookie, but we should validate it's current
        fetch(window.location.href, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(error => {
            console.log('Session check fetch failed (expected for some pages):', error.message);
        });
    }

    /**
     * Validate session is still active
     * Makes a lightweight request to check if user is still logged in
     */
    function validateSession() {
        // Returns Promise that resolves if session is valid
        fetch('/profile/', {  // Any protected endpoint will work
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                // Session expired
                showSessionExpiredNotification();
            }
        })
        .catch(error => {
            // Network error - session status unclear
            console.log('Could not validate session:', error.message);
        });
    }

    /**
     * Show notification that session has expired
     */
    function showSessionExpiredNotification() {
        const existingNotif = document.getElementById('session-expired-notif');
        if (existingNotif) {
            return; // Don't show duplicate notifications
        }

        const notification = document.createElement('div');
        notification.id = 'session-expired-notif';
        notification.className = 'notification notification-warning session-expired';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #ff9800;
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            max-width: 400px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <strong>⚠️ Session Expired</strong>
                <span>Your session expired while the device was asleep. Please refresh or log in again.</span>
                <button onclick="window.location.reload();" style="
                    background-color: white;
                    color: #ff9800;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                ">REFRESH</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.opacity = '0.8';
            }
        }, 10000);
    }

    /**
     * Handle page visibility changes (when device wakes up)
     * refresh CSRF token and validate session when page becomes visible again
     */
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            isPageHidden = true;
        } else {
            isPageHidden = false;
            const timeSinceLastActive = Date.now() - lastActiveTime;
            
            // If page was hidden for more than inactivity threshold
            if (timeSinceLastActive > INACTIVITY_THRESHOLD) {
                console.log('Device woke up after', Math.round(timeSinceLastActive / 1000), 'seconds');
                refreshCSRFToken();
                validateSession();
            }
        }
    });

    /**
     * Handle window focus events (user returns to window)
     */
    window.addEventListener('focus', () => {
        const timeSinceLastActive = Date.now() - lastActiveTime;
        
        // If significant time has passed, validate session
        if (timeSinceLastActive > INACTIVITY_THRESHOLD) {
            console.log('Window regained focus after', Math.round(timeSinceLastActive / 1000), 'seconds');
            refreshCSRFToken();
            validateSession();
        }
        
        lastActiveTime = Date.now();
    });

    /**
     * Track user activity (prevents false session expirations)
     */
    document.addEventListener('mousemove', () => {
        lastActiveTime = Date.now();
    });

    document.addEventListener('keypress', () => {
        lastActiveTime = Date.now();
    });

    document.addEventListener('click', () => {
        lastActiveTime = Date.now();
    });

    /**
     * Periodically validate session (every 5 minutes)
     * This catches edge cases where session might have expired
     */
    setInterval(() => {
        if (!isPageHidden && !document.hidden) {
            validateSession();
        }
    }, SESSION_CHECK_INTERVAL);

    /**
     * Handle before unload - save last active time
     */
    window.addEventListener('beforeunload', () => {
        sessionStorage.setItem('lastActiveTime', lastActiveTime);
    });

    // Initialize
    lastActiveTime = parseInt(sessionStorage.getItem('lastActiveTime')) || Date.now();
    console.log('Session manager initialized');
})();
