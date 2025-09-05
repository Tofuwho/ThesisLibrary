/**
 * Download Handler Module
 * Handles thesis download functionality with authentication checks
 * 
 * This module provides functions to:
 * - Check authentication before downloads
 * - Show login modal for unauthenticated users
 * - Handle download responses properly
 */

/**
 * Handles download button clicks for thesis files
 * Makes AJAX request to check authentication before allowing download
 * 
 * @param {number} thesisId - The ID of the thesis to download
 */
function handleDownloadClick(thesisId) {
    console.log('Download handler: Processing download request for thesis ID:', thesisId);
    
    // Make AJAX request to check authentication
    fetch(`/thesis/${thesisId}/download/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        console.log('Download handler: Received response with status:', response.status);
        
        // Handle different response types
        if (response.status === 401) {
            // User is not authenticated - show login modal
            console.log('Download handler: User not authenticated, showing login modal');
            return response.json();
        } else if (response.ok) {
            // User is authenticated - proceed with download
            console.log('Download handler: User authenticated, triggering download');
            window.location.href = `/thesis/${thesisId}/download/`;
            return null;
        } else {
            // Other error occurred
            console.log('Download handler: Unexpected error, attempting to parse response');
            return response.json().catch(() => {
                showLoginModal(window.location.pathname);
                return null;
            });
        }
    })
    .then(data => {
        // Process JSON response if available
        if (data && data.require_login) {
            console.log('Download handler: Server requires login, showing modal');
            showLoginModal(window.location.pathname);
        }
    })
    .catch(error => {
        console.error('Download handler: Error occurred during download process:', error);
        showLoginModal(window.location.pathname);
    });
}

/**
 * Retrieves CSRF token from cookies for AJAX requests
 * Required for Django's CSRF protection
 * 
 * @returns {string} CSRF token value
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}
