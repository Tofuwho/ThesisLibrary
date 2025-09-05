/**
 * Utility Functions Module
 * Contains common utility functions used across the application
 * 
 * This module provides:
 * - CSRF token management
 * - Common DOM manipulation helpers
 * - Error handling utilities
 */

/**
 * Retrieves CSRF token from cookies for Django CSRF protection
 * This is a duplicate of the function in auth.js for modularity
 * 
 * @returns {string} CSRF token value or empty string if not found
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

/**
 * Shows a temporary notification message to the user
 * 
 * @param {string} message - The message to display
 * @param {string} type - The type of notification ('success', 'error', 'info', 'warning')
 * @param {number} duration - How long to show the message in milliseconds (default: 5000)
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after specified duration
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

/**
 * Gets the appropriate icon for notification types
 * 
 * @param {string} type - The notification type
 * @returns {string} FontAwesome icon class name
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Debounces a function to limit how often it can be called
 * Useful for search inputs, resize handlers, etc.
 * 
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to wait
 * @returns {Function} The debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Checks if an element is visible in the viewport
 * 
 * @param {HTMLElement} element - The element to check
 * @returns {boolean} True if element is visible
 */
function isElementVisible(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}
