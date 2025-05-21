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

// Load user data from JSON file
$usersData = json_decode(file_get_contents("../storage/users.json"), true);

// Find the current user
$currentUser = null;
foreach ($usersData['users'] as $user) {
    if ($user['id'] == $userId) {
        $currentUser = $user;
        break;
    }
}

if (!$currentUser) {
    // Handle error - user not found
    header("Location: ../landing.php?error=user_not_found");
    exit();
}

// Get student's submissions
$studentSubmissions = [];
$thesesDir = "../storage/theses/";

// Check if directory exists
if (is_dir($thesesDir)) {
    $files = scandir($thesesDir);
    
    foreach ($files as $file) {
        // Skip . and .. directories
        if ($file === '.' || $file === '..') {
            continue;
        }
        
        // Check if the file belongs to this student (using naming convention)
        // Assuming files follow pattern: YYYY_Department_AuthorName.extension
        $fileInfo = pathinfo($file);
        $filename = $fileInfo['filename'];
        
        // Extract author name from filename
        $parts = explode('_', $filename);
        if (count($parts) >= 3) {
            $authorName = str_replace('-', ' ', end($parts));
            
            // Simple check - if author name contains student's username
            // This is a basic approach - you might want to refine this logic
            if (stripos($authorName, $username) !== false || 
                stripos($file, $userId) !== false) {
                
                // Get file info
                $fileSize = filesize($thesesDir . $file);
                $fileDate = filemtime($thesesDir . $file);
                
                // Get year and department from filename
                $year = $parts[0] ?? 'Unknown';
                $department = $parts[1] ?? 'Unknown';
                
                $studentSubmissions[] = [
                    'filename' => $file,
                    'title' => str_replace('-', ' ', $filename),
                    'size' => $fileSize,
                    'date' => date('F j, Y', $fileDate),
                    'year' => $year,
                    'department' => $department
                ];
            }
        }
    }
}

// Sort submissions by date (newest first)
usort($studentSubmissions, function($a, $b) {
    return strtotime($b['date']) - strtotime($a['date']);
});

// Load header
include_once "../includes/header.php";
?>

<div class="container mt-4">
    <h1>Student Dashboard</h1>
    <p>Welcome, <?php echo htmlspecialchars($username); ?>!</p>
    
    <div class="row mt-4">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Quick Actions</h5>
                    <div class="list-group">
                        <a href="submit.php" class="list-group-item list-group-item-action">
                            <i class="fas fa-upload"></i> Submit New Thesis
                        </a>
                        <a href="my-submissions.php" class="list-group-item list-group-item-action">
                            <i class="fas fa-folder"></i> My Submissions
                        </a>
                        <a href="../index.php" class="list-group-item list-group-item-action">
                            <i class="fas fa-search"></i> Browse Theses
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-body">
                    <h5 class="card-title">My Account</h5>
                    <p><strong>Name:</strong> <?php echo htmlspecialchars($currentUser['name'] ?? $username); ?></p>
                    <p><strong>Department:</strong> <?php echo htmlspecialchars($currentUser['department'] ?? 'Not specified'); ?></p>
                    <p><strong>Year Level:</strong> <?php echo htmlspecialchars($currentUser['year_level'] ?? 'Not specified'); ?></p>
                </div>
            </div>
        </div>
        
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5>Recent Submissions</h5>
                </div>
                <div class="card-body">
                    <?php if (count($studentSubmissions) > 0): ?>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Thesis Title</th>
                                        <th>Year</th>
                                        <th>Department</th>
                                        <th>Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php foreach (array_slice($studentSubmissions, 0, 5) as $submission): ?>
                                    <tr>
                                        <td><?php echo htmlspecialchars($submission['title']); ?></td>
                                        <td><?php echo htmlspecialchars($submission['year']); ?></td>
                                        <td><?php echo htmlspecialchars($submission['department']); ?></td>
                                        <td><?php echo htmlspecialchars($submission['date']); ?></td>
                                        <td>
                                            <a href="../thesis.php?file=<?php echo urlencode($submission['filename']); ?>" 
                                               class="btn btn-sm btn-primary">View</a>
                                        </td>
                                    </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>
                    <?php else: ?>
                        <div class="alert alert-info">
                            You haven't submitted any theses yet. 
                            <a href="submit.php" class="alert-link">Submit your first thesis now</a>.
                        </div>
                    <?php endif; ?>
                </div>
                <?php if (count($studentSubmissions) > 5): ?>
                <div class="card-footer">
                    <a href="my-submissions.php" class="btn btn-outline-primary">View All Submissions</a>
                </div>
                <?php endif; ?>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h5>System Announcements</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <strong>Welcome to the offline Thesis Library system!</strong><br>
                        This system allows you to submit and manage your thesis documents.
                    </div>
                    <!-- Additional announcements can be added here -->
                </div>
            </div>
        </div>
    </div>
</div>

<?php
// Load footer
include_once "../includes/footer.php";
?>