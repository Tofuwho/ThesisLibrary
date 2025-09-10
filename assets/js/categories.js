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
});

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
    
    // Update the hidden input value
    if (departmentInput) {
        departmentInput.value = departmentId;
    }
    
    // Update visual state
    updateDepartmentButtonStates(button);
    
    // Show/hide appropriate filter groups
    updateFilterGroupVisibility(departmentId);
    
    // Submit the form to apply the filter
    const filterForm = document.getElementById('filter-form');
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
    
    if (filterForm) {
        // Handle checkbox changes for immediate filtering
        const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Auto-submit form when filters change
                setTimeout(() => {
                    filterForm.submit();
                }, 100);
            });
        });
    }
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
