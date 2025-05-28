<?php 
session_start(); // Ensure this is at the top of your PHP files
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thesis Library</title>
    <link rel="stylesheet" href="<?php echo BASE_URL; ?>assets/css/style.css">
    <link rel="stylesheet" href="<?php echo BASE_URL; ?>assets/css/student.css">
    <link rel="stylesheet" href="<?php echo BASE_URL; ?>assets/css/categories.css">
</head>
<body>
    <header class="main-header">
        <div class="container">
            <div class="logo-container">
                <div class="logo-square"></div>
                <h1>Thesis Library</h1>
            </div>
            <nav class="main-nav">
                <ul>
                    <li><a href="<?php echo BASE_URL; ?>index.php" class="nav-link">Home</a></li>
                    <li><a href="<?php echo BASE_URL; ?>categories.php" class="nav-link">Categories</a></li>
                    <li><a href="#" class="nav-link">About</a></li>
                    <li><a href="#" class="nav-link">Contact</a></li>
                </ul>
            </nav>
            <div class="auth-buttons">
                <?php 
                
                if (isset($_SESSION['role'])): 
                    if ($_SESSION['role'] === 'student'): ?>
                        <a href="<?php echo BASE_URL; ?>student/dashboard.php" class="btn btn-outline">Dashboard</a>
                    <?php elseif ($_SESSION['role'] === 'admin'): ?>
                        <a href="<?php echo BASE_URL; ?>admin/dashboard.php" class="btn btn-outline">Dashboard</a>
                    <?php endif; 
                endif; ?>
                <a href="<?php echo BASE_URL; ?>auth/logout.php" class="btn btn-outline" style="margin-left: 10px;">Log Out</a>
            </div>
        </div>
    </header>
    <main>