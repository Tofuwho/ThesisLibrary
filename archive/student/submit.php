<?php
// Start session
session_start();

// Check if user is logged in and is a student
if (!isset($_SESSION['user_id']) || $_SESSION['role'] !== 'student') {
    header("Location: ../landing.php");
    exit();
}

$userId = $_SESSION['user_id'];
$username = $_SESSION['username'];

// Process form submission
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Retrieve form data
    $title = trim($_POST['thesis_title'] ?? '');
    $abstract = trim($_POST['abstract'] ?? '');
    $department = $_POST['department'] ?? '';
    $year = $_POST['year'] ?? date('Y');
    $keywords = trim($_POST['keywords'] ?? '');
    
    // Retrieve co-workers
    $coworkers = isset($_POST['coworkers']) ? $_POST['coworkers'] : [];

    // Validate required fields
    if (empty($title) || empty($department) || empty($year)) {
        $message = "All required fields must be filled.";
        $messageType = "danger";
    } 
    // Check if file was uploaded
    elseif (!isset($_FILES['thesis_file']) || $_FILES['thesis_file']['error'] !== UPLOAD_ERR_OK) {
        $message = "Please select a valid thesis file to upload.";
        $messageType = "danger";
    } 
    else {
        // File upload configuration
        $uploadDir = "../storage/theses/";
        $fileInfo = pathinfo($_FILES['thesis_file']['name']);
        $fileExtension = strtolower($fileInfo['extension']);
        
        // Check file extension (allowing common document formats)
        $allowedExtensions = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'];
        
        if (!in_array($fileExtension, $allowedExtensions)) {
            $message = "Invalid file type. Allowed file types: " . implode(', ', $allowedExtensions);
            $messageType = "danger";
        } 
        else {
            // Create a sanitized filename from title and user's name
            $sanitizedTitle = preg_replace('/[^a-zA-Z0-9]/', '-', $title);
            $sanitizedAuthor = preg_replace('/[^a-zA-Z0-9]/', '-', $authors);
            
            // Format: YYYY_Department_AuthorName.extension
            $newFilename = $year . '_' . $department . '_' . $sanitizedAuthor . '.' . $fileExtension;
            $uploadPath = $uploadDir . $newFilename;
            
            // Check if file already exists
            if (file_exists($uploadPath)) {
                $message = "A file with this name already exists. Please try a different title or author name.";
                $messageType = "danger";
            } 
            else {
                // Ensure the upload directory exists
                if (!is_dir($uploadDir)) {
                    mkdir($uploadDir, 0755, true);
                }
                
                // Move uploaded file
                if (move_uploaded_file($_FILES['thesis_file']['tmp_name'], $uploadPath)) {
                    // Create a metadata file for the thesis
                    $metadataFile = $uploadDir . $year . '_' . $department . '_' . $sanitizedAuthor . '.json';
                    $metadata = [
                        'title' => $title,
                        'abstract' => $abstract,
                        'authors' => $authors,
                        'department' => $department,
                        'year' => $year,
                        'keywords' => $keywords,
                        'file' => $newFilename,
                        'uploaded_by' => $userId,
                        'uploaded_at' => date('Y-m-d H:i:s'),
                        'file_size' => $_FILES['thesis_file']['size'],
                    ];
                    
                    file_put_contents($metadataFile, json_encode($metadata, JSON_PRETTY_PRINT));
                    
                    $message = "Your thesis has been successfully uploaded!";
                    $messageType = "success";
                    
                    // Optional: Log the action
                    $logEntry = date('Y-m-d H:i:s') . " - User $userId ($username) uploaded thesis: $newFilename\n";
                    file_put_contents("../storage/upload_log.txt", $logEntry, FILE_APPEND);
                    
                    // Redirect to view the thesis
                    header("Location: my-submissions.php?message=upload_success");
                    exit();
                } 
                else {
                    $message = "Failed to upload the file. Please try again.";
                    $messageType = "danger";
                }
            }
        }
    }
}

// Load header
include_once "../includes/header.php";
?>

<div class="container mt-4">
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header">
                    <h2>Submit Thesis</h2>
                </div>
                <div class="card-body">
                    <?php if (!empty($message)): ?>
                    <div class="alert alert-<?php echo $messageType; ?>" role="alert">
                        <?php echo htmlspecialchars($message); ?>
                    </div>
                    <?php endif; ?>
                    
                    <form method="POST" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label for="thesis_title" class="form-label">Thesis Title <span class="text-danger">*</span></label>
                            <input type="text" class="form-control" id="thesis_title" name="thesis_title" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="authors" class="form-label">Author(s) <span class="text-danger">*</span></label>
                            <input type="text" class="form-control" id="authors" name="authors" required placeholder="e.g., Juan Dela Cruz">
                        </div>
                        
                        <div class="mb-3">
                            <label for="department" class="form-label">Department <span class="text-danger">*</span></label>
                            <select class="form-select" id="department" name="department" required>
                                <option value="">Select Department</option>
                                <?php foreach ($departments as $code => $name): ?>
                                    <option value="<?php echo htmlspecialchars($code); ?>"><?php echo htmlspecialchars($name); ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="year" class="form-label">Year <span class="text-danger">*</span></label>
                            <select class="form-select" id="year" name="year" required>
                                <?php 
                                $currentYear = date('Y');
                                for ($year = $currentYear; $year >= $currentYear - 10; $year--): 
                                ?>
                                    <option value="<?php echo $year; ?>"><?php echo $year; ?></option>
                                <?php endfor; ?>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="abstract" class="form-label">Abstract</label>
                            <textarea class="form-control" id="abstract" name="abstract" rows="5"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label for="thesis_file" class="form-label">Thesis Document <span class="text-danger">*</span></label>
                            <input type="file" class="form-control" id="thesis_file" name="thesis_file" required>
                        </div>
                        
                        <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                            <a href="dashboard.php" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">Submit Thesis</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<?php
// Load footer
include_once "../includes/footer.php";
?>