        // JavaScript for interactive filters
        document.addEventListener('DOMContentLoaded', function() {
            // Show more functionality
            const showMoreLinks = document.querySelectorAll('.show-more');
            showMoreLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const filterSection = this.parentElement;
                    const hiddenItems = filterSection.querySelectorAll('.filter-list li.hidden');
                    
                    hiddenItems.forEach(item => {
                        item.classList.remove('hidden');
                    });
                    
                    if (hiddenItems.length > 0) {
                        this.textContent = 'Show less';
                    } else {
                        const allItems = filterSection.querySelectorAll('.filter-list li');
                        Array.from(allItems).slice(5).forEach(item => {
                            item.classList.add('hidden');
                        });
                        this.textContent = 'Show more';
                    }
                });
            });
            
            // Sort select change
            const sortSelect = document.getElementById('sort-by');
            if (sortSelect) {
                sortSelect.addEventListener('change', function() {
                    // Add animation class to show change
                    this.classList.add('option-changed');
                    setTimeout(() => {
                        this.classList.remove('option-changed');
                    }, 500);
                    
                    // Here you would typically reload or reorder results
                    // For demo, we'll just add a pulsing effect to thesis items
                    const thesisItems = document.querySelectorAll('.thesis-item');
                    thesisItems.forEach(item => {
                        item.classList.add('pulse');
                        setTimeout(() => {
                            item.classList.remove('pulse');
                        }, 1000);
                    });
                });
            }
            
            // Filter buttons
            const applyButton = document.querySelector('.apply-filters-button');
            const clearButton = document.querySelector('.clear-filters-button');
            
            if (applyButton) {
                applyButton.addEventListener('click', function() {
                    // Add animation to show action
                    this.classList.add('button-active');
                    setTimeout(() => {
                        this.classList.remove('button-active');
                    }, 300);
                    
                    // For demo purposes, add pulse to thesis items
                    const thesisItems = document.querySelectorAll('.thesis-item');
                    thesisItems.forEach(item => {
                        item.classList.add('pulse');
                        setTimeout(() => {
                            item.classList.remove('pulse');
                        }, 1000);
                    });
                });
            }
            
            if (clearButton) {
                clearButton.addEventListener('click', function() {
                    // Clear all checkboxes
                    const checkboxes = document.querySelectorAll('.filter-list input[type="checkbox"]');
                    checkboxes.forEach(checkbox => {
                        checkbox.checked = false;
                    });
                    
                    // Add animation to show action
                    this.classList.add('button-active');
                    setTimeout(() => {
                        this.classList.remove('button-active');
                    }, 300);
                });
            }
        });