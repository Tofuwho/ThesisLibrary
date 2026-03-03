/**
 * Main Application JavaScript Module
 * Handles core UI functionality and user interactions across the Thesis Library
 * 
 * This module provides:
 * - Navigation state management
 * - Form enhancements and animations
 * - Scroll-based animations and effects
 * - Search functionality
 * - Responsive behavior
 * - Accessibility improvements
 */

/**
 * Initialize main application functionality when DOM is loaded
 * Sets up navigation, form enhancements, animations, and event listeners
 */
document.addEventListener('DOMContentLoaded', function () {
    initializeNavigation();
    enhanceFormElements();
    setupScrollAnimations();
    initializeSearchFunctionality();
    setupResponsiveBehavior();
    enhanceAccessibility();
});

/**
 * Navigation Management
 * Handles active navigation state and navigation interactions
 */

/**
 * Initialize navigation functionality
 * Sets active navigation items based on current page location
 */
function initializeNavigation() {
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    // Set active state for current page navigation
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentLocation === linkPath ||
            (currentLocation.includes(linkPath) && linkPath !== '/')) {
            link.classList.add('active');
        }
    });
}

/**
 * Form Enhancement System
 * Provides enhanced user experience for form elements
 */

/**
 * Enhance form elements with animations and better UX
 * Adds focus states, change animations, and visual feedback
 */
function enhanceFormElements() {
    // Enhanced select dropdown behavior
    const selectElements = document.querySelectorAll('select');

    selectElements.forEach(select => {
        // Add focus animation for better visual feedback
        select.addEventListener('focus', function () {
            this.parentElement.classList.add('focused');
        });

        select.addEventListener('blur', function () {
            this.parentElement.classList.remove('focused');
        });

        // Add change animation to indicate user interaction
        select.addEventListener('change', function () {
            this.classList.add('changed');

            // Remove animation class after transition completes
            setTimeout(() => {
                this.classList.remove('changed');
            }, 300);
        });
    });
}

/**
 * Scroll Animation System
 * Provides smooth reveal animations for content as user scrolls
 */

/**
 * Setup scroll-based reveal animations for page sections
 * Uses Intersection Observer API for performance-optimized animations
 */
function setupScrollAnimations() {
    const sections = document.querySelectorAll('section');

    // Intersection Observer callback for reveal animations
    const revealSection = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Stop observing once revealed to improve performance
                observer.unobserve(entry.target);
            }
        });
    };

    const sectionObserver = new IntersectionObserver(revealSection, {
        root: null,
        threshold: 0.15
    });

    // Observe all sections for reveal animations
    sections.forEach(section => {
        section.classList.add('hidden-section');
        sectionObserver.observe(section);
    });

    // Add hover effects for interactive elements
    setupCardHoverEffects();
}

/**
 * Setup hover effects for thesis and category cards
 * Provides visual feedback and enhanced interactivity
 */
function setupCardHoverEffects() {
    // Add hover effects for thesis cards
    const thesisCards = document.querySelectorAll('.thesis-card');

    thesisCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-10px)';
            this.style.boxShadow = 'var(--shadow-accent)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        });
    });

    // Add hover effects for category cards
    const categoryCards = document.querySelectorAll('.category-card');

    categoryCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-5px) scale(1.02)';
            this.style.boxShadow = 'var(--shadow-accent)';

            // Animate the icon
            const icon = this.querySelector('.category-icon i');
            if (icon) {
                icon.style.transform = 'scale(1.2)';
                icon.style.color = 'var(--luxury-gold)';
            }
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';

            // Reset icon animation
            const icon = this.querySelector('.category-icon i');
            if (icon) {
                icon.style.transform = 'scale(1)';
                icon.style.color = '';
            }
        });
    });
}

/**
 * Search Functionality System
 * Handles search input and filtering functionality
 */

/**
 * Initialize search functionality across the application
 * Sets up search input handlers and filtering logic
 */
function initializeSearchFunctionality() {
    const searchForm = document.querySelector('.hero-search-form');
    const searchInput = document.querySelector('.hero-search-form input');

    if (searchForm && searchInput) {
        // Add focus effects to the search container
        searchInput.addEventListener('focus', function () {
            this.closest('.search-input-group').classList.add('focused');
        });

        searchInput.addEventListener('blur', function () {
            this.closest('.search-input-group').classList.remove('focused');
        });

        // Basic validation before submission
        searchForm.addEventListener('submit', function (e) {
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.classList.add('shake');
                setTimeout(() => searchInput.classList.remove('shake'), 500);
            }
        });
    }
}

/**
 * Responsive Behavior System
 * Handles responsive design interactions and mobile optimizations
 */

/**
 * Setup responsive behavior for different screen sizes
 * Handles mobile menu, responsive layouts, and touch interactions
 */
function setupResponsiveBehavior() {
    // Handle table responsiveness
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });

    // Handle image-heavy sections on mobile
    const handleResize = () => {
        const isMobile = window.innerWidth <= 768;
        document.body.classList.toggle('is-mobile', isMobile);
    };

    window.addEventListener('resize', handleResize);
    handleResize();
}

/**
 * Accessibility Enhancement System
 * Improves accessibility features and keyboard navigation
 */

/**
 * Enhance accessibility features across the application
 * Adds keyboard navigation, ARIA labels, and screen reader support
 */
function enhanceAccessibility() {
    // Add Esc key support for modals
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active, .auth-modal.active');
            if (activeModal) {
                // If hideLoginModal exists (from modal-handler.js)
                if (typeof hideLoginModal === 'function') {
                    hideLoginModal();
                } else {
                    activeModal.classList.remove('active');
                }
            }
        }
    });

    // Add aria-labels to buttons that only have icons
    const iconButtons = document.querySelectorAll('button:not([aria-label])');
    iconButtons.forEach(btn => {
        const icon = btn.querySelector('.fa, .fas, .far, .fab');
        if (icon && btn.innerText.trim() === '') {
            // Try to infer name from icon class
            const iconClass = Array.from(icon.classList).find(c => c.startsWith('fa-'));
            if (iconClass) {
                const label = iconClass.replace('fa-', '').replace('-', ' ');
                btn.setAttribute('aria-label', label);
            }
        }
    });
}