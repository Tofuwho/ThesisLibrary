/**
 * Submission Portal JavaScript Module
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
 * Initialize submission portal functionality when DOM is loaded
 * Sets up all form interactions, file uploads, and auto-save features
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    setupFileUploads();
    setupAutoSave();
    loadSavedData();
    autofillUserData(); // Autofill after loading saved data (saved data takes precedence)
    setupAcademicStructure();
    setupCoAuthorManagement(); // new
});

/* ---------------------------
   --- Co-author management ---
   --------------------------- */

function setupCoAuthorManagement() {
    const coauthorsContainer = document.getElementById('coauthors') || document.getElementById('coworkers');
    const addBtn = document.getElementById('addCoAuthorBtn') || document.getElementById('addCoworkerBtn');

    if (!coauthorsContainer || !addBtn) return;

    addBtn.addEventListener('click', () => {
        // Instead of using a global counter, calculate based on existing blocks
        const nextIndex = coauthorsContainer.querySelectorAll('.coauthor-block, .coworker-block').length;
        createCoauthorBlock(coauthorsContainer, nextIndex, {});
        reindexCoauthors(coauthorsContainer); // ensures numbering stays continuous
    });
}


/**
 * Create a co-author block and append it to container.
 * index: integer (used for name/id) - the function will not renumber existing blocks.
 * values: optional object { first_name, last_name, student_id, email }
 */
function createCoauthorBlock(container, index, values = {}) {
    const block = document.createElement('div');
    block.className = 'coauthor-block';
    block.setAttribute('data-index', index);

    // Use data-field attributes to make reindexing easy
    block.innerHTML = `
        <h4>Co-Author ${index + 1}</h4>
        <div class="form-row">
            <div class="form-group">
                <label for="coauthor${index}_first_name">First Name</label>
                <input data-field="first_name" type="text" id="coauthor${index}_first_name"
                       name="coauthors[${index}][first_name]" placeholder="First Name" value="${escapeHtml(values.first_name || '')}">
            </div>
            <div class="form-group">
                <label for="coauthor${index}_last_name">Last Name</label>
                <input data-field="last_name" type="text" id="coauthor${index}_last_name"
                       name="coauthors[${index}][last_name]" placeholder="Last Name" value="${escapeHtml(values.last_name || '')}">
            </div>
            <div class="form-group">
                <label for="coauthor${index}_student_id">Co-Author Student ID</label>
                <input data-field="student_id" type="text" id="coauthor${index}_student_id"
                       name="coauthors[${index}][student_id]" placeholder="Student ID" value="${escapeHtml(values.student_id || '')}">
            </div>
            <div class="form-group">
                <label for="coauthor${index}_email">Email</label>
                <input data-field="email" type="email" id="coauthor${index}_email"
                       name="coauthors[${index}][email]" placeholder="Email" value="${escapeHtml(values.email || '')}">
            </div>
        </div>
        <div class="form-actions-inline">
            <button type="button" class="btn btn-danger removeCoauthorBtn">Remove</button>
        </div>
        <hr>
    `;

    // Append
    container.appendChild(block);

    // Wire up remove button
    const removeBtn = block.querySelector('.removeCoauthorBtn');
    removeBtn.addEventListener('click', () => {
        block.remove();
        reindexCoauthors(container);
        updateReviewSection();
        saveFormData();
    });

    // Attach input/blur listeners for these inputs (dynamic)
    block.querySelectorAll('input, textarea, select').forEach(inp => {
        inp.addEventListener('input', () => {
            // clear inline error if corrected
            clearFieldError(inp);
            updateReviewSection();
            saveFormData();
        });
        inp.addEventListener('blur', () => {
            // show immediate feedback on blur for empty required-like co-author logic handled on validate
            if (inp.type === 'email' && inp.value.trim()) {
                // quick format check
                if (!/^[\w.%+-]+@gmail\.com$/i.test(inp.value.trim())) {
                    showFieldError(inp, 'Please enter a valid Gmail address.');
                }
            }
        });
    });
}

/**
 * After remove, reindex blocks so names/ids remain sequential: coauthors[0], coauthors[1], ...
 */
function reindexCoauthors(container) {
    const blocks = Array.from(container.querySelectorAll('.coauthor-block'));
    blocks.forEach((block, newIndex) => {
        block.setAttribute('data-index', newIndex);
        // update header
        const h4 = block.querySelector('h4');
        if (h4) h4.textContent = `Co-Author ${newIndex + 1}`;

        // update each input and its label inside this block
        block.querySelectorAll('[data-field]').forEach(input => {
            const field = input.getAttribute('data-field');
            const newId = `coauthor${newIndex}_${field}`;
            input.id = newId;
            input.name = `coauthors[${newIndex}][${field}]`;

            // set label.for within the same .form-group
            const group = input.closest('.form-group');
            if (group) {
                const label = group.querySelector('label');
                if (label) label.htmlFor = newId;
            }
        });
    });
}

/* ---------------------------
   --- Shared helpers -------
   --------------------------- */

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function showFieldError(field, message) {
    if (!field) return;
    const errorId = (field.id || field.name || Math.random()).replace(/[^a-z0-9_\-]/gi, '') + '-error';
    let err = document.getElementById(errorId);
    if (!err) {
        err = document.createElement('div');
        err.id = errorId;
        err.className = 'error-message';
        err.style.color = '#ff4444';
        err.style.fontSize = '0.9em';
        err.style.marginTop = '4px';
        field.insertAdjacentElement('afterend', err);
    }
    field.style.borderColor = '#ff4444';
    err.textContent = message;
}

function clearFieldError(field) {
    if (!field) return;
    const errorId = (field.id || field.name || '').replace(/[^a-z0-9_\-]/gi, '') + '-error';
    const err = document.getElementById(errorId);
    if (err) err.remove();
    field.style.borderColor = 'var(--light-gray)';
}

/* ---------------------------
   --- Navigation / Sections -
   --------------------------- */

function nextSection(sectionId) {
    if (validateCurrentSection()) {
        showSection(sectionId);
        updateReviewSection();
    }
}

function previousSection(sectionId) {
    showSection(sectionId);
}

function showSection(sectionId) {
    if (!sectionId) return;
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));
    const target = document.getElementById(sectionId);
    if (!target) return;
    target.classList.add('active');

    // nav highlighting
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(i => i.classList.remove('active'));
    const myNav = document.querySelector(`[data-section="${sectionId}"]`);
    if (myNav) myNav.classList.add('active');

    updateProgressBar(sectionId);
}

/* progress bar unchanged */
function updateProgressBar(sectionId) {
    const progressMap = {
        'basic-info': 20,
        'upload': 40,
        'supervisor': 60,
        'thesis-details': 80,
        'review': 100
    };
    const activeSection = document.querySelector('.section.active');
    const progressFill = activeSection && activeSection.querySelector('.progress-fill');
    if (progressFill && progressMap[sectionId] !== undefined) {
        progressFill.style.width = progressMap[sectionId] + '%';
    }
}

/* ---------------------------
   --- Validation -----------
   --------------------------- */

/**
 * Validates the section element.
 * If showErrors === true, will display errors and set borders. Otherwise runs silently.
 * Returns true if section valid.
 */
function validateSection(sectionEl, showErrors = true) {
    if (!sectionEl) return true;
    let valid = true;
    const saveLightGray = 'var(--light-gray)';

    // Required fields inside the section (skip disabled/hidden)
    const requiredFields = Array.from(sectionEl.querySelectorAll('[required]')).filter(f => !f.disabled && isElementVisible(f));
    for (let field of requiredFields) {
        // Skip validation for elements that are hidden / disabled
        let isEmpty = false;

        if (field.type === 'file') {
            isEmpty = !(field.files && field.files.length > 0);
        } else {
            const val = (field.value || '').trim();
            isEmpty = (val === '');
        }

        if (isEmpty) {
            valid = false;
            if (showErrors) {
                showFieldError(field, 'This field is required.');
                // focus first invalid
                if (sectionEl.classList.contains('active')) {
                    try { field.focus(); } catch (e) {}
                }
            }
        } else {
            // valid for this field -> clear any existing error
            if (showErrors) clearFieldError(field);
        }

        // email extra check
        if (!isEmpty && field.type === 'email') {
            const val = field.value.trim();
            if (val && !/^[\w.%+-]+@gmail\.com$/i.test(val)) {
                valid = false;
                if (showErrors) showFieldError(field, 'Please enter a valid Gmail address.');
            } else if (showErrors) {
                // clear email error if it exists and now correct
                clearFieldError(field);
            }
        }
    }

    // Co-authors validation (if this section contains coauthors container)
    const coauthorsContainer = sectionEl.querySelector('#coauthors') || sectionEl.querySelector('#coworkers');
    if (coauthorsContainer) {
        const blocks = Array.from(coauthorsContainer.querySelectorAll('.coauthor-block, .coworker-block'));
        blocks.forEach(block => {
            // use block dataset index or compute
            let index = block.getAttribute('data-index');
            // Collect inputs inside block by data-field
            const firstName = block.querySelector('[data-field="first_name"]');
            const lastName  = block.querySelector('[data-field="last_name"]');
            const studentId = block.querySelector('[data-field="student_id"]');
            const email     = block.querySelector('[data-field="email"]');

            const values = {
                firstName: firstName?.value.trim() || '',
                lastName: lastName?.value.trim() || '',
                studentId: studentId?.value.trim() || '',
                email: email?.value.trim() || ''
            };

            const anyFilled = values.firstName || values.lastName || values.studentId || values.email;

            if (anyFilled) {
                // all fields become required
                if (!values.firstName) {
                    valid = false;
                    if (showErrors) showFieldError(firstName, 'First name is required when adding a co-author.');
                } else if (showErrors) clearFieldError(firstName);

                if (!values.lastName) {
                    valid = false;
                    if (showErrors) showFieldError(lastName, 'Last name is required when adding a co-author.');
                } else if (showErrors) clearFieldError(lastName);

                if (!values.studentId) {
                    valid = false;
                    if (showErrors) showFieldError(studentId, 'Student ID is required when adding a co-author.');
                } else if (showErrors) clearFieldError(studentId);

                if (!values.email) {
                    valid = false;
                    if (showErrors) showFieldError(email, 'Email is required when adding a co-author.');
                } else if (values.email && !/^[\w.%+-]+@gmail\.com$/i.test(values.email)) {
                    valid = false;
                    if (showErrors) showFieldError(email, 'Please enter a valid Gmail address for co-author.');
                } else if (showErrors) clearFieldError(email);
            } else {
                // If nothing filled in this coauthor block, clear any previous errors
                if (showErrors) {
                    [firstName, lastName, studentId, email].forEach(clearFieldError);
                }
            }
        });
    }

    return valid;
}

/**
 * Helper to determine if an element is visible (not display:none and in DOM)
 */
function isElementVisible(el) {
    if (!el) return false;
    // offsetParent covers most cases (not visible if display:none)
    return !!(el.offsetParent !== null);
}

/**
 * Validate current active section (legacy wrapper)
 */
function validateCurrentSection() {
    const activeSection = document.querySelector('.section.active');
    return validateSection(activeSection, true);
}

/* ---------------------------
   --- Event listeners ------
   --------------------------- */

function initializeEventListeners() {
    const navItems = document.querySelectorAll('.nav-item');
    const sectionOrder = ["basic-info", "upload", "supervisor", "thesis-details", "review"];

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const sectionId = this.getAttribute('data-section');
            if (!sectionId) return;
            const currentSectionEl = document.querySelector('.section.active');
            const currentIndex = sectionOrder.indexOf(currentSectionEl?.id);
            const targetIndex = sectionOrder.indexOf(sectionId);

            // If going forward, ensure all earlier sections (0..targetIndex-1) are valid.
            if (targetIndex > currentIndex) {
                for (let i = 0; i < targetIndex; i++) {
                    const secId = sectionOrder[i];
                    const secEl = document.getElementById(secId);
                    if (!validateSection(secEl, false)) {
                        // show the first invalid section and show errors
                        showSection(secId);
                        validateSection(secEl, true);
                        showAlert('Please fix the errors before proceeding.', 'error');
                        e.preventDefault();
                        return;
                    }
                }
            }

            // going backwards or all required sections ok
            showSection(sectionId);
        });
    });

    // Form submit
    const form = document.getElementById('thesisForm');
    if (form) form.addEventListener('submit', handleFormSubmission);

    // Real-time validation for static inputs
    document.querySelectorAll('input, textarea, select').forEach(input => {
        // Skip if dynamically added later — they have own listeners
        input.addEventListener('blur', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.style.borderColor = '#ff4444';
            } else {
                this.style.borderColor = 'var(--light-gray)';
            }
        });

        input.addEventListener('input', function() {
            if (this.style.borderColor === 'rgb(255, 68, 68)' && this.value.trim()) {
                this.style.borderColor = 'var(--light-gray)';
            }
            updateReviewSection();
        });
    });
}

/* ---------------------------
   --- File uploads (unchanged logic, minor safety) ---
   --------------------------- */

function setupFileUploads() {
    setupSingleFileUpload('thesisFile', 'thesisFileList', 50);
    setupSingleFileUpload('approvalSheet', 'approvalSheetList', 10);
    setupMultipleFileUpload('supportingFiles', 'supportingFilesList', 10);

    const fileUploads = document.querySelectorAll('.file-upload');
    fileUploads.forEach(upload => {
        upload.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        upload.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        upload.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            const fileInput = this.querySelector('input[type="file"]');
            if (!fileInput) return;
            fileInput.files = e.dataTransfer.files;
            handleFileSelection(fileInput);
            
            // Auto-extract abstract if this is the thesis file upload
            if (fileInput.id === 'thesisFile' && fileInput.files && fileInput.files.length > 0) {
                extractAbstractFromPDF(fileInput.files[0]);
            }
        });
    });
}

function setupSingleFileUpload(inputId, listId, maxSizeMB) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('change', function() {
        handleFileSelection(this, listId, maxSizeMB, false);
        
        // Auto-extract abstract if this is the thesis file upload
        if (inputId === 'thesisFile' && this.files && this.files.length > 0) {
            extractAbstractFromPDF(this.files[0]);
        }
    });
}
function setupMultipleFileUpload(inputId, listId, maxSizeMB) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('change', function() {
        handleFileSelection(this, listId, maxSizeMB, true);
    });
}
function handleFileSelection(input, listId, maxSizeMB, multiple) {
    if (!input) return;
    const files = Array.from(input.files || []);
    const list = document.getElementById(listId);
    if (!list) return;
    if (!multiple) list.innerHTML = '';

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
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-size">${fileSize}</div>
            </div>
        </div>
        <button type="button" class="remove-file">×</button>
    `;
    // wire remove
    item.querySelector('.remove-file').addEventListener('click', () => {
        removeFileElement(item, inputId, index);
    });
    return item;
}
function removeFileElement(fileItem, inputId, index) {
    const input = document.getElementById(inputId);
    if (!input) {
        fileItem.remove();
        return;
    }
    if (input.hasAttribute('multiple')) {
        const dt = new DataTransfer();
        const files = Array.from(input.files || []);
        files.forEach((file, i) => {
            if (i !== index) dt.items.add(file);
        });
        input.files = dt.files;
    } else {
        input.value = '';
    }
    fileItem.remove();
}
function removeFile(button, inputId, index) { removeFileElement(button.closest('.file-item'), inputId, index); }
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Extract abstract from uploaded PDF file
 * @param {File} pdfFile - The PDF file to extract abstract from
 */
function extractAbstractFromPDF(pdfFile) {
    const abstractTextarea = document.getElementById('abstract');
    if (!abstractTextarea) return;
    
    // Show loading indicator
    const originalPlaceholder = abstractTextarea.placeholder;
    abstractTextarea.placeholder = 'Extracting abstract from PDF...';
    abstractTextarea.disabled = true;
    
    // Create FormData to send the file
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    
    // Get CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // Make API call to extract abstract
    fetch('/api/extract-abstract/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        abstractTextarea.disabled = false;
        abstractTextarea.placeholder = originalPlaceholder;
        
        if (data.success) {
            let successMessages = [];
            
            // Populate title field if extracted
            if (data.title) {
                const titleInput = document.getElementById('thesisTitle');
                if (titleInput && !titleInput.value.trim()) {
                    titleInput.value = data.title;
                    successMessages.push('Title extracted');
                }
            }
            
            // Populate abstract field with extracted text
            if (data.abstract) {
                abstractTextarea.value = data.abstract;
                const wordCount = data.word_count || data.abstract.split(/\s+/).length;
                successMessages.push(`Abstract extracted (${wordCount} words)`);
            }
            
            // Show success message
            if (successMessages.length > 0) {
                showAlert(successMessages.join(' and ') + ' successfully!', 'success');
            } else {
                showAlert('Extraction completed, but no title or abstract found. Please enter them manually.', 'info');
            }
            
            // Update review section if visible
            updateReviewSection();
        } else {
            // Show info message if extraction failed
            const message = data.message || 'Could not automatically extract abstract or title. Please enter them manually.';
            showAlert(message, 'info');
        }
    })
    .catch(error => {
        console.error('Error extracting abstract:', error);
        abstractTextarea.disabled = false;
        abstractTextarea.placeholder = originalPlaceholder;
        showAlert('Error extracting abstract. Please enter it manually.', 'error');
    });
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string} Cookie value
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ---------------------------
   --- Academic structure (unchanged)
   --------------------------- */

function setupAcademicStructure() { /* existing logic left intact */ }

function loadDepartments() {
    const academicLevelSelect = document.getElementById('academic_level');
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    if (!academicLevelSelect || !departmentSelect) return;
    const academicLevelId = academicLevelSelect.value;
    departmentSelect.innerHTML = '<option value="">Select Department</option>';
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    if (!academicLevelId) { departmentSelect.disabled = true; courseSelect.disabled = true; return; }
    departmentSelect.disabled = false; courseSelect.disabled = true;
    fetch(`/api/departments/${academicLevelId}/`)
        .then(r => r.json())
        .then(data => {
            (data.departments || []).forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id; option.textContent = dept.name; departmentSelect.appendChild(option);
            });
        }).catch(e => { console.error('Error loading departments:', e); populateDepartmentsFallback(academicLevelId); });
}
function loadCourses() {
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    if (!departmentSelect || !courseSelect) return;
    const departmentId = departmentSelect.value;
    courseSelect.innerHTML = '<option value="">Select Course</option>';
    if (!departmentId) { courseSelect.disabled = true; return; }
    courseSelect.disabled = false;
    fetch(`/api/courses/${departmentId}/`)
        .then(r => r.json())
        .then(data => {
            (data.courses || []).forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.name; courseSelect.appendChild(o); });
        })
        .catch(e => { console.error('Error loading courses:', e); populateCoursesFallback(departmentId); });
}
function populateDepartmentsFallback(academicLevelId) { /* same as before */ }
function populateCoursesFallback(departmentId) { /* same as before */ }

/* ---------------------------
   --- Review / save / load -
   --------------------------- */

function updateReviewSection() {
    const form = document.getElementById('thesisForm');
    if (!form) return;
    const formData = new FormData(form);

    document.getElementById('reviewStudentName').textContent =
        `${formData.get('firstName') || ''} ${formData.get('lastName') || ''}`.trim() || '-';
    document.getElementById('reviewStudentId').textContent = formData.get('studentId') || '-';
    document.getElementById('reviewSubmitterEmail').textContent = formData.get('email') || '-';

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
    document.getElementById('reviewThesisTitle').textContent = formData.get('thesisTitle') || '-';
    document.getElementById('reviewAbstract').textContent = formData.get('abstract') || '-';
    document.getElementById('reviewKeywords').textContent = formData.get('keywords') || '-';
    document.getElementById('reviewSupervisor').textContent = formData.get('supervisorName') || '-';
    document.getElementById('reviewCoSupervisor').textContent = formData.get('coSupervisorName') || '-';

    // Co-authors: prefer dynamic list container (#reviewCoAuthors). If not present, fill up to 3 fallback slots.
    const reviewList = document.getElementById('reviewCoAuthors');
    const coauthorsContainer = document.getElementById('coauthors') || document.getElementById('coworkers');
    const blocks = coauthorsContainer ? Array.from(coauthorsContainer.querySelectorAll('.coauthor-block, .coworker-block')) : [];

    if (reviewList) {
        reviewList.innerHTML = '';
        blocks.forEach((block, i) => {
            const first = block.querySelector('[data-field="first_name"]')?.value || '';
            const last  = block.querySelector('[data-field="last_name"]')?.value || '';
            const sid   = block.querySelector('[data-field="student_id"]')?.value || '';
            const email = block.querySelector('[data-field="email"]')?.value || '';
            if (first || last || sid || email) {
                const li = document.createElement('li');
                li.textContent = `${i + 1}. ${first} ${last} (ID: ${sid || '-'}, Email: ${email || '-'})`;
                reviewList.appendChild(li);
            }
        });
    } else {
        // fallback to old reviewCoworker1/2/3 if present
        for (let i = 0; i < 3; i++) {
            const span = document.getElementById(`reviewCoworker${i + 1}`);
            if (!span) continue;
            const block = blocks[i];
            if (!block) { span.textContent = '-'; continue; }
            const first = block.querySelector('[data-field="first_name"]')?.value || '';
            const last  = block.querySelector('[data-field="last_name"]')?.value || '';
            const sid   = block.querySelector('[data-field="student_id"]')?.value || '';
            const email = block.querySelector('[data-field="email"]')?.value || '';
            span.textContent = (first || last || sid || email) ? `${first} ${last} (ID: ${sid || ''}, Email: ${email || ''})` : '-';
        }
    }
}

/* ---------------------------
   --- Form submission & top-level validation
   --------------------------- */

function handleFormSubmission(e) {
    e.preventDefault();
    const confirmCheckbox = document.getElementById('confirmSubmission');
    if (!confirmCheckbox || !confirmCheckbox.checked) {
        showAlert('Please confirm your submission by checking the confirmation box.', 'error');
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
    }

    // Full validation across all sections
    if (!validateForm()) {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Thesis';
        }
        return;
    }

    clearSavedData();
    const form = document.getElementById('thesisForm');
    if (form) form.submit();
}

function validateForm() {
    const sectionOrder = ["basic-info", "upload", "supervisor", "thesis-details", "review"];
    let allValid = true;
    for (let i = 0; i < sectionOrder.length; i++) {
        const sec = document.getElementById(sectionOrder[i]);
        if (!validateSection(sec, true)) {
            // show first invalid section
            showSection(sectionOrder[i]);
            allValid = false;
            break;
        }
    }

    // Additional checks (files, academic selection) are covered by the per-section required attributes
    // but keep extra checks if there are edge cases:

    // Check academic structure explicitly (if those fields somehow not present in required)
    const academicLevel = document.getElementById('academic_level')?.value || '';
    const department = document.getElementById('department')?.value || '';
    const course = document.getElementById('course')?.value || '';
    if (!academicLevel || !department || !course) {
        showAlert('Please select Academic Level, Department, and Course/Program.', 'error');
        allValid = false;
    }

    // Files
    const thesisFile = document.getElementById('thesisFile')?.files?.[0];
    const approvalSheet = document.getElementById('approvalSheet')?.files?.[0];
    if (!thesisFile) { showAlert('Please upload your thesis document.', 'error'); allValid = false; }
    if (!approvalSheet) { showAlert('Please upload your approval sheet.', 'error'); allValid = false; }

    return allValid;
}

/* ---------------------------
   --- Autofill user data ---
   --------------------------- */

/**
 * Autofill form fields with logged-in user's data
 * Only fills fields that are empty (so saved data takes precedence)
 */
function autofillUserData() {
    // Check if USER_DATA is available (defined in template)
    if (typeof USER_DATA === 'undefined') return;
    
    const firstNameField = document.getElementById('firstName');
    const lastNameField = document.getElementById('lastName');
    const emailField = document.getElementById('email');
    const studentIdField = document.getElementById('studentId');
    
    // Only autofill if field is empty (preserve any saved or manually entered data)
    if (firstNameField && !firstNameField.value.trim() && USER_DATA.firstName) {
        firstNameField.value = USER_DATA.firstName;
    }
    
    if (lastNameField && !lastNameField.value.trim() && USER_DATA.lastName) {
        lastNameField.value = USER_DATA.lastName;
    }
    
    if (emailField && !emailField.value.trim() && USER_DATA.email) {
        emailField.value = USER_DATA.email;
    }
    
    if (studentIdField && !studentIdField.value.trim() && USER_DATA.studentId) {
        studentIdField.value = USER_DATA.studentId;
    }
    
    // Update review section if any fields were filled
    if ((firstNameField && firstNameField.value) || 
        (lastNameField && lastNameField.value) || 
        (emailField && emailField.value) || 
        (studentIdField && studentIdField.value)) {
        updateReviewSection();
    }
}

/* ---------------------------
   --- Auto-save / load -----
   --------------------------- */

function setupAutoSave() {
    const form = document.getElementById('thesisForm');
    if (!form) return;
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('input', saveFormData);
        input.addEventListener('change', saveFormData);
    });
    // Auto-save every 30s
    setInterval(saveFormData, 30000);
}

function saveFormData() {
    const form = document.getElementById('thesisForm');
    if (!form) return;
    const fd = new FormData(form);
    const data = {};
    for (let [key, value] of fd.entries()) {
        if (data[key]) {
            if (Array.isArray(data[key])) data[key].push(value);
            else data[key] = [data[key], value];
        } else {
            data[key] = value;
        }
    }
    localStorage.setItem('thesisFormData', JSON.stringify(data));
    localStorage.setItem('thesisFormLastSaved', new Date().toISOString());
    updateSaveIndicator(true);
}

function loadSavedData() {
    const savedData = localStorage.getItem('thesisFormData');
    if (!savedData) return;
    try {
        const data = JSON.parse(savedData);
        const form = document.getElementById('thesisForm');
        if (!form) return;

        // First: gather coauthor keys and rebuild dynamic blocks
        const coauthorKeys = Object.keys(data).filter(k => /^(coauthors|coworkers)\[\d+\]\[(first_name|last_name|student_id|email)\]$/.test(k));
        if (coauthorKeys.length > 0) {
            // group by index
            const groups = {};
            coauthorKeys.forEach(k => {
                const m = k.match(/^(?:coauthors|coworkers)\[(\d+)\]\[(.+)\]$/);
                if (!m) return;
                const idx = parseInt(m[1], 10);
                const field = m[2];
                groups[idx] = groups[idx] || {};
                groups[idx][field] = data[k];
            });

            // create blocks in sorted order (and reindex to sequential)
            const container = document.getElementById('coauthors') || document.getElementById('coworkers');
            if (container) {
                // remove existing dynamic blocks first
                container.innerHTML = '';
                const sortedIndexes = Object.keys(groups).map(x => parseInt(x, 10)).sort((a, b) => a - b);
                sortedIndexes.forEach((origIdx, newIndex) => {
                    createCoauthorBlock(container, newIndex, groups[origIdx]);
                });
                // Reindex to ensure sequential names (createCoauthorBlock uses the newIndex we passed)
            }
        }

        // Then restore other inputs
        Object.keys(data).forEach(key => {
            // Skip coauthors keys handled above
            if (/^(coauthors|coworkers)\[\d+\]\[(first_name|last_name|student_id|email)\]$/.test(key)) return;

            const input = form.querySelector(`[name="${key}"]`);
            if (!input) return;
            if (input.type === 'checkbox') {
                input.checked = data[key] === 'on' || data[key] === true;
            } else if (input.type === 'file') {
                // cannot restore file inputs
            } else {
                input.value = data[key];
            }
        });

        updateReviewSection();
        showAlert('Previous form data has been restored.', 'info');
    } catch (error) {
        console.error('Error loading saved data:', error);
    }
}

function updateSaveIndicator(saved = false) {
    const metaChip = document.querySelector('.meta-chip .dot.success');
    if (!metaChip) return;
    if (saved) {
        metaChip.style.backgroundColor = '#28a745';
        metaChip.title = 'Last saved: ' + new Date().toLocaleTimeString();
    } else {
        metaChip.style.backgroundColor = '#ffc107';
        metaChip.title = 'Unsaved changes';
    }
}

function clearSavedData() {
    localStorage.removeItem('thesisFormData');
    localStorage.removeItem('thesisFormLastSaved');
}

/* ---------------------------
   --- Utilities -----------
   --------------------------- */

function showAlert(message, type) {
    // remove non-info alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => {
        if (!alert.classList.contains('alert-info')) alert.remove();
    });
    const activeSection = document.querySelector('.section.active') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    activeSection.insertBefore(alert, activeSection.firstChild);
    setTimeout(() => { alert.remove(); }, 5000);
}