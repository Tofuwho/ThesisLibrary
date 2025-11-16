// Mobile JavaScript - Handles mobile menu functionality

document.addEventListener('DOMContentLoaded', function() {
    // Only initialize mobile menu on mobile devices
    if (window.innerWidth <= 768) {
        initializeMobileMenu();
        removeMobileScrollAnimations();
        // setupMobileModalToggles(); <-- This is NOW HANDLED BY AUTH.JS
    }

    // Re-initialize on window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth <= 768) {
                initializeMobileMenu();
                removeMobileScrollAnimations();
                // setupMobileModalToggles(); <-- This is NOW HANDLED BY AUTH.JS
            } else {
                cleanupMobileMenu();
            }
        }, 250);
    });
});

function initializeMobileMenu() {
    // Check if mobile menu already exists
    if (document.querySelector('.mobile-menu')) {
        return;
    }

    const mainHeaderInner = document.querySelector('.main-header-inner');
    if (!mainHeaderInner) return;

    // Create hamburger button
    const hamburger = document.createElement('button');
    hamburger.className = 'hamburger-menu';
    hamburger.setAttribute('aria-label', 'Toggle menu');
    hamburger.innerHTML = '<span></span><span></span><span></span>';

    // Create mobile overlay
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';

    // Create mobile menu container
    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';

    // Clone navigation
    const headerFlexCenter = document.querySelector('.header-flex-center');
    if (headerFlexCenter) {
        const navClone = headerFlexCenter.cloneNode(true);
        navClone.style.display = 'block'; // Force display
        mobileMenu.appendChild(navClone);
    }

    // Clone auth buttons
    const authButtons = document.querySelector('.auth-buttons');
    if (authButtons) {
        const authClone = authButtons.cloneNode(true);
        authClone.style.display = 'flex'; // Force display
        mobileMenu.appendChild(authClone);

        // Re-attach event listeners for cloned login button
        const clonedLoginBtn = authClone.querySelector('#loginButton');
        if (clonedLoginBtn) {
            const originalLoginBtn = document.querySelector('#loginButton');
            if (originalLoginBtn) {
                clonedLoginBtn.addEventListener('click', function() {
                    // This click will be caught by the listener in auth.js
                    originalLoginBtn.click();
                });
            }
        }
    }

    // Append elements to DOM
    mainHeaderInner.appendChild(hamburger);
    document.body.appendChild(overlay);
    document.body.appendChild(mobileMenu);

    // Toggle menu function
    function toggleMenu() {
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
    }

    // Close menu function
    function closeMenu() {
        hamburger.classList.remove('active');
        mobileMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Event listeners
    hamburger.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', closeMenu);

    // Close menu when clicking on nav links
    const mobileNavLinks = mobileMenu.querySelectorAll('.nav-link');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Close menu when clicking on login/signup buttons
    const loginButtons = mobileMenu.querySelectorAll('#loginButton, .login-btn');
    loginButtons.forEach(button => {
        button.addEventListener('click', closeMenu);
    });

    // Close menu when clicking on dashboard/auth buttons
    const dashboardButtons = mobileMenu.querySelectorAll('.dashboard-btn');
    dashboardButtons.forEach(button => {
        button.addEventListener('click', closeMenu);
    });

    // Close menu on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
            closeMenu();
        }
    });

}

function cleanupMobileMenu() {
    // Remove mobile menu elements when switching to desktop view
    const hamburger = document.querySelector('.hamburger-menu');
    const overlay = document.querySelector('.mobile-overlay');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (hamburger) hamburger.remove();
    if (overlay) overlay.remove();
    if (mobileMenu) mobileMenu.remove();

    document.body.style.overflow = '';
}

// Remove scroll animation classes on mobile for better performance
function removeMobileScrollAnimations() {
    const heroSection = document.querySelector('.hero-section');
    const sections = document.querySelectorAll('section.hidden-section');

    // Remove animation classes from hero section
    if (heroSection) {
        heroSection.classList.remove('hidden-section', 'visible');
        heroSection.style.opacity = '1';
        heroSection.style.transform = 'none';
    }

    // Remove animation classes from all sections
    sections.forEach(section => {
        section.classList.remove('hidden-section', 'visible');
        section.style.opacity = '1';
        section.style.transform = 'none';
    });
}
