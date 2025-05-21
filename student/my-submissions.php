</div>
            <div class="modal-body">
                <p>Are you sure you want to delete <strong id="deleteThesisTitle"></strong>?</p>
                <p class="text-danger">This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form method="POST">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="filename" id="deleteFilename">
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Set up delete modal data
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const filename = button.getAttribute('data-filename');
            const title = button.getAttribute('data-title');
            
            document.getElementById('deleteFilename').value = filename;
            document.getElementById('deleteThesisTitle').textContent = title;
        });
    }
    
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = document.getElementById('submissionsTable');
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
            
            for (let i = 0; i < rows.length; i++) {
                const rowText = rows[i].textContent.toLowerCase();
                if (rowText.includes(searchTerm)) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        });
    }
});
</script>

<?php
// Load footer
include_once "../includes/footer.php";
?><?php
// Start session
session_start();

// Check if user is logged in and is a student
if (!isset($_SESSION['user_id']) || $_SESSION['role'] !== 'student') {
    header("Location: ../landing.php");
    exit();
}

$userId = $_SESSION['user_id'];
$username = $_SESSION['username'];

// Process messages
$message = '';
$messageType = '';

if (isset($_GET['message'])) {
    switch ($_GET['message']) {
        case 'upload_success':
            $message = "Your thesis has been successfully uploaded!";
            $messageType = "success";
            break;
        case 'delete_success':
            $message = "Thesis has been successfully deleted.";
            $messageType = "success";
            break;
        case 'update_success':
            $message = "Thesis information has been updated successfully.";
            $messageType = "success";
            break;
    }
}

// Handle delete action (if implemented)
if (isset($_POST['action']) && $_POST['action'] === 'delete' && isset($_POST['filename'])) {
    $filename = $_POST['filename'];
    $thesisFile = "../storage/theses/" . $filename;
    $metadataFile = "../storage/theses/" . pathinfo($filename, PATHINFO_FILENAME) . ".json";
    
    // Security check: Verify this file belongs to the current user
    $belongsToUser = false;
    
    if (file_exists($metadataFile)) {
        $metadata = json_decode(file_get_contents($metadataFile), true);
        if (isset($metadata['uploaded_by']) && $metadata['uploaded_by'] == $userId) {
            $belongsToUser = true;
        }
    } else {
        // Fallback to filename check if no metadata
        $filenameParts = explode('_', pathinfo($filename, PATHINFO_FILENAME));
        if (count($filenameParts) >= 3) {
            $authorName = str_replace('-', ' ', end($filenameParts));
            if (stripos($authorName, $username) !== false) {
                $belongsToUser = true;
            }
        }
    }
    
    if ($belongsToUser) {
        // Delete the files
        if (file_exists($thesisFile)) {
            unlink($thesisFile);
        }
        if (file_exists($metadataFile)) {
            unlink($metadataFile);
        }
        
        // Log the action
        $logEntry = date('Y-m-d H:i:s') . " - User $userId ($username) deleted thesis: $filename\n";
        file_put_contents("../storage/deletion_log.txt", $logEntry, FILE_APPEND);
        
        $message = "Thesis has been successfully deleted.";
        $messageType = "success";
    } else {
        $message = "You do not have permission to delete this file.";
        $messageType = "danger";
    }
}

// Get student's submissions
$studentSubmissions = [];
$thesesDir = "../storage/theses/";

// Function to extract metadata from JSON or from filename
function getThesisMetadata($filename, $thesesDir) {
    $metadataFile = $thesesDir . pathinfo($filename, PATHINFO_FILENAME) . ".json";
    
    if (file_exists($metadataFile)) {
        return json_decode(file_get_contents($metadataFile), true);
    } else {
        // Extract basic info from filename
        $fileInfo = pathinfo($filename);
        $filenameParts = explode('_', $fileInfo['filename']);
        
        $year = $filenameParts[0] ?? 'Unknown';
        $department = $filenameParts[1] ?? 'Unknown';
        $authorName = isset($filenameParts[2]) ? str_replace('-', ' ', $filenameParts[2]) : 'Unknown';
        
        return [
            'title' => str_replace('-', ' ', $fileInfo['filename']),
            'authors' => $authorName,
            'department' => $department,
            'year' => $year,
            'file' => $filename,
            'uploaded_at' => date('Y-m-d H:i:s', filemtime($thesesDir . $filename)),
            'file_size' => filesize($thesesDir . $filename),
        ];
    }
}

// Check if directory exists
if (is_dir($thesesDir)) {
    $files = scandir($thesesDir);
    
    foreach ($files as $file) {
        // Skip . and .. directories and JSON metadata files
        if ($file === '.' || $file === '..' || pathinfo($file, PATHINFO_EXTENSION) === 'json') {
            continue;
        }
        
        // Get metadata
        $metadata = getThesisMetadata($file, $thesesDir);
        
        // Check if the file belongs to this student
        $belongsToUser = false;
        
        if (isset($metadata['uploaded_by']) && $metadata['uploaded_by'] == $userId) {
            $belongsToUser = true;
        } else {
            // Fallback to checking the filename
            $authorName = $metadata['authors'] ?? '';
            if (stripos($authorName, $username) !== false || stripos($file, $username) !== false) {
                $belongsToUser = true;
            }
        }
        
        if ($belongsToUser) {
            // Format file size
            $fileSize = $metadata['file_size'] ?? filesize($thesesDir . $file);
            if ($fileSize < 1024) {
                $formattedSize = $fileSize . " B";
            } elseif ($fileSize < 1048576) {
                $formattedSize = round($fileSize / 1024, 2) . " KB";
            } else {
                $formattedSize = round($fileSize / 1048576, 2) . " MB";
            }
            
            $metadata['formatted_size'] = $formattedSize;
            $metadata['filename'] = $file;
            
            // Get upload date
            if (!isset($metadata['uploaded_at'])) {
                $metadata['uploaded_at'] = date('Y-m-d H:i:s', filemtime($thesesDir . $file));
            }
            
            $studentSubmissions[] = $metadata;
        }
    }
}

// Sort submissions by upload date (newest first)
usort($studentSubmissions, function($a, $b) {
    return strtotime($b['uploaded_at']) - strtotime($a['uploaded_at']);
});

// Load header
include_once "../includes/header.php";
?>

<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>My Submissions</h1>
        <a href="submit.php" class="btn btn-primary">
            <i class="fas fa-upload"></i> Submit New Thesis
        </a>
    </div>
    
    <?php if (!empty($message)): ?>
    <div class="alert alert-<?php echo $messageType; ?>" role="alert">
        <?php echo htmlspecialchars($message); ?>
    </div>
    <?php endif; ?>
    
    <?php if (empty($studentSubmissions)): ?>
    <div class="alert alert-info">
        <p>You haven't submitted any theses yet.</p>
        <a href="submit.php" class="btn btn-sm btn-primary mt-2">Submit your first thesis</a>
    </div>
    <?php else: ?>
    <div class="card">
        <div class="card-header bg-light">
            <div class="row">
                <div class="col-md-6">
                    <h5 class="mb-0">Your Theses (<?php echo count($studentSubmissions); ?>)</h5>
                </div>
                <div class="col-md-6">
                    <input type="text" id="searchInput" class="form-control" placeholder="Search theses...">
                </div>
            </div>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover table-striped mb-0" id="submissionsTable">
                    <thead class="thead-light">
                        <tr>
                            <th>Title</th>
                            <th>Year</th>
                            <th>Department</th>
                            <th>File Size</th>
                            <th>Uploaded</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($studentSubmissions as $submission): ?>
                        <tr>
                            <td><?php echo htmlspecialchars($submission['title'] ?? 'Unknown Title'); ?></td>
                            <td><?php echo htmlspecialchars($submission['year'] ?? 'Unknown'); ?></td>
                            <td><?php echo htmlspecialchars($submission['department_full'] ?? $submission['department'] ?? 'Unknown'); ?></td>
                            <td><?php echo htmlspecialchars($submission['formatted_size'] ?? 'Unknown'); ?></td>
                            <td>
                                <?php 
                                $uploadDate = isset($submission['uploaded_at']) ? new DateTime($submission['uploaded_at']) : null;
                                echo $uploadDate ? $uploadDate->format('M j, Y, g:i a') : 'Unknown';
                                ?>
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <a href="../thesis.php?file=<?php echo urlencode($submission['filename']); ?>" 
                                       class="btn btn-sm btn-primary" title="View">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                    <a href="../storage/theses/<?php echo urlencode($submission['filename']); ?>" 
                                       class="btn btn-sm btn-success" title="Download" download>
                                        <i class="fas fa-download"></i>
                                    </a>
                                    <button type="button" class="btn btn-sm btn-danger" title="Delete"
                                            data-bs-toggle="modal" data-bs-target="#deleteModal"
                                            data-filename="<?php echo htmlspecialchars($submission['filename']); ?>"
                                            data-title="<?php echo htmlspecialchars($submission['title'] ?? 'this thesis'); ?>">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <?php endif; ?>
    
    <div class="mt-4">
        <a href="dashboard.php" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Dashboard
        </a>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="deleteModalLabel">Confirm Deletion</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>