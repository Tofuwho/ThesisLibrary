/**
 * Theme Management System
 * Handles light/dark theme switching with persistence and system preference detection
 * 
 * This module provides:
 * - Theme switching between light and dark modes
 * - Local storage persistence
 * - System preference detection
 * - Dynamic theme toggle button creation
 * - Smooth theme transitions
 */

/**
 * ThemeManager Class
 * Manages all theme-related functionality including switching, persistence, and UI updates
 */
class ThemeManager {
    /**
     * Initialize the theme manager
     * Sets up initial theme, creates toggle button, and binds events
     */
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'light';
        this.init();
    }

    /**
     * Initialize theme system components
     * Applies current theme, creates toggle button, and sets up event listeners
     */
    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeToggle();
        this.bindEvents();
    }

    /**
     * Retrieve stored theme preference from localStorage
     * 
     * @returns {string|null} The stored theme or null if none exists
     */
    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    /**
     * Store theme preference in localStorage for persistence
     * 
     * @param {string} theme - The theme to store ('light' or 'dark')
     */
    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    /**
     * Apply the specified theme to the document
     * Updates DOM attributes, stores preference, and updates UI elements
     * 
     * @param {string} theme - The theme to apply ('light' or 'dark')
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        this.updateThemeToggleIcon();
    }

    /**
     * Toggle between light and dark themes
     * Switches to the opposite of the current theme
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    /**
     * Create and insert the theme toggle button into the UI
     * Dynamically creates button and places it in the appropriate location
     */
    createThemeToggle() {
        // Check if toggle already exists to prevent duplicates
        if (document.querySelector('.theme-toggle')) {
            return;
        }

        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle theme');
        toggle.innerHTML = this.getThemeIcon();
        
        // Find the header buttons container for proper placement
        const headerButtons = document.querySelector('.nav-right, .auth-buttons, .header-buttons');
        if (headerButtons) {
            headerButtons.appendChild(toggle);
        } else {
            // Fallback: add to header if no specific button container found
            const header = document.querySelector('.main-header, .redesigned-header');
            if (header) {
                const headerInner = header.querySelector('.header-inner, .container');
                if (headerInner) {
                    headerInner.appendChild(toggle);
                }
            }
        }
    }

    /**
     * Get the appropriate icon for the current theme
     * Returns moon icon for light theme, sun icon for dark theme
     * 
     * @returns {string} HTML string for the theme icon
     */
    getThemeIcon() {
        return this.currentTheme === 'light' ? 
            '<i class="fas fa-moon"></i>' : 
            '<i class="fas fa-sun"></i>';
    }

    /**
     * Update the theme toggle button icon
     * Refreshes the icon to match the current theme
     */
    updateThemeToggleIcon() {
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            toggle.innerHTML = this.getThemeIcon();
        }
    }

    /**
     * Bind event listeners for theme interactions
     * Handles toggle button clicks and system preference changes
     */
    bindEvents() {
        // Bind click event to theme toggle button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-toggle')) {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // Listen for system theme changes (prefers-color-scheme)
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                // Only auto-switch if user hasn't manually set a preference
                if (!this.getStoredTheme()) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    /**
     * Get the current active theme
     * 
     * @returns {string} Current theme ('light' or 'dark')
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Set theme programmatically
     * 
     * @param {string} theme - Theme to set ('light' or 'dark')
     */
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
        }
    }
}

/**
 * Initialize theme manager when DOM is loaded
 * Creates global themeManager instance for application-wide access
 */
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

/**
 * Export ThemeManager for use in other scripts (if using modules)
 * Provides compatibility with module systems
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
