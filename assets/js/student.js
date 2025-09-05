/**
 * Student Dashboard JavaScript Module
 * Handles thesis submission form functionality and user interactions
 * 
 * This module provides:
 * - Multi-step form navigation
 * - File upload management with drag & drop
 * - Auto-save functionality
 * - Form validation
 * - Academic structure management
 * - Real-time form preview
 */

/**
 * Initialize student dashboard functionality when DOM is loaded
 * Sets up all form interactions, file uploads, and auto-save features
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    setupFileUploads();
    setupAutoSave();
    loadSavedData();
    setupAcademicStructure();
});

/**
 * Form Navigation System
 * Handles multi-step form navigation and progress tracking
 */

/**
 * Navigate to the next section in the form
 * Validates current section before proceeding
 * 
 * @param {string} sectionId - The ID of the section to navigate to
 */
function nextSection(sectionId) {
    if (validateCurrentSection()) {
        showSection(sectionId);
        updateReviewSection();
    }
}

/**
 * Navigate to the previous section in the form
 * No validation required for going back
 * 
 * @param {string} sectionId - The ID of the section to navigate to
 */
function previousSection(sectionId) {
    showSection(sectionId);
}

/**
 * Show the specified section and update navigation state
 * Handles section visibility, navigation highlighting, and progress tracking
 * 
 * @param {string} sectionId - The ID of the section to show
 */
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Show target section
    document.getElementById(sectionId).classList.add('active');
    
    // Update navigation highlighting
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
    
    // Update progress bar to reflect current position
    updateProgressBar(sectionId);
}

/**
 * Update the progress bar to reflect current form completion
 * Maps section IDs to percentage values for visual progress indication
 * 
 * @param {string} sectionId - The current section ID
 */
function updateProgressBar(sectionId) {
    const progressMap = {
        'basic-info': 20,
        'thesis-details': 40,
        'upload': 60,
        'supervisor': 80,
        'review': 100
    };
    
    const activeSection = document.querySelector('.section.active');
    const progressFill = activeSection.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = progressMap[sectionId] + '%';
    }
}

/**
 * Validate the current section's required fields
 * Provides visual feedback for validation errors
 * 
 * @returns {boolean} True if all required fields are valid
 */
function validateCurrentSection() {
    const activeSection = document.querySelector('.section.active');
    const requiredFields = activeSection.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            // Highlight invalid fields with red border
            field.style.borderColor = '#ff4444';
            field.focus();
            isValid = false;
            return false;
        } else {
            // Reset border color for valid fields
            field.style.borderColor = 'var(--light-gray)';
        }
    });
    
    return isValid;
}

/**
 * Event Listener Management
 * Sets up all interactive event handlers for the form
 */

/**
 * Initialize all event listeners for form interactions
 * Handles navigation, form submission, and real-time validation
 */
function initializeEventListeners() {
    // Navigation click handlers for section switching
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            showSection(sectionId);
        });
    });
    
    // Form submission handler with validation
    document.getElementById('thesisForm').addEventListener('submit', handleFormSubmission);
    
    // Real-time validation for all form inputs
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        // Validate on blur (when user leaves field)
        input.addEventListener('blur', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.style.borderColor = '#ff4444';
            } else {
                this.style.borderColor = 'var(--light-gray)';
            }
        });
        
        // Clear error styling when user starts typing
        input.addEventListener('input', function() {
            if (this.style.borderColor === 'rgb(255, 68, 68)' && this.value.trim()) {
                this.style.borderColor = 'var(--light-gray)';
            }
            // Update review section in real-time
            updateReviewSection();
        });
    });
}

/**
 * File Upload Management System
 * Handles file uploads with drag & drop, validation, and preview functionality
 */

/**
 * Setup all file upload functionality
 * Configures single file uploads, multiple file uploads, and drag & drop
 */
function setupFileUploads() {
    // Setup individual file upload types with size limits
    setupSingleFileUpload('thesisFile', 'thesisFileList', 50);        // 50MB limit
    setupSingleFileUpload('approvalSheet', 'approvalSheetList', 10);   // 10MB limit
    setupMultipleFileUpload('supportingFiles', 'supportingFilesList', 10); // 10MB per file
    
    // Setup drag and drop functionality for all file upload areas
    const fileUploads = document.querySelectorAll('.file-upload');
    fileUploads.forEach(upload => {
        // Handle drag over events - show visual feedback
        upload.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        // Handle drag leave events - remove visual feedback
        upload.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        
        // Handle file drop events - process dropped files
        upload.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            const fileInput = this.querySelector('input[type="file"]');
            fileInput.files = e.dataTransfer.files;
            handleFileSelection(fileInput);
        });
    });
}

/**
 * Setup single file upload with size validation
 * 
 * @param {string} inputId - ID of the file input element
 * @param {string} listId - ID of the file list container
 * @param {number} maxSizeMB - Maximum file size in megabytes
 */
function setupSingleFileUpload(inputId, listId, maxSizeMB) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    
    input.addEventListener('change', function() {
        handleFileSelection(this, listId, maxSizeMB, false);
    });
}

/**
 * Setup multiple file upload with size validation
 * 
 * @param {string} inputId - ID of the file input element
 * @param {string} listId - ID of the file list container
 * @param {number} maxSizeMB - Maximum file size per file in megabytes
 */
function setupMultipleFileUpload(inputId, listId, maxSizeMB) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    
    input.addEventListener('change', function() {
        handleFileSelection(this, listId, maxSizeMB, true);
    });
}

function handleFileSelection(input, listId, maxSizeMB, multiple) {
    const files = Array.from(input.files);
    const list = document.getElementById(listId);
    
    if (!multiple) {
        list.innerHTML = '';
    }
    
    files.forEach((file, index) => {
        if (file.size > maxSizeMB * 1024 * 1024) {
            showAlert(`File "${file.name}" is too large. Maximum size is ${maxSizeMB}MB.`, 'error');
            return;
        }
        
        const fileItem = createFileItem(file, input.id, index);
        list.appendChild(fileItem);
    });
}

function createFileItem(file, inputId, index) {
    const item = document.createElement('div');
    item.className = 'file-item';
    
    const fileExtension = file.name.split('.').pop().toUpperCase();
    const fileSize = formatFileSize(file.size);
    
    item.innerHTML = `
        <div class="file-info">
            <div class="file-icon">${fileExtension}</div>
            <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${fileSize}</div>
            </div>
        </div>
        <button type="button" class="remove-file" onclick="removeFile(this, '${inputId}', ${index})">×</button>
    `;
    
    return item;
}

function removeFile(button, inputId, index) {
    const input = document.getElementById(inputId);
    const fileItem = button.closest('.file-item');
    
    // Remove file from input (for single file uploads, clear the input)
    if (input.hasAttribute('multiple')) {
        const dt = new DataTransfer();
        const files = Array.from(input.files);
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        input.files = dt.files;
    } else {
        input.value = '';
    }
    
    fileItem.remove();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Academic structure management
function setupAcademicStructure() {
    // Initialize the academic structure dropdowns
    console.log('Setting up academic structure...');
}

function loadDepartments() {
    const academicLevelSelect = document.getElementById('academic_level');
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    
    if (!academicLevelSelect || !departmentSelect) return;
    
    const academicLevelId = academicLevelSelect.value;
    
    // Clear department and course dropdowns
    departmentSelect.innerHTML = '<option value="">Select Department</option>';
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    
    if (!academicLevelId) {
        departmentSelect.disabled = true;
        courseSelect.disabled = true;
        return;
    }
    
    // Enable department dropdown
    departmentSelect.disabled = false;
    courseSelect.disabled = true;
    
    // Fetch departments for the selected academic level
    fetch(`/api/departments/${academicLevelId}/`)
        .then(response => response.json())
        .then(data => {
            data.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                option.textContent = dept.name;
                departmentSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading departments:', error);
            // Fallback: populate with static data based on academic level
            populateDepartmentsFallback(academicLevelId);
        });
}

function loadCourses() {
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    
    if (!departmentSelect || !courseSelect) return;
    
    const departmentId = departmentSelect.value;
    
    // Clear course dropdown
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    
    if (!departmentId) {
        courseSelect.disabled = true;
        return;
    }
    
    // Enable course dropdown
    courseSelect.disabled = false;
    
    // Fetch courses for the selected department
    fetch(`/api/courses/${departmentId}/`)
        .then(response => response.json())
        .then(data => {
            data.courses.forEach(course => {
                const option = document.createElement('option');
                option.value = course.id;
                option.textContent = course.name;
                courseSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading courses:', error);
            // Fallback: populate with static data based on department
            populateCoursesFallback(departmentId);
        });
}

function populateDepartmentsFallback(academicLevelId) {
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    
    // Clear existing options
    departmentSelect.innerHTML = '<option value="">Select Department</option>';
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    
    // Static fallback data based on your academic structure
    const departments = {
        '1': [ // Undergraduate
            { id: 1, name: 'CICT - College of Information and Communication Technology' },
            { id: 2, name: 'CAS - College of Arts and Sciences' },
            { id: 3, name: 'CBM - College of Business Management' },
            { id: 4, name: 'CCJ - College of Criminal Justice' },
            { id: 5, name: 'CE - College of Education' },
            { id: 6, name: 'CHTM - College of Hospitality & Tourism Management' },
            { id: 7, name: 'CET - College of Engineering and Technology' }
        ],
        '2': [ // Graduate School
            { id: 8, name: 'Graduate School' }
        ]
    };
    
    const academicLevelDepartments = departments[academicLevelId] || [];
    academicLevelDepartments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept.id;
        option.textContent = dept.name;
        departmentSelect.appendChild(option);
    });
}

function populateCoursesFallback(departmentId) {
    const courseSelect = document.getElementById('course');
    
    // Clear existing options
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    
    // Static fallback data based on your academic structure
    const courses = {
        '1': [ // CICT
            { id: 1, name: 'Bachelor of Science in Computer Science' },
            { id: 2, name: 'Bachelor of Science in Information Systems' }
        ],
        '2': [ // CAS
            { id: 3, name: 'Bachelor of Science in Psychology' },
            { id: 4, name: 'Bachelor of Science in Public Administration' },
            { id: 5, name: 'Bachelor of Science in Social Work' }
        ],
        '3': [ // CBM
            { id: 6, name: 'Bachelor of Science in Business Administration' },
            { id: 7, name: 'Major in Human Resource Management' },
            { id: 8, name: 'Major in Marketing Management' },
            { id: 9, name: 'Bachelor of Science in Entrepreneurship' },
            { id: 10, name: 'Bachelor of Science in Office Administration' }
        ],
        '4': [ // CCJ
            { id: 11, name: 'Bachelor of Science in Criminology' }
        ],
        '5': [ // CE
            { id: 12, name: 'Bachelor in Elementary Education' },
            { id: 13, name: 'Bachelor of Secondary Education' },
            { id: 14, name: 'Major in English' },
            { id: 15, name: 'Major in Mathematics' },
            { id: 16, name: 'Major in Science' }
        ],
        '6': [ // CHTM
            { id: 17, name: 'Bachelor of Science in Hospitality Management' },
            { id: 18, name: 'Bachelor of Science in Tourism Management' }
        ],
        '7': [ // CET
            { id: 19, name: 'Bachelor of Science in Civil Engineering' },
            { id: 20, name: 'Bachelor of Science in Industrial Engineering' },
            { id: 21, name: 'Bachelor of Science in Mechanical Engineering' },
            { id: 22, name: 'Bachelor of Science in Industrial Technology' }
        ],
        '8': [ // Graduate School
            { id: 23, name: 'Master of Arts in Education major in Educational Management' },
            { id: 24, name: 'Master in Business Administration' },
            { id: 25, name: 'Master in Public Administration' },
            { id: 26, name: 'Master of Science in Criminal Justice' }
        ]
    };
    
    const departmentCourses = courses[departmentId] || [];
    departmentCourses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.id;
        option.textContent = course.name;
        courseSelect.appendChild(option);
    });
}

// Review section updates
function updateReviewSection() {
    const form = document.getElementById('thesisForm');
    const formData = new FormData(form);
    
    // Update summary fields
    document.getElementById('reviewStudentName').textContent = 
        `${formData.get('firstName') || ''} ${formData.get('lastName') || ''}`.trim() || '-';
    document.getElementById('reviewStudentId').textContent = formData.get('studentId') || '-';
    document.getElementById('reviewSubmitterEmail').textContent = formData.get('email') || '-';
    
    // Get display text for academic structure
    const academicLevelSelect = document.getElementById('academic_level');
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    
    const academicLevelText = academicLevelSelect ? academicLevelSelect.options[academicLevelSelect.selectedIndex]?.text || '-' : '-';
    const departmentText = departmentSelect ? departmentSelect.options[departmentSelect.selectedIndex]?.text || '-' : '-';
    const courseText = courseSelect ? courseSelect.options[courseSelect.selectedIndex]?.text || '-' : '-';
    
    document.getElementById('reviewAcademicLevel').textContent = academicLevelText;
    document.getElementById('reviewDepartment').textContent = departmentText;
    document.getElementById('reviewCourse').textContent = courseText;
    document.getElementById('reviewYear').textContent = formData.get('year') || '-';
    document.getElementById('reviewResearchCategory').textContent = formData.get('research_category') || '-';
    document.getElementById('reviewThesisTitle').textContent = formData.get('thesisTitle') || '-';
    document.getElementById('reviewAbstract').textContent = formData.get('abstract') || '-';
    document.getElementById('reviewKeywords').textContent = formData.get('keywords') || '-';
    document.getElementById('reviewSupervisor').textContent = formData.get('supervisorName') || '-';
    document.getElementById('reviewCoSupervisor').textContent = formData.get('coSupervisorName') || '-';
    document.getElementById('reviewExpectedCompletion').textContent = formData.get('expectedCompletion') || '-';

    // Collect co-authors information
    for (let i = 0; i < 3; i++) {
        const firstName = formData.get(`coworkers[${i}][first_name]`);
        const lastName = formData.get(`coworkers[${i}][last_name]`);
        const studentId = formData.get(`coworkers[${i}][student_id]`);
        const email = formData.get(`coworkers[${i}][email]`);
        
        const coworkerInfo = firstName || lastName || studentId || email 
            ? `${firstName || ''} ${lastName || ''} (ID: ${studentId || ''}, Email: ${email || ''})`
            : '-';
        
        document.getElementById(`reviewCoworker${i + 1}`).textContent = coworkerInfo;
    }
}

// Form submission
function handleFormSubmission(e) {
    e.preventDefault();
    
    const confirmCheckbox = document.getElementById('confirmSubmission');
    if (!confirmCheckbox.checked) {
        showAlert('Please confirm your submission by checking the confirmation box.', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    const form = document.getElementById('thesisForm');
    
    // Validate required fields before submission
    if (!validateForm()) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Thesis';
        return;
    }

    // Clear saved data before submission
    clearSavedData();
    
    // Submit the form normally - this will include the CSRF token
    form.submit();
}

// Validate all required fields
function validateForm() {
    const form = document.getElementById('thesisForm');
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#ff4444';
            field.focus();
            isValid = false;
            return false;
        } else {
            field.style.borderColor = 'var(--light-gray)';
        }
    });
    
    // Check if academic structure is selected
    const academicLevel = document.getElementById('academic_level').value;
    const department = document.getElementById('department').value;
    const course = document.getElementById('course').value;
    
    if (!academicLevel || !department || !course) {
        showAlert('Please select Academic Level, Department, and Course/Program.', 'error');
        isValid = false;
    }
    
    // Check if files are uploaded
    const thesisFile = document.getElementById('thesisFile').files[0];
    const approvalSheet = document.getElementById('approvalSheet').files[0];
    
    if (!thesisFile) {
        showAlert('Please upload your thesis document.', 'error');
        isValid = false;
    }
    
    if (!approvalSheet) {
        showAlert('Please upload your approval sheet.', 'error');
        isValid = false;
    }
    
    return isValid;
}

// Auto-save functionality
function setupAutoSave() {
    const form = document.getElementById('thesisForm');
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            saveFormData();
        });
        
        input.addEventListener('change', function() {
            saveFormData();
        });
    });
    
    // Auto-save every 30 seconds
    setInterval(saveFormData, 30000);
}

function saveFormData() {
    const form = document.getElementById('thesisForm');
    const formData = new FormData(form);
    const data = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        if (data[key]) {
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }
    
    // Save to localStorage
    localStorage.setItem('thesisFormData', JSON.stringify(data));
    localStorage.setItem('thesisFormLastSaved', new Date().toISOString());
    
    // Update save indicator
    updateSaveIndicator(true);
}

function loadSavedData() {
    const savedData = localStorage.getItem('thesisFormData');
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            const form = document.getElementById('thesisForm');
            
            // Restore form data
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = data[key] === 'on' || data[key] === true;
                    } else if (input.type === 'file') {
                        // Skip file inputs as they can't be restored
                    } else {
                        input.value = data[key];
                    }
                }
            });
            
            // Update review section
            updateReviewSection();
            
            // Show restore notification
            showAlert('Previous form data has been restored.', 'info');
        } catch (error) {
            console.error('Error loading saved data:', error);
        }
    }
}

function updateSaveIndicator(saved = false) {
    const metaChip = document.querySelector('.meta-chip .dot.success');
    if (metaChip) {
        if (saved) {
            metaChip.style.backgroundColor = '#28a745';
            metaChip.title = 'Last saved: ' + new Date().toLocaleTimeString();
        } else {
            metaChip.style.backgroundColor = '#ffc107';
            metaChip.title = 'Unsaved changes';
        }
    }
}

function clearSavedData() {
    localStorage.removeItem('thesisFormData');
    localStorage.removeItem('thesisFormLastSaved');
}

// Utility functions
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => {
        if (!alert.classList.contains('alert-info')) {
            alert.remove();
        }
    });
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    const activeSection = document.querySelector('.section.active');
    activeSection.insertBefore(alert, activeSection.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}