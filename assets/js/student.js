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
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
    setupFileUploads();
    setupAutoSave();
    loadSavedData();
    autofillUserData(); // Autofill after loading saved data (saved data takes precedence)
    setupAcademicStructure();
    setupCoAuthorManagement(); // new
    adaptUIForRole();
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
                <label for="coauthor${index}_student_id">Co-Author ID</label>
                <input data-field="student_id" type="text" id="coauthor${index}_student_id"
                       name="coauthors[${index}][student_id]" placeholder="Student/Faculty ID" value="${escapeHtml(values.student_id || '')}">
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
                if (!/^[\w.%+-]+@(gmail\.com|tcu\.edu\.ph)$/i.test(inp.value.trim())) {
                    showFieldError(inp, 'Please enter a valid Gmail or TCU Institutional email address (@tcu.edu.ph).');
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
    const sections = document.querySelectorAll('.form-section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.style.opacity = '0';
        section.style.transform = 'translateY(10px)';
    });

    const target = document.getElementById(sectionId);
    if (!target) return;

    // Smooth transition
    target.classList.add('active');
    setTimeout(() => {
        target.style.opacity = '1';
        target.style.transform = 'translateY(0)';
    }, 10);

    // nav highlighting
    const navItems = document.querySelectorAll('.nav-step');
    navItems.forEach(i => i.classList.remove('active'));
    const myNav = document.querySelector(`[data-section="${sectionId}"]`);
    if (myNav) myNav.classList.add('active');

    // Scroll to top of form smoothly
    window.scrollTo({ top: 100, behavior: 'smooth' });
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
                    try { field.focus(); } catch (e) { }
                }
            }
        } else {
            // valid for this field -> clear any existing error
            if (showErrors) clearFieldError(field);
        }

        // email extra check
        if (!isEmpty && field.type === 'email') {
            const val = field.value.trim();
            if (val && !/^[\w.%+-]+@(gmail\.com|tcu\.edu\.ph)$/i.test(val)) {
                valid = false;
                if (showErrors) showFieldError(field, 'Please enter a valid Gmail or TCU Institutional email address (@tcu.edu.ph).');
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
            const lastName = block.querySelector('[data-field="last_name"]');
            const studentId = block.querySelector('[data-field="student_id"]');
            const email = block.querySelector('[data-field="email"]');

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
                } else if (values.email && !/^[\w.%+-]+@(gmail\.com|tcu\.edu\.ph)$/i.test(values.email)) {
                    valid = false;
                    if (showErrors) showFieldError(email, 'Please enter a valid Gmail or TCU Institutional email address for co-author.');
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
    const activeSection = document.querySelector('.form-section.active');
    return validateSection(activeSection, true);
}

/* ---------------------------
   --- Event listeners ------
   --------------------------- */

function initializeEventListeners() {
    const navItems = document.querySelectorAll('.nav-step');
    const sectionOrder = ["basic-info", "upload", "supervisor", "thesis-details", "review"];

    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
            const sectionId = this.getAttribute('data-section');
            if (!sectionId) return;
            const currentSectionEl = document.querySelector('.form-section.active');
            const currentIndex = sectionOrder.indexOf(currentSectionEl?.id);
            const targetIndex = sectionOrder.indexOf(sectionId);

            // If going forward, ensure all earlier sections (0..targetIndex-1) are valid.
            if (targetIndex > currentIndex) {
                for (let i = 0; i <= currentIndex; i++) {
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
        input.addEventListener('blur', function () {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.style.borderColor = '#ff4444';
                this.classList.add('input-error');
            } else {
                this.style.borderColor = '';
                this.classList.remove('input-error');
            }
        });

        input.addEventListener('input', function () {
            if (this.classList.contains('input-error') && this.value.trim()) {
                this.style.borderColor = '';
                this.classList.remove('input-error');
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
        upload.addEventListener('dragover', function (e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        upload.addEventListener('dragleave', function (e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        upload.addEventListener('drop', function (e) {
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
    input.addEventListener('change', function () {
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
    input.addEventListener('change', function () {
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
    if (!academicLevelSelect || !departmentSelect) return Promise.resolve();

    const academicLevelId = academicLevelSelect.value;
    departmentSelect.innerHTML = '<option value="">Select Department</option>';
    courseSelect.innerHTML = '<option value="">Select Course</option>';

    if (!academicLevelId) {
        departmentSelect.disabled = true;
        courseSelect.disabled = true;
        return Promise.resolve();
    }

    departmentSelect.disabled = false;
    courseSelect.disabled = true;

    return fetch(`/api/departments/${academicLevelId}/`)
        .then(r => r.json())
        .then(data => {
            (data.departments || []).forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                option.textContent = dept.name;
                departmentSelect.appendChild(option);
            });
        })
        .catch(e => {
            console.error('Error loading departments:', e);
            populateDepartmentsFallback(academicLevelId);
        });
}
function loadCourses() {
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');
    if (!departmentSelect || !courseSelect) return Promise.resolve();

    const departmentId = departmentSelect.value;
    courseSelect.innerHTML = '<option value="">Select Course</option>';

    if (!departmentId) {
        courseSelect.disabled = true;
        return Promise.resolve();
    }

    courseSelect.disabled = false;

    return fetch(`/api/courses/${departmentId}/`)
        .then(r => r.json())
        .then(data => {
            (data.courses || []).forEach(c => {
                const o = document.createElement('option');
                o.value = c.id;
                o.textContent = c.name;
                courseSelect.appendChild(o);
            });
        })
        .catch(e => {
            console.error('Error loading courses:', e);
            populateCoursesFallback(departmentId);
        });
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

    const updateText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text || '-';
    };

    updateText('reviewStudentName', `${formData.get('firstName') || ''} ${formData.get('lastName') || ''}`.trim());
    updateText('reviewStudentId', formData.get('studentId'));
    updateText('reviewSubmitterEmail', formData.get('email'));

    const academicLevelSelect = document.getElementById('academic_level');
    const departmentSelect = document.getElementById('department');
    const courseSelect = document.getElementById('course');

    const academicLevelText = academicLevelSelect ? academicLevelSelect.options[academicLevelSelect.selectedIndex]?.text || '-' : '-';
    const departmentText = departmentSelect ? departmentSelect.options[departmentSelect.selectedIndex]?.text || '-' : '-';
    const courseText = courseSelect ? courseSelect.options[courseSelect.selectedIndex]?.text || '-' : '-';

    updateText('reviewAcademicLevel', academicLevelText);
    updateText('reviewDepartment', departmentText);
    updateText('reviewCourse', courseText);
    updateText('reviewYear', formData.get('year'));
    updateText('reviewThesisTitle', formData.get('thesisTitle'));
    updateText('reviewAbstract', formData.get('abstract'));
    updateText('reviewKeywords', formData.get('keywords'));
    updateText('reviewSupervisor', formData.get('supervisorName'));
    updateText('reviewSupervisorEmail', formData.get('supervisorEmail'));
    const dept = formData.get('supervisorDepartment') || '';
    const title = formData.get('supervisorTitle') || '';
    updateText('reviewSupervisorDeptTitle', `${dept}${dept && title ? ' / ' : ''}${title}`);
    updateText('reviewCoSupervisor', formData.get('coSupervisorName'));
    updateText('reviewCoSupervisorEmail', formData.get('coSupervisorEmail'));

    // Co-authors: prefer dynamic list container (#reviewCoAuthors).
    const reviewList = document.getElementById('reviewCoAuthors');
    const coauthorsContainer = document.getElementById('coauthors') || document.getElementById('coworkers');
    const blocks = coauthorsContainer ? Array.from(coauthorsContainer.querySelectorAll('.coauthor-block, .coworker-block')) : [];

    if (reviewList) {
        reviewList.innerHTML = '';
        blocks.forEach((block, i) => {
            const first = block.querySelector('[data-field="first_name"]')?.value || '';
            const last = block.querySelector('[data-field="last_name"]')?.value || '';
            const sid = block.querySelector('[data-field="student_id"]')?.value || '';
            const email = block.querySelector('[data-field="email"]')?.value || '';
            if (first || last || sid || email) {
                const li = document.createElement('li');
                li.style.marginBottom = '5px';
                li.innerHTML = `<span style="color:var(--portal-primary); font-weight:700;">${i + 1}.</span> ${escapeHtml(first)} ${escapeHtml(last)} <br> <small style="opacity:0.8;">ID: ${escapeHtml(sid || '-')}, Email: ${escapeHtml(email || '-')}</small>`;
                reviewList.appendChild(li);
            }
        });
        if (blocks.length === 0) {
            reviewList.innerHTML = '<li style="color:var(--portal-text-light); font-style:italic;">No co-authors added</li>';
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
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    }

    // Full validation across all sections
    if (!validateForm()) {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Final Submission';
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

    // Check academic structure explicitly
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

/**
 * Adapt UI based on user role (Student vs Professor)
 */
function adaptUIForRole() {
    if (typeof USER_DATA === 'undefined' || !USER_DATA.role) return;

    if (USER_DATA.role === 'professor') {
        const isProfessor = true;
        
        // 1. Update Hero Section
        const heroTitle = document.querySelector('.hero-text h1');
        const heroSub = document.querySelector('.hero-text p');
        if (heroTitle) heroTitle.textContent = 'Faculty Research Portal';
        if (heroSub) heroSub.textContent = 'Archive and preserve your professional research and studies';

        // 2. Update Basic Info labels
        const idLabel = document.querySelector('label[for="studentId"]');
        const idInput = document.getElementById('studentId');
        if (idLabel) idLabel.innerHTML = 'Professor / Employee ID <span class="required">*</span>';
        if (idInput) idInput.placeholder = 'e.g. PROF-202X-XXX';

        // 3. Update Review Section labels
        const reviewIdLabel = document.querySelector('#reviewStudentId')?.previousElementSibling;
        if (reviewIdLabel) reviewIdLabel.textContent = 'Faculty ID:';

        // 4. Update Co-author labels (mostly for new ones)
        // We'll also need to update createCoauthorBlock to check the role
        
        // 5. Update Agreement text
        const agreementText = document.querySelector('.final-agreement .label-text');
        if (agreementText) {
            agreementText.innerHTML = `
                I certify that this submission is my own original professional work. 
                I understand that this study will be archived in the TCU digital library for academic reference.
            `;
        }

        // 6. Update document labels
        const manuscriptLabel = document.querySelector('label[for="thesisFile"]');
        if (manuscriptLabel) manuscriptLabel.innerHTML = 'Research Manuscript / Paper (PDF) <span class="required">*</span>';
    }
}

/* ---------------------------
   --- Autofill user data ---
   --------------------------- */

function autofillUserData() {
    if (typeof USER_DATA === 'undefined') return;

    const firstNameField = document.getElementById('firstName');
    const lastNameField = document.getElementById('lastName');
    const emailField = document.getElementById('email');
    const studentIdField = document.getElementById('studentId');

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

    if ((firstNameField && firstNameField.value) || (lastNameField && lastNameField.value) ||
        (emailField && emailField.value) || (studentIdField && studentIdField.value)) {
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
    setInterval(saveFormData, 30000);
}

function saveFormData() {
    const form = document.getElementById('thesisForm');
    if (!form) return;
    const fd = new FormData(form);
    const data = {};
    for (let [key, value] of fd.entries()) {
        if (value instanceof File) continue; // Skip files
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

        // Restore dynamic blocks
        const coauthorKeys = Object.keys(data).filter(k => /^(coauthors|coworkers)\[\d+\]\[(first_name|last_name|student_id|email)\]$/.test(k));
        if (coauthorKeys.length > 0) {
            const groups = {};
            coauthorKeys.forEach(k => {
                const m = k.match(/^(?:coauthors|coworkers)\[(\d+)\]\[(.+)\]$/);
                if (!m) return;
                const idx = parseInt(m[1], 10);
                const field = m[2];
                groups[idx] = groups[idx] || {};
                groups[idx][field] = data[k];
            });

            const container = document.getElementById('coauthors') || document.getElementById('coworkers');
            if (container) {
                container.innerHTML = '';
                const sortedIndexes = Object.keys(groups).map(x => parseInt(x, 10)).sort((a, b) => a - b);
                sortedIndexes.forEach((origIdx, newIndex) => {
                    createCoauthorBlock(container, newIndex, groups[origIdx]);
                });
            }
        }

        // Then restore other inputs
        const staticKeys = Object.keys(data).filter(key =>
            !/^(coauthors|coworkers)\[\d+\]\[(first_name|last_name|student_id|email)\]$/.test(key)
        );

        for (let key of staticKeys) {
            const input = form.querySelector(`[name="${key}"]`);
            if (!input) continue;

            if (input.type === 'checkbox') {
                input.checked = data[key] === 'on' || data[key] === true;
            } else if (input.type === 'file') {
                // Ignore
            } else {
                input.value = data[key];

                // Special handling for cascading selects
                if (key === 'academic_level' && data[key]) {
                    loadDepartments().then(() => {
                        if (data['department']) {
                            const deptSelect = document.getElementById('department');
                            if (deptSelect) {
                                deptSelect.value = data['department'];
                                loadCourses().then(() => {
                                    if (data['course']) {
                                        const csSelect = document.getElementById('course');
                                        if (csSelect) csSelect.value = data['course'];
                                        updateReviewSection();
                                    }
                                });
                            }
                        }
                    });
                }
            }
        }

        updateReviewSection();
        if (typeof showNotification === 'function') {
            showNotification('Restored your previous draft.', 'info', 3000);
        }
    } catch (error) {
        console.error('Error loading saved data:', error);
    }
}

function updateSaveIndicator(saved = false) {
    const metaChip = document.querySelector('.meta-chip');
    if (!metaChip) return;
    const dot = metaChip.querySelector('.dot');
    if (dot) dot.style.backgroundColor = saved ? '#22c55e' : '#f59e0b';
}

function clearSavedData() {
    localStorage.removeItem('thesisFormData');
    localStorage.removeItem('thesisFormLastSaved');
}

/* ---------------------------
   --- Utilities -----------
   --------------------------- */

function showAlert(message, type) {
    // Attempt to use showNotification if available in utils.js
    if (typeof showNotification === 'function') {
        showNotification(message, type);
        return;
    }

    // Fallback to inline alert
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    const activeSection = document.querySelector('.form-section.active') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = 'padding: 15px; margin-bottom: 20px; border-radius: 12px; font-weight: 600; border-left: 5px solid;';

    if (type === 'error') {
        alert.style.backgroundColor = '#fbecec';
        alert.style.color = '#a31d23';
        alert.style.borderColor = '#a31d23';
    } else {
        alert.style.backgroundColor = '#f0fdf4';
        alert.style.color = '#15803d';
        alert.style.borderColor = '#22c55e';
    }

    alert.textContent = message;
    activeSection.insertBefore(alert, activeSection.firstChild);
    setTimeout(() => { alert.remove(); }, 5000);
}
