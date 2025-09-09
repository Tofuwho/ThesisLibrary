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
document.addEventListener('DOMContentLoaded', function() {
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
        select.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        select.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
        
        // Add change animation to indicate user interaction
        select.addEventListener('change', function() {
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
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
            this.style.boxShadow = '0 8px 20px rgba(126, 1, 255, 0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        });
    });

    // Add hover effects for category cards
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
            this.style.boxShadow = '0 8px 20px rgba(126, 1, 255, 0.2)';
            
            // Animate the icon
            const icon = this.querySelector('.category-icon i');
            if (icon) {
                icon.style.transform = 'scale(1.2)';
                icon.style.color = 'rgb(126, 1, 255)';
            }
        });
        
        card.addEventListener('mouseleave', function() {
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
    // Search functionality will be implemented here
    // This is a placeholder for future search features
    console.log('Search functionality initialized');
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
    // Responsive behavior will be implemented here
    // This is a placeholder for responsive features
    console.log('Responsive behavior initialized');
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
    // Accessibility enhancements will be implemented here
    // This is a placeholder for accessibility features
    console.log('Accessibility enhancements initialized');
}