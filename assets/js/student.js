// script.js
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    setupFileUploads();
    setupKeywordInput();
});

// Navigation between sections
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
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Show target section
    document.getElementById(sectionId).classList.add('active');
    
    // Update navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
    
    // Update progress bar
    updateProgressBar(sectionId);
}

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

function validateCurrentSection() {
    const activeSection = document.querySelector('.section.active');
    const requiredFields = activeSection.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = 'var(--primary-color)';
            field.focus();
            isValid = false;
            return false;
        } else {
            field.style.borderColor = 'var(--light-gray)';
        }
    });
    
    return isValid;
}

// Initialize event listeners
function initializeEventListeners() {
    // Navigation click handlers
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            showSection(sectionId);
        });
    });
    
    // Form submission handler
    document.getElementById('thesisForm').addEventListener('submit', handleFormSubmission);
    
    // Real-time validation
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
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

// File upload functionality
function setupFileUploads() {
    setupSingleFileUpload('thesisFile', 'thesisFileList', 50);
    setupMultipleFileUpload('supportingFiles', 'supportingFilesList', 10);
    
    // Drag and drop functionality
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
            fileInput.files = e.dataTransfer.files;
            handleFileSelection(fileInput);
        });
    });
}

function setupSingleFileUpload(inputId, listId, maxSizeMB) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    
    input.addEventListener('change', function() {
        handleFileSelection(this, listId, maxSizeMB, false);
    });
}

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

// Keywords functionality
let keywords = [];

function setupKeywordInput() {
    const keywordInput = document.getElementById('keywordInput');
    keywordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addKeyword();
        }
    });
}

function addKeyword() {
    const input = document.getElementById('keywordInput');
    const keyword = input.value.trim();
    
    if (keyword && !keywords.includes(keyword)) {
        keywords.push(keyword);
        updateKeywordTags();
        input.value = '';
        document.getElementById('keywords').value = keywords.join(',');
    }
}

function removeKeyword(keyword) {
    keywords = keywords.filter(k => k !== keyword);
    updateKeywordTags();
    document.getElementById('keywords').value = keywords.join(',');
}

function updateKeywordTags() {
    const container = document.getElementById('keywordTags');
    container.innerHTML = '';
    
    keywords.forEach(keyword => {
        const tag = document.createElement('div');
        tag.className = 'keyword-tag';
        tag.innerHTML = `
            ${keyword}
            <span class="remove" onclick="removeKeyword('${keyword}')">×</span>
        `;
        container.appendChild(tag);
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
    document.getElementById('reviewDepartment').textContent = formData.get('department') || '-';
    document.getElementById('reviewDegreeLevel').textContent = formData.get('degreeLevel') || '-';
    document.getElementById('reviewCategory').textContent = formData.get('category') || '-';
    document.getElementById('reviewThesisTitle').textContent = formData.get('thesisTitle') || '-';
    document.getElementById('reviewAbstract').textContent = formData.get('abstract') || '-';
    document.getElementById('reviewKeywords').textContent = formData.get('keywords') || '-';
    document.getElementById('reviewSupervisor').textContent = formData.get('supervisorName') || '-';

    // Collect co-workers information
    for (let i = 0; i < 3; i++) { // Assuming you have 3 co-workers
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
    const formData = new FormData(form);

    // Submit normally to server; server will redirect and show messages
    form.submit();
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