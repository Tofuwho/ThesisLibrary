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
    initializeLocalLinks();
    rebindCoauthors();
    
    // Intercept search form submit for AJAX loading
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(searchForm);
            const params = new URLSearchParams(window.location.search);
            
            for (const [key, value] of formData.entries()) {
                params.set(key, value);
            }
            
            const deptInput = document.getElementById('department-input');
            if (deptInput) {
                params.set('department', deptInput.value);
            } else {
                params.delete('department');
            }
            
            params.delete('page'); // Reset to first page of results
            
            const actionUrl = window.location.pathname + '?' + params.toString();
            loadFilteredResults(actionUrl);
        });
    }

    // Apply theme for initial department
    const urlParams = new URLSearchParams(window.location.search);
    const currentDepartment = urlParams.get('department') || 'all';
    applyDepartmentThemeFromId(currentDepartment);
    
    // Optimize animations: only animate categories on first visit, and only animate results when searching
    optimizeAnimations();
});

// Handle browser Back/Forward navigation using AJAX
window.addEventListener('popstate', function() {
    loadFilteredResults(window.location.href, false);
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
    
    // Trigger submission dynamically via AJAX instead of full page submit
    if (filterForm) {
        if (typeof filterForm.requestSubmit === 'function') {
            filterForm.requestSubmit();
        } else {
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            filterForm.dispatchEvent(submitEvent);
        }
    } else {
        const params = new URLSearchParams(window.location.search);
        params.set('department', departmentId);
        params.delete('page'); // Reset page
        const actionUrl = window.location.pathname + '?' + params.toString();
        loadFilteredResults(actionUrl);
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

    // Add listener for all inputs to mark the button as dirty (needs application)
    filterForm.addEventListener('change', () => {
        if (applyButton) {
            applyButton.classList.add('dirty');
            if (!applyButton.classList.contains('pulse')) {
                applyButton.classList.add('pulse');
            }
        }
    });

    // Intercept filter form submit for AJAX load
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(filterForm);
        const params = new URLSearchParams();
        
        for (const [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }

        // Preserve search queries from current URL if they aren't in the filter form
        const currentUrlParams = new URLSearchParams(window.location.search);
        if (currentUrlParams.has('search') && !params.has('search')) {
            params.set('search', currentUrlParams.get('search'));
        }
        if (currentUrlParams.has('search_mode') && !params.has('search_mode')) {
            params.set('search_mode', currentUrlParams.get('search_mode'));
        }

        // Reset page to 1 on filter submit
        params.delete('page');

        const actionUrl = window.location.pathname + '?' + params.toString();
        loadFilteredResults(actionUrl);
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
    const form = document.getElementById('filter-form');
    if (form) {
        form.reset();
        const deptInput = document.getElementById('department-input');
        if (deptInput) deptInput.value = 'all';
    }
    const url = new URL(window.location.href, window.location.origin);
    url.search = '';
    loadFilteredResults(url.toString());
}

/**
 * Update sort parameter and reload page
 * 
 * @param {string} sortValue - The sort value to apply
 */
function updateSort(sortValue) {
    const url = new URL(window.location.href, window.location.origin);
    url.searchParams.set('sort', sortValue);
    loadFilteredResults(url.toString());
}

/**
 * Load filtered results asynchronously (AJAX)
 */
function loadFilteredResults(url, pushToHistory = true) {
    const resultsContainer = document.querySelector('.cat-thesis-results');
    const sidebarContainer = document.querySelector('.filter-sidebar');
    const heroMetaContainer = document.querySelector('.hero-meta');

    // Add loading class to start transitions
    if (resultsContainer) resultsContainer.classList.add('ajax-loading');
    if (sidebarContainer) sidebarContainer.classList.add('ajax-loading');
    if (heroMetaContainer) heroMetaContainer.classList.add('ajax-loading');

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Update document title
            document.title = doc.title;

            // Replace HTML content of target sections
            if (resultsContainer && doc.querySelector('.cat-thesis-results')) {
                resultsContainer.innerHTML = doc.querySelector('.cat-thesis-results').innerHTML;
            }
            if (sidebarContainer && doc.querySelector('.filter-sidebar')) {
                sidebarContainer.innerHTML = doc.querySelector('.filter-sidebar').innerHTML;
            }
            if (heroMetaContainer && doc.querySelector('.hero-meta')) {
                heroMetaContainer.innerHTML = doc.querySelector('.hero-meta').innerHTML;
            }

            // Rebind all event listeners and UI components on the new DOM structure
            initializeFilterForm();
            initializeFilterGroups();
            initializeLocalLinks();
            rebindCoauthors();

            // Sync the active class and colors on the category bookmark buttons
            const newUrlParams = new URLSearchParams(new URL(url, window.location.origin).search);
            const currentDept = newUrlParams.get('department') || 'all';
            
            const allButtons = document.querySelectorAll('.dept-bookmark');
            allButtons.forEach(button => {
                const buttonDept = button.getAttribute('data-dept') || 'all';
                if (buttonDept === currentDept) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            });

            // Apply correct department color theme
            applyDepartmentThemeFromId(currentDept);

            // Update browser URL
            if (pushToHistory) {
                history.pushState(null, '', url);
            }

            // Trigger entry animation and remove loading state
            setTimeout(() => {
                if (resultsContainer) resultsContainer.classList.remove('ajax-loading');
                if (sidebarContainer) sidebarContainer.classList.remove('ajax-loading');
                if (heroMetaContainer) heroMetaContainer.classList.remove('ajax-loading');
                
                // Re-run search/subsequent-visit animations
                optimizeAnimations();
            }, 50);
        })
        .catch(error => {
            console.error('AJAX Load Error, falling back to full page load:', error);
            if (pushToHistory) {
                window.location.href = url;
            } else {
                window.location.reload();
            }
        });
}

function initializeLocalLinks() {
    // Pagination links
    const paginationLinks = document.querySelectorAll('.pagination a, .page-link');
    paginationLinks.forEach(link => {
        if (link.dataset.ajaxBound) return;
        link.dataset.ajaxBound = "true";
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetUrl = this.getAttribute('href');
            if (targetUrl) {
                const fullUrl = new URL(targetUrl, window.location.href).toString();
                loadFilteredResults(fullUrl);
            }
        });
    });

    // "Did you mean" links
    const didYouMeanLinks = document.querySelectorAll('.deep-search-info a');
    didYouMeanLinks.forEach(link => {
        if (link.dataset.ajaxBound) return;
        link.dataset.ajaxBound = "true";
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetUrl = this.getAttribute('href');
            if (targetUrl) {
                const fullUrl = new URL(targetUrl, window.location.href).toString();
                loadFilteredResults(fullUrl);
            }
        });
    });
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
        ippg: 'ippg',
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
    // Curated palette for known Taguig City University colleges
    const palette = {
        all: '#800000',        // TCU Maroon (heritage color)
        graduate: '#7C3AED',   // Purple/Violet
        ce: '#10B981',         // Emerald Green (Education)
        cict: '#0284C7',       // Sky Blue (ICT/Tech)
        cas: '#F59E0B',        // Amber (Arts & Sciences)
        cbm: '#4F46E5',        // Indigo (Business & Management)
        ccj: '#4B5563',        // Slate/Charcoal (Criminal Justice)
        chtm: '#EF4444',       // Ruby Red (Hospitality & Tourism)
        cet: '#F97316',        // Orange/Rust (Engineering & Tech)
        ippg: '#0D9488',       // Teal (Public Policy & Governance)
        coll: '#800000',       // Maroon
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
    if (!res) return { r: 128, g: 0, b: 0 };
    return { r: parseInt(res[1], 16), g: parseInt(res[2], 16), b: parseInt(res[3], 16) };
}

function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
        h = s = 0; // achromatic
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return {
        h: Math.round(h * 360),
        s: Math.round(s * 100),
        l: Math.round(l * 100)
    };
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
    
    // Set RGB and HSL custom variables on the root for advanced styles
    root.style.setProperty('--dept-accent-rgb', `${r}, ${g}, ${b}`);
    const { h, s, l } = rgbToHsl(r, g, b);
    root.style.setProperty('--dept-accent-h', h);
    root.style.setProperty('--dept-accent-s', `${s}%`);
    root.style.setProperty('--dept-accent-l', `${l}%`);
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
function rebindCoauthors() {
    const moreLinks = document.querySelectorAll('.more-coauthors');
    moreLinks.forEach(link => {
        if (link.dataset.bound) return;
        link.dataset.bound = "true";
        
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const coauthorList = this.previousElementSibling;
            if (coauthorList) {
                coauthorList.querySelectorAll('li.hidden').forEach(li => {
                    li.classList.remove('hidden');
                });
            }
            this.remove();
        });
    });
}

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

    const url = new URL(window.location.href, window.location.origin);
    url.search = '';
    loadFilteredResults(url.toString());
}

