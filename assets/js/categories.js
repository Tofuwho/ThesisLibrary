/**
 * Categories Page JavaScript Module
 * Handles department filtering, filter management, and category-specific functionality
 * 
 * This module provides:
 * - Department button switching
 * - Filter form management
 * - Dynamic filter group visibility
 * - URL parameter handling
 * - Filter state persistence
 */

/**
 * Initialize categories page functionality when DOM is loaded
 * Sets up department switching, filter management, and form interactions
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDepartmentButtons();
    initializeFilterForm();
    initializeFilterGroups();
    restoreFilterState();
    // Apply theme for initial department
    const urlParams = new URLSearchParams(window.location.search);
    const currentDepartment = urlParams.get('department') || 'all';
    applyDepartmentThemeFromId(currentDepartment);
    
    // Optimize animations: only animate categories on first visit, and only animate results when searching
    optimizeAnimations();
});

/**
 * Animation Optimization
 * Controls which elements animate based on first visit and search state
 */
function optimizeAnimations() {
    const urlParams = new URLSearchParams(window.location.search);
    const hasSearch = urlParams.get('search') && urlParams.get('search').trim() !== '';
    const categoriesMain = document.querySelector('.categories-main');
    
    if (!categoriesMain) return;
    
    // Check if this is the first time visiting categories (not just first time on this page load)
    const hasAnimatedBefore = sessionStorage.getItem('categoriesAnimated') === 'true';
    
    if (hasSearch) {
        // When searching: only animate results header and thesis items
        categoriesMain.classList.add('search-mode');
        // Disable all other animations
        disableCategoryAnimations();
        // Enable only results animations
        enableSearchResultsAnimations();
    } else if (!hasAnimatedBefore) {
        // First time visiting: allow all animations
        sessionStorage.setItem('categoriesAnimated', 'true');
        categoriesMain.classList.add('first-visit');
    } else {
        // Subsequent visits without search: disable all animations including thesis items
        categoriesMain.classList.add('subsequent-visit');
        disableCategoryAnimations();
        // Also disable thesis items on subsequent visits
        const thesisItems = document.querySelectorAll('.cat-thesis-item');
        thesisItems.forEach(item => {
            item.classList.add('no-animation');
        });
    }
}

/**
 * Disable category animations (hero, sidebar, etc.)
 * Note: Does not disable thesis items - they are handled separately
 */
function disableCategoryAnimations() {
    const elementsToDisable = [
        '.categories-hero',
        '.academic-header',
        '.university-crest',
        '.categories-hero h1',
        '.categories-hero p',
        '.hero-meta',
        '.hero-search',
        '.filter-sidebar',
        '.department-bookmarks',
        '.dept-bookmark',
        '.cat-thesis-results'
    ];
    
    elementsToDisable.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.classList.add('no-animation');
        });
    });
}

/**
 * Enable animations only for search results (header and thesis items)
 */
function enableSearchResultsAnimations() {
    // Results header should animate
    const resultsHeader = document.querySelector('.cat-results-header');
    if (resultsHeader) {
        resultsHeader.classList.remove('no-animation');
        resultsHeader.classList.add('search-animate');
    }
    
    // Thesis items should animate
    const thesisItems = document.querySelectorAll('.cat-thesis-item');
    thesisItems.forEach((item, index) => {
        item.classList.remove('no-animation');
        item.classList.add('search-animate');
        item.style.setProperty('--i', index);
    });
}

/**
 * Department Button Management
 * Handles department switching and visual state updates
 */

/**
 * Initialize department bookmark buttons
 * Sets up click handlers and visual state management
 */
function initializeDepartmentButtons() {
    const departmentButtons = document.querySelectorAll('.dept-bookmark');
    
    departmentButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            handleDepartmentSwitch(this);
        });
    });
    
    // Set initial active state based on current department
    setActiveDepartmentButton();
}

/**
 * Handle department button click
 * Updates URL, form state, and visual indicators
 * 
 * @param {HTMLElement} button - The clicked department button
 */
function handleDepartmentSwitch(button) {
    const departmentId = button.getAttribute('data-dept');
    const departmentInput = document.getElementById('department-input');
    const filterForm = document.getElementById('filter-form');
    
    // Update the hidden input value
    if (departmentInput) {
        departmentInput.value = departmentId;
    }
    
    // Update visual state
    updateDepartmentButtonStates(button);
    
    // Apply department theme immediately and persist
    applyDepartmentThemeFromButton(button);

    // Show/hide appropriate filter groups
    updateFilterGroupVisibility(departmentId);
    
    // Auto-submit when department changes to trigger immediate filtering
    // as requested by the user. Sidebar filters still require manual Apply.
    if (filterForm) {
        filterForm.submit();
    }
}

/**
 * Update visual states of all department buttons
 * Removes active class from all buttons and adds it to the selected one
 * 
 * @param {HTMLElement} activeButton - The button to mark as active
 */
function updateDepartmentButtonStates(activeButton) {
    const allButtons = document.querySelectorAll('.dept-bookmark');
    
    allButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    activeButton.classList.add('active');
}

/**
 * Set the active department button based on current URL parameters
 * Restores the correct visual state on page load
 */
function setActiveDepartmentButton() {
    const urlParams = new URLSearchParams(window.location.search);
    const currentDepartment = urlParams.get('department') || 'all';
    
    const activeButton = document.querySelector(`[data-dept="${currentDepartment}"]`);
    if (activeButton) {
        updateDepartmentButtonStates(activeButton);
        applyDepartmentThemeFromButton(activeButton);
    }
}

/**
 * Filter Group Management
 * Handles visibility of department-specific filter sections
 */

/**
 * Initialize filter group visibility
 * Sets up the initial state of filter groups based on current department
 */
function initializeFilterGroups() {
    const urlParams = new URLSearchParams(window.location.search);
    const currentDepartment = urlParams.get('department') || 'all';
    
    updateFilterGroupVisibility(currentDepartment);
}

/**
 * Update filter group visibility based on selected department
 * Shows the appropriate filter group and hides others
 * 
 * @param {string} departmentId - The ID of the selected department
 */
function updateFilterGroupVisibility(departmentId) {
    const allFilterGroups = document.querySelectorAll('.filter-group');
    
    allFilterGroups.forEach(group => {
        const groupDept = group.getAttribute('data-dept');
        
        if (groupDept === departmentId) {
            group.style.display = 'block';
        } else {
            group.style.display = 'none';
        }
    });
}

/**
 * Filter Form Management
 * Handles form interactions and state management
 */

/**
 * Initialize filter form functionality
 * Sets up form submission handling and checkbox interactions
 */
function initializeFilterForm() {
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;

    const applyButton = filterForm.querySelector('.apply-filters-button');
    if (!applyButton) return;

    // Add listener for all inputs to mark the button as dirty (needs application)
    filterForm.addEventListener('change', () => {
        applyButton.classList.add('dirty');
        
        // Add a subtle animation/pulsing effect
        if (!applyButton.classList.contains('pulse')) {
            applyButton.classList.add('pulse');
        }
    });
}

/**
 * Restore filter state from URL parameters
 * Checks URL parameters and restores form state on page load
 */
function restoreFilterState() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Restore checkbox states
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        const paramName = checkbox.name;
        const paramValues = urlParams.getAll(paramName);
        
        if (paramValues.includes(checkbox.value)) {
            checkbox.checked = true;
        }
    });
    
    // Restore department input
    const departmentInput = document.getElementById('department-input');
    if (departmentInput) {
        const departmentParam = urlParams.get('department');
        if (departmentParam) {
            departmentInput.value = departmentParam;
        }
    }
}

/**
 * Utility Functions
 * Helper functions for common operations
 */

/**
 * Clear all filters and reset to default state
 * Removes all URL parameters and resets form
 */
function clearAllFilters() {
    const url = new URL(window.location);
    url.search = '';
    window.location.href = url.toString();
}

/**
 * Update sort parameter and reload page
 * 
 * @param {string} sortValue - The sort value to apply
 */
function updateSort(sortValue) {
    const url = new URL(window.location);
    url.searchParams.set('sort', sortValue);
    window.location.href = url.toString();
}

// Make functions globally available for inline onclick handlers
window.updateSort = updateSort;
window.clearAllFilters = clearAllFilters;

/**
 * Department Theme Application
 * Applies a per-department color theme via CSS variables with good contrast
 */
function applyDepartmentThemeFromButton(button) {
    const deptId = button.getAttribute('data-dept') || 'all';
    applyDepartmentThemeFromId(deptId);
}

function applyDepartmentThemeFromId(deptId) {
    const button = document.querySelector(`.dept-bookmark[data-dept="${deptId}"]`);
    let colorKey = (button && button.getAttribute('data-color')) || 'all';
    // Normalize known mappings to existing CSS classes
    const normalize = {
        graduate: 'graduate',
        ce: 'ce',
        cict: 'cict',
        cas: 'cas',
        cbm: 'cbm',
        ccj: 'ccj',
        cee: 'ce',
        cet: 'cet',
        chtm: 'chtm',
        coll: 'coll',
        cols: 'cols',
        colb: 'colb',
        all: 'all'
    };
    colorKey = normalize[colorKey] || colorKey.toLowerCase();
    const accent = pickAccentColor(colorKey);
    setDeptThemeVars(accent);
    setDeptClass(colorKey);
    try { localStorage.setItem('deptTheme', JSON.stringify({ key: colorKey, accent })); } catch (_) {}
}

function pickAccentColor(colorKey) {
    // Curated palette for known keys; fallback uses deterministic HSL from key
    const palette = {
        all: '#6B7280',        // gray-500
        graduate: '#7C3AED',   // violet-600
        ce: '#059669',         // emerald-600
    };
    if (palette[colorKey]) return palette[colorKey];
    return stringToColor(colorKey);
}

function stringToColor(str) {
    // Simple hash -> HSL with medium saturation for readability
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
        hash |= 0;
    }
    const h = Math.abs(hash) % 360;
    const s = 60; // percent
    const l = 45; // percent
    return hslToHex(h, s, l);
}

function hslToHex(h, s, l) {
    s /= 100; l /= 100;
    const k = n => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    const toHex = x => Math.round(x * 255).toString(16).padStart(2, '0');
    return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`;
}

function hexToRgb(hex) {
    const res = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!res) return { r: 107, g: 114, b: 128 };
    return { r: parseInt(res[1], 16), g: parseInt(res[2], 16), b: parseInt(res[3], 16) };
}

function luminance({ r, g, b }) {
    const a = [r, g, b].map(v => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
}

function setDeptThemeVars(accentHex) {
    const root = document.documentElement;
    const { r, g, b } = hexToRgb(accentHex);
    const lum = luminance({ r, g, b });
    const contrast = lum > 0.5 ? '#111827' : '#FFFFFF'; // black or white
    const softBg = `rgba(${r}, ${g}, ${b}, 0.08)`;
    const softBgDark = `rgba(${r}, ${g}, ${b}, 0.18)`;
    const border = `rgba(${r}, ${g}, ${b}, 0.35)`;

    root.style.setProperty('--dept-accent', accentHex);
    root.style.setProperty('--dept-accent-contrast', contrast);
    root.style.setProperty('--dept-bg-soft', softBg);
    root.style.setProperty('--dept-bg-soft-dark', softBgDark);
    root.style.setProperty('--dept-border', border);
}

function setDeptClass(colorKey) {
    const container = document.querySelector('.categories-main');
    if (!container) return;
    // remove existing dept-* classes
    container.className = container.className
        .split(' ')
        .filter(c => !/^dept-/.test(c))
        .join(' ')
        .trim();
    container.classList.add(`dept-${colorKey}`);
}

/**
 * Co-Author List Expand/Collapse
 * Handles showing all co-authors when "+N more" is clicked
 */
document.addEventListener('DOMContentLoaded', function() {
    const moreLinks = document.querySelectorAll('.more-coauthors');

    moreLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const coauthorList = this.previousElementSibling; // assumes <ul> is before link
            coauthorList.querySelectorAll('li.hidden').forEach(li => {
                li.classList.remove('hidden');
            });
            this.remove(); // remove "+N more" link after expanding
        });
    });
});

/**
 * Enhanced clearAllFilters
 * Clears checkboxes and resets department to "all"
 */
function clearAllFilters() {
    const form = document.getElementById('filter-form');
    if (form) {
        form.reset();

        // Reset department explicitly
        const deptInput = document.getElementById('department-input');
        if (deptInput) deptInput.value = 'all';
    }

    // Reload without query params
    const url = new URL(window.location);
    url.search = '';
    window.location.href = url.toString();
}
