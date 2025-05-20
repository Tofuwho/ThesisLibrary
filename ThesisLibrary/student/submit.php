<?php
// Start session
session_start();

// Check if user is logged in and is a student
if (!isset($_SESSION['user_id']) || $_SESSION['role'] !== 'student') {
    header("Location: ../landing.php");
    exit();
}

// Include database connection
// require_once '../includes/db_connect.php';

$student_id = $_SESSION['user_id'];
$student_name = $_SESSION['name'];

// Check if this is an edit request
$edit_mode = false;
$thesis_data = [];

if (isset($_GET['edit']) && !empty($_GET['edit'])) {
    $edit_mode = true;
    $thesis_id = $_GET['edit'];
    
    // In real application, fetch thesis data from database
    // For now, we'll use mock data
    $thesis_data = [
        'id' => $thesis_id,
        'title' => 'Impact of Climate Change on Agriculture',
        'abstract' => 'This thesis examines the effects of climate change on agricultural production systems and proposes adaptive strategies for sustainable farming in changing environmental conditions.',
        'keywords' => 'climate change, agriculture, sustainability, crop yield',
        'department' => 'Environmental Science',
        'supervisor' => 'Dr. Jane Smith',
        'co_authors' => 'Alex Johnson',
        'completion_date' => '2025-05-10',
        'file_path' => 'theses/climate_change_agriculture.pdf',
        'status' => 'pending'
    ];
}

// Define departments and categories
$departments = ['Computer Science', 'Engineering', 'Environmental Science', 'Business Administration', 'Medicine', 'Psychology', 'Physics', 'Mathematics', 'Literature', 'Economics'];

$categories = ['Research Paper', 'Case Study', 'Experimental', 'Review', 'Theoretical', 'Analytical', 'Descriptive', 'Comparative'];

// Form processing (submit or update)
$submission_message = '';
$message_type = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Process form submission
    
    // For demo purposes, we'll just set a success message
    if ($edit_mode) {
        $submission_message = "Your thesis has been updated successfully and is awaiting review.";
    } else {
        $submission_message = "Your thesis has been submitted successfully and is awaiting review.";
    }
    $message_type = "success";
    
    // In real application:
    // 1. Validate all inputs
    // 2. Handle file upload
    // 3. Insert/update in database
    // 4. Set appropriate messages
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $edit_mode ? 'Edit Thesis' : 'Submit Thesis'; ?> | Thesis Library</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="../assets/css/style.css">
    <link rel="stylesheet" href="../assets/css/student.css">
</head>
<body>
    <?php include_once "../includes/header.php"; ?>

    <section class="student-dashboard">
        <div class="container">
            <div class="dashboard-container">
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="profile-section">
                        <div class="profile-avatar">
                            <?php echo substr($student_name, 0, 1); ?>
                        </div>
                        <div class="profile-info">
                            <h3 class="profile-name"><?php echo $student_name; ?></h3>
                            <p class="profile-id">Student ID: <?php echo $student_id; ?></p>
                        </div>
                    </div>
                    <ul class="sidebar-menu">
                        <li>
                            <a href="dashboard.php">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                        </li>
                        <li>
                            <a href="submit.php" class="active">
                                <i class="fas fa-upload"></i> Submit Thesis
                            </a>
                        </li>
                        <li>
                            <a href="my-submissions.php">
                                <i class="fas fa-file-alt"></i> My Submissions
                            </a>
                        </li>
                        <li>
                            <a href="../thesis.php">
                                <i class="fas fa-search"></i> Browse Theses
                            </a>
                        </li>
                        <li>
                            <a href="../includes/logout.php">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </li>
                    </ul>
                </div>

                <!-- Main Content -->
                <div class="main-content">
                    <div class="dashboard-header">
                        <div class="welcome-text">
                            <h2><?php echo $edit_mode ? 'Edit Thesis' : 'Submit New Thesis'; ?></h2>
                            <p>Please fill in all the required information about your thesis</p>
                        </div>
                        <div class="action-buttons">
                            <a href="my-submissions.php" class="btn-student btn-outline-primary">
                                <i class="fas fa-arrow-left btn-icon"></i>Back to My Submissions
                            </a>
                        </div>
                    </div>

                    <?php if (!empty($submission_message)): ?>
                    <div class="notification notification-<?php echo $message_type; ?>">
                        <i class="fas fa-info-circle"></i> <?php echo $submission_message; ?>
                        <span class="notification-close"><i class="fas fa-times"></i></span>
                    </div>
                    <?php endif; ?>

                    <!-- Submission Progress -->
                    <div class="progress-tracker">
                        <div class="progress-step active">
                            <div class="step-icon">1</div>
                            <div class="step-label">Fill Details</div>
                        </div>
                        <div class="progress-step">
                            <div class="step-icon">2</div>
                            <div class="step-label">Upload File</div>
                        </div>
                        <div class="progress-step">
                            <div class="step-icon">3</div>
                            <div class="step-label">Preview</div>
                        </div>
                        <div class="progress-step">
                            <div class="step-icon">4</div>
                            <div class="step-label">Submit</div>
                        </div>
                    </div>

                    <!-- Form Content -->
                    <div class="content-card">
                        <div class="content-card-header">
                            <h3>Thesis Information</h3>
                        </div>
                        <div class="content-card-body">
                            <form action="submit.php<?php echo $edit_mode ? '?edit='.$thesis_id : ''; ?>" method="POST" enctype="multipart/form-data" id="thesisForm">
                                
                                <?php if ($edit_mode): ?>
                                <input type="hidden" name="thesis_id" value="<?php echo $thesis_data['id']; ?>">
                                <?php endif; ?>
                                
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label for="title">Thesis Title *</label>
                                        <input type="text" id="title" name="title" class="form-control" value="<?php echo $edit_mode ? $thesis_data['title'] : ''; ?>" required>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="department">Department *</label>
                                        <select id="department" name="department" class="form-control" required>
                                            <option value="">Select Department</option>
                                            <?php foreach ($departments as $department): ?>
                                            <option value="<?php echo $department; ?>" <?php echo ($edit_mode && $thesis_data['department'] == $department) ? 'selected' : ''; ?>><?php echo $department; ?></option>
                                            <?php endforeach; ?>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="abstract">Abstract (200-300 words) *</label>
                                    <textarea id="abstract" name="abstract" class="form-control" rows="6" required><?php echo $edit_mode ? $thesis_data['abstract'] : ''; ?></textarea>
                                    <div id="wordCounter" style="text-align: right; font-size: 0.8rem; color: var(--medium-gray);">
                                        0 words (min: 200, max: 300)
                                    </div>
                                </div>
                                
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label for="keywords">Keywords (comma separated) *</label>
                                        <input type="text" id="keywords" name="keywords" class="form-control" value="<?php echo $edit_mode ? $thesis_data['keywords'] : ''; ?>" required>
                                        <small class="helper-text">Example: AI, machine learning, neural networks</small>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="category">Category *</label>
                                        <select id="category" name="category" class="form-control" required>
                                            <option value="">Select Category</option>
                                            <?php foreach ($categories as $category): ?>
                                            <option value="<?php echo $category; ?>"><?php echo $category; ?></option>
                                            <?php endforeach; ?>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label for="supervisor">Supervisor Name *</label>
                                        <input type="text" id="supervisor" name="supervisor" class="form-control" value="<?php echo $edit_mode ? $thesis_data['supervisor'] : ''; ?>" required>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label for="co_authors">Co-Authors (if any)</label>
                                        <input type="text" id="co_authors" name="co_authors" class="form-control" value="<?php echo $edit_mode ? $thesis_data['co_authors'] : ''; ?>">
                                    </div>
                                </div>
                                
                                <div class="form-grid">
                                    <div class="form-group">
                                        <label for="completion_date">Completion Date *</label>
                                        <input type="date" id="completion_date" name="completion_date" class="form-control" value="<?php echo $edit_mode ? $thesis_data['completion_date'] : ''; ?>" required>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label>Access Level *</label>
                                        <div style="display: flex; gap: 20px; margin-top: 10px;">
                                            <label style="font-weight: normal;">
                                                <input type="radio" name="access_level" value="public" checked> Public
                                            </label>
                                            <label style="font-weight: normal;">
                                                <input type="radio" name="access_level" value="restricted"> Restricted
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- File upload section -->
                                <div class="form-group">
                                    <label>Thesis PDF *</label>
                                    <label for="thesis_file" class="file-upload">
                                        <i class="fas fa-cloud-upload-alt"></i>
                                        <div class="file-upload-text">
                                            <h4>Upload your thesis document</h4>
                                            <p id="file-name"><?php echo $edit_mode ? basename($thesis_data['file_path']) : 'PDF format only, max 10MB'; ?></p>
                                        </div>
                                        <input type="file" id="thesis_file" name="thesis_file" accept=".pdf" <?php echo $edit_mode ? '' : 'required'; ?>>
                                    </label>
                                </div>
                                
                                <div class="form-group" style="margin-top: 30px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <button type="button" class="btn-student btn-outline-primary" onclick="window.location.href='dashboard.php'">
                                            <i class="fas fa-times btn-icon"></i>Cancel
                                        </button>
                                        <button type="submit" class="btn-student btn-primary">
                                            <i class="fas fa-paper-plane btn-icon"></i><?php echo $edit_mode ? 'Update Thesis' : 'Submit Thesis'; ?>
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <?php include_once "../includes/footer.php"; ?>

    <script src="../assets/js/main.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Word counter for abstract
            const abstractField = document.getElementById('abstract');
            const wordCounter = document.getElementById('wordCounter');
            
            function countWords(text) {
                const words = text.trim().split(/\s+/).filter(Boolean);
                return words.length;
            }
            
            function updateWordCount() {
                const wordCount = countWords(abstractField.value);
                let color = 'var(--medium-gray)';
                
                if (wordCount < 200) {
                    color = 'var(--danger-color)';
                } else if (wordCount > 300) {
                    color = 'var(--danger-color)';
                } else {
                    color = 'var(--success-color)';
                }
                
                wordCounter.innerHTML = `${wordCount} words (min: 200, max: 300)`;
                wordCounter.style.color = color;
            }
            
            abstractField.addEventListener('input', updateWordCount);
            
            // Initial count if edit mode
            if (abstractField.value) {
                updateWordCount();
            }
            
            // File upload preview
            const fileInput = document.getElementById('thesis_file');
            const fileNameDisplay = document.getElementById('file-name');
            
            fileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const file = this.files[0];
                    
                    // Check file type
                    if (file.type !== 'application/pdf') {
                        alert('Only PDF files are allowed!');
                        this.value = '';
                        return;
                    }
                    
                    // Check file size (max 10MB)
                    if (file.size > 10 * 1024 * 1024) {
                        alert('File size exceeds 10MB limit!');
                        this.value = '';
                        return;
                    }
                    
                    fileNameDisplay.textContent = file.name;
                }
            });
            
            // Close notifications
            const notifications = document.querySelectorAll('.notification');
            notifications.forEach(notification => {
                const closeBtn = notification.querySelector('.notification-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', function() {
                        notification.style.display = 'none';
                    });
                }
            });
            
            // Form validation
            const form = document.getElementById('thesisForm');
            form.addEventListener('submit', function(event) {
                const wordCount = countWords(abstractField.value);
                
                if (wordCount < 200 || wordCount > 300) {
                    event.preventDefault();
                    alert('Abstract must be between 200 and 300 words.');
                    abstractField.focus();
                }
            });
        });
    </script>
</body>
</html>