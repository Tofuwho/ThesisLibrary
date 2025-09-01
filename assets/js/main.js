// Main JavaScript for Thesis Library

document.addEventListener('DOMContentLoaded', function() {
    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentLocation === linkPath || 
            (currentLocation.includes(linkPath) && linkPath !== '/')) {
            link.classList.add('active');
        }
    });

    // Enhanced select dropdown behavior
    const selectElements = document.querySelectorAll('select');
    
    selectElements.forEach(select => {
        // Add focus animation
        select.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        select.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
        
        // Add change animation
        select.addEventListener('change', function() {
            this.classList.add('changed');
            
            setTimeout(() => {
                this.classList.remove('changed');
            }, 300);
        });
    });

    // Add scroll reveal animations for sections
    const sections = document.querySelectorAll('section');
    
    const revealSection = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    };
    
    const sectionObserver = new IntersectionObserver(revealSection, {
        root: null,
        threshold: 0.15
    });
    
    sections.forEach(section => {
        section.classList.add('hidden-section');
        sectionObserver.observe(section);
    });

    // Add hover effects for thesis cards and category cards
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
                icon.style.color = 'rgb(126, 1, 255)';
            }
        });
    });

    // Resource buttons pulse effect
    const resourceButtons = document.querySelectorAll('.resource-button');
    
    resourceButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.classList.add('pulse');
        });
        
        button.addEventListener('mouseleave', function() {
            this.classList.remove('pulse');
        });
    });

    // Custom dropdown enhancement
    document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
        const select = dropdown.querySelector('select');
        
        select.addEventListener('change', function() {
            // Apply a highlight effect when option changes
            dropdown.classList.add('option-changed');
            
            setTimeout(() => {
                dropdown.classList.remove('option-changed');
            }, 500);
        });
    });

    // Search form enhancement
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            if (searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.classList.add('shake');
                
                setTimeout(() => {
                    searchInput.classList.remove('shake');
                }, 600);
            } else {
                // Add loading animation for search
                const searchButton = this.querySelector('.search-button');
                searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
                // Simulate search delay (for demo purposes)
                setTimeout(() => {
                    searchButton.innerHTML = '<span>search</span>';
                }, 1000);
            }
        });
        
        searchInput.addEventListener('focus', function() {
            searchForm.classList.add('focused-form');
        });
        
        searchInput.addEventListener('blur', function() {
            searchForm.classList.remove('focused-form');
        });
    }

    // Logo animation
    const logoSquare = document.querySelector('.logo-square');
    if (logoSquare) {
        logoSquare.addEventListener('mouseenter', function() {
            this.style.transform = 'rotate(45deg)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        logoSquare.addEventListener('mouseleave', function() {
            this.style.transform = 'rotate(0deg)';
        });
    }

    // Add CSS to support JS animations
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .hidden-section {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.8s ease, transform 0.8s ease;
        }
        
        .visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .focused-form {
            box-shadow: 0 0 0 3px rgba(126, 1, 255, 0.3);
        }
        
        .filter-dropdown.focused {
            transform: translateY(-2px);
        }
        
        .category-icon i {
            transition: transform 0.3s ease, color 0.3s ease;
        }
        
        .nav-link:hover {
            transition: color 0.3s ease;
        }
        
        .view-button, .browse-button, .resource-button {
            position: relative;
            overflow: hidden;
        }
        
        .view-button:after, .browse-button:after, .resource-button:after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.2);
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }
        
        .view-button:hover:after, .browse-button:hover:after, .resource-button:hover:after {
            transform: translateX(0);
        }
    `;
    document.head.appendChild(styleElement);

    // Dynamic background effect for hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        // Create subtle pattern elements
        for (let i = 0; i < 5; i++) {
            const patternElement = document.createElement('div');
            patternElement.classList.add('bg-pattern');
            patternElement.style.position = 'absolute';
            patternElement.style.borderRadius = '50%';
            patternElement.style.background = 'rgba(126, 1, 255, 0.05)';
            patternElement.style.pointerEvents = 'none';
            
            // Random positioning and sizing
            const size = Math.random() * 200 + 50;
            patternElement.style.width = `${size}px`;
            patternElement.style.height = `${size}px`;
            patternElement.style.left = `${Math.random() * 100}%`;
            patternElement.style.top = `${Math.random() * 100}%`;
            patternElement.style.animation = `float ${Math.random() * 10 + 20}s infinite ease-in-out`;
            
            hero.appendChild(patternElement);
        }
        
        // Add animation for floating elements
        const floatAnimation = `
            @keyframes float {
                0%, 100% { transform: translate(0, 0) rotate(0deg); }
                25% { transform: translate(5%, 5%) rotate(5deg); }
                50% { transform: translate(0, 10%) rotate(0deg); }
                75% { transform: translate(-5%, 5%) rotate(-5deg); }
            }
        `;
        
        const styleFloat = document.createElement('style');
        styleFloat.textContent = floatAnimation;
        document.head.appendChild(styleFloat);
    }

    // === DEPARTMENT FILTER FUNCTIONALITY ===
    const deptButtons = document.querySelectorAll(".dept-bookmark");
    const filterGroups = document.querySelectorAll(".filter-group");
    const categoriesMain = document.querySelector('.categories-main');
    const deptClassPrefix = 'dept-';
    const departmentInput = document.getElementById('department-input');

    // Debug logging
    console.log('Department buttons found:', deptButtons.length);
    console.log('Filter groups found:', filterGroups.length);
    console.log('Categories main found:', !!categoriesMain);
    console.log('Department input found:', !!departmentInput);
    
    // Log all department buttons and their data attributes
    deptButtons.forEach((btn, index) => {
        const rawColor = btn.getAttribute('data-color');
        const cleanColor = rawColor ? rawColor.toLowerCase().replace(/[^a-z0-9-]/g, '').trim() : '';
        console.log(`Button ${index}:`, {
            text: btn.textContent,
            dataDept: btn.dataset.dept,
            dataColor: btn.dataset.color,
            rawColor: rawColor,
            cleanColor: cleanColor
        });
    });
    
    // Log all filter groups and their data attributes
    filterGroups.forEach((group, index) => {
        console.log(`Filter group ${index}:`, {
            dataDept: group.dataset.dept,
            display: group.style.display
        });
    });

    // Helper to activate department UI
    function activateDepartment(dept) {
        // Normalize the department value
        dept = dept.toString().trim();
        console.log('Activating department:', dept);

        // Hide all filter groups first
        filterGroups.forEach(group => {
            group.style.display = "none";
        });

        // Remove active class from all dept buttons
        deptButtons.forEach(btn => {
            btn.classList.remove("active");
        });

        // Show the matching filter group
        const activeGroup = document.querySelector(`.filter-group[data-dept="${dept}"]`);
        if (activeGroup) {
            activeGroup.style.display = "block";
            console.log('Found and showing filter group for dept:', dept);
        } else {
            console.log('No filter group found for dept:', dept);
        }

        // Highlight the active dept button and get color class
        const activeBtn = document.querySelector(`.dept-bookmark[data-dept="${dept}"]`);
        let colorClass = '';
        
        if (activeBtn) {
            activeBtn.classList.add("active");
            colorClass = activeBtn.getAttribute('data-color') || '';
            console.log('Found and activated button for dept:', dept, 'with color:', colorClass);
        } else if (dept === 'all') {
            const allBtn = document.querySelector('.dept-bookmark[data-dept="all"]');
            if (allBtn) {
                allBtn.classList.add("active");
                console.log('Activated "all" button');
            }
            colorClass = 'all';
        } else {
            console.log('No button found for dept:', dept);
        }

        // Apply color class to main container
        if (categoriesMain) {
            // Remove all existing department color classes
            categoriesMain.className = categoriesMain.className.replace(/\bdept-[^ ]+/g, '').trim();
            
            // Add new color class if not 'all'
            if (colorClass && colorClass !== 'all') {
                // Clean the color class to ensure it's valid for CSS
                // This handles cases where department names have spaces or special characters
                // Example: "College of Engineering Technology" -> "cet " -> "cet"
                const cleanColorClass = colorClass.toLowerCase().replace(/[^a-z0-9-]/g, '').trim();
                if (cleanColorClass) {
                    categoriesMain.classList.add(deptClassPrefix + cleanColorClass);
                    console.log('Applied color class:', deptClassPrefix + cleanColorClass, 'from original:', colorClass);
                    
                    // Debug: Check if CSS variables are being applied
                    const computedStyle = window.getComputedStyle(categoriesMain);
                    const primaryColor = computedStyle.getPropertyValue('--primary-color');
                    const primaryMedium = computedStyle.getPropertyValue('--primary-medium');
                    const primaryLight = computedStyle.getPropertyValue('--primary-light');
                    console.log('CSS variables:', {
                        '--primary-color': primaryColor,
                        '--primary-medium': primaryMedium,
                        '--primary-light': primaryLight
                    });
                    
                    // Check if elements are actually using the variables
                    const heroElement = document.querySelector('.categories-hero');
                    if (heroElement) {
                        const heroStyle = window.getComputedStyle(heroElement);
                        console.log('Hero background:', heroStyle.background);
                        console.log('Hero border:', heroStyle.border);
                    }
                } else {
                    console.warn('No valid color class generated from:', colorClass);
                    // Fallback to default color
                    categoriesMain.classList.add(deptClassPrefix + 'default');
                }
            }
        }

        // Set hidden input value
        if (departmentInput) {
            departmentInput.value = dept;
            console.log('Set department input value to:', dept);
        }
    }

    // On page load, set department from input or query string
    let initialDept = 'all';
    if (departmentInput && departmentInput.value) {
        initialDept = departmentInput.value;
    } else {
        // Check URL parameters for department
        const urlParams = new URLSearchParams(window.location.search);
        const urlDept = urlParams.get('department');
        if (urlDept) {
            initialDept = urlDept;
        }
    }
    
    console.log('Initial department set to:', initialDept);
    
    // Initialize the department UI with a small delay to ensure DOM is ready
    setTimeout(() => {
        activateDepartment(initialDept);
    }, 100);

    // Add click event listeners to department buttons
    deptButtons.forEach(button => {
        button.addEventListener("click", (e) => {
            e.preventDefault(); // Prevent any default button behavior
            
            const selectedDept = button.dataset.dept;
            console.log('Department clicked:', selectedDept); // Debug log
            
            if (!selectedDept) {
                console.error('No department data found for button:', button);
                return;
            }
            
            // Update the UI immediately
            activateDepartment(selectedDept);
            
            // Submit the filter form
            if (departmentInput && departmentInput.form) {
                departmentInput.form.submit();
            }
        });
    });
});