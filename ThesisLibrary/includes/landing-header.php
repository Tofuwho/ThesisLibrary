<?php
// Start session if not already started
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thesis Library Repository</title>
    <link rel="stylesheet" href="assets/css/landing.css">
</head>
<body>
    <header class="landing-header">
        <div class="container">
            <div class="logo">
                <h1>Thesis Library</h1>
            </div>
            <nav>
                <ul>
                    <?php if (isset($_SESSION['user'])): ?>
                        <?php if ($_SESSION['role'] === 'admin'): ?>
                            <li><a href="admin/dashboard.php">Admin Dashboard</a></li>
                        <?php else: ?>
                            <li><a href="student/dashboard.php">My Dashboard</a></li>
                        <?php endif; ?>
                        <li><a href="logout.php">Logout</a></li>
                    <?php else: ?>
                        <li><button id="openModal" class="login-btn">Login</button></li>
                    <?php endif; ?>
                </ul>
            </nav>
        </div>
    </header>