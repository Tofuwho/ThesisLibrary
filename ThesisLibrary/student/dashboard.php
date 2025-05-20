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

// Get user information
$student_id = $_SESSION['user_id'];
$student_name = $_SESSION['name'];
$student_email = $_SESSION['email'];

// Get statistics (placeholder data - replace with actual database queries)
$total_submissions = 5;
$approved_submissions = 3;
$pending_submissions = 1;
$rejected_submissions = 1;

// Get recent activity (placeholder data - replace with actual database queries)
$recent_activity = [
    [
        'date' => '2025-05-15',
        'title' => 'Research Methodology in AI',
        'status' => 'approved',
        'id' => 101
    ],
    [
        'date' => '2025-05-10',
        'title' => 'Impact of Climate Change on Agriculture',
        'status' => 'pending',
        'id' => 102
    ],
    [
        'date' => '2025-04-28',
        'title' => 'Quantum Computing Applications',
        'status' => 'approved',
        'id' => 99
    ]
];

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Dashboard | Thesis Library</title>
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
                            <a href="dashboard.php" class="active">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                        </li>
                        <li>
                            <a href="submit.php">
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
                            <h2>Welcome back, <?php echo $student_name; ?>!</h2>
                            <p>Manage your thesis submissions and track your progress</p>
                        </div>
                        <div class="action-buttons">
                            <a href="submit.php" class="btn-student btn-primary">
                                <i class="fas fa-plus btn-icon"></i>New Submission
                            </a>
                        </div>
                    </div>

                    <!-- Stats -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <i class="fas fa-file-alt"></i>
                            <div class="stat-value"><?php echo $total_submissions; ?></div>
                            <div class="stat-label">Total Submissions</div>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-check-circle"></i>
                            <div class="stat-value"><?php echo $approved_submissions; ?></div>
                            <div class="stat-label">Approved</div>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-clock"></i>
                            <div class="stat-value"><?php echo $pending_submissions; ?></div>
                            <div class="stat-label">Pending Review</div>
                        </div>
                        <div class="stat-card">
                            <i class="fas fa-times-circle"></i>
                            <div class="stat-value"><?php echo $rejected_submissions; ?></div>
                            <div class="stat-label">Needs Revision</div>
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="content-card">
                        <div class="content-card-header">
                            <h3>Recent Activity</h3>
                            <a href="my-submissions.php" class="btn-student btn-outline-primary">View All</a>
                        </div>
                        <div class="content-card-body">
                            <div class="table-responsive">
                                <table class="data-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Thesis Title</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php foreach ($recent_activity as $activity): ?>
                                        <tr>
                                            <td><?php echo date('M d, Y', strtotime($activity['date'])); ?></td>
                                            <td><?php echo $activity['title']; ?></td>
                                            <td>
                                                <?php if ($activity['status'] == 'approved'): ?>
                                                    <span class="status-badge status-approved">Approved</span>
                                                <?php elseif ($activity['status'] == 'pending'): ?>
                                                    <span class="status-badge status-pending">Pending</span>
                                                <?php else: ?>
                                                    <span class="status-badge status-rejected">Rejected</span>
                                                <?php endif; ?>
                                            </td>
                                            <td>
                                                <div class="table-actions">
                                                    <a href="../thesis.php?id=<?php echo $activity['id']; ?>" class="action-icon action-icon-view" title="View">
                                                        <i class="fas fa-eye"></i>
                                                    </a>
                                                    <?php if ($activity['status'] != 'approved'): ?>
                                                    <a href="submit.php?edit=<?php echo $activity['id']; ?>" class="action-icon action-icon-edit" title="Edit">
                                                        <i class="fas fa-edit"></i>
                                                    </a>
                                                    <?php endif; ?>
                                                </div>
                                            </td>
                                        </tr>
                                        <?php endforeach; ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Guidelines Card -->
                    <div class="content-card">
                        <div class="content-card-header">
                            <h3>Submission Guidelines</h3>
                        </div>
                        <div class="content-card-body">
                            <p>Please follow these guidelines when submitting your thesis:</p>
                            <ul style="padding-left: 20px; margin: 15px 0;">
                                <li>Upload your thesis in PDF format only</li>
                                <li>Maximum file size: 10MB</li>
                                <li>Include an abstract of 200-300 words</li>
                                <li>Select the appropriate academic department and subject categories</li>
                                <li>All submissions will be reviewed by your department before appearing in the library</li>
                            </ul>
                            <a href="submit.php" class="btn-student btn-primary">Submit Thesis</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <?php include_once "../includes/footer.php"; ?>

    <script src="../assets/js/main.js"></script>
    <script>
        // Simple notification close functionality
        document.addEventListener('DOMContentLoaded', function() {
            const notifications = document.querySelectorAll('.notification');
            
            notifications.forEach(notification => {
                const closeBtn = notification.querySelector('.notification-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', function() {
                        notification.style.display = 'none';
                    });
                }
            });
        });
    </script>
</body>
</html>