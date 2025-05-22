<?php
session_start();
require_once '../db/connection.php'; // Make sure this defines $pdo

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['signup_username'] ?? '');
    $email = trim($_POST['signup_email'] ?? '');
    $password = $_POST['signup_password'] ?? '';
    $role = $_POST['role'] ?? 'student';

    // Basic validation
    if (empty($username) || empty($email) || empty($password) || empty($role)) {
        die('Please fill in all required fields.');
    }

    try {
        // Check if user already exists
        $stmt = $pdo->prepare("SELECT id FROM users WHERE email = :email OR username = :username");
        $stmt->execute([
            'email' => $email,
            'username' => $username
        ]);
        if ($stmt->fetch()) {
            die('Email or Username already taken.');
        }

        // Hash the password
        $hashedPassword = password_hash($password, PASSWORD_DEFAULT);

        // Insert user into database
        $stmt = $pdo->prepare("INSERT INTO users (username, email, password, role) 
                               VALUES (:username, :email, :password, :role)");
        $stmt->execute([
            'username' => $username,
            'email' => $email,
            'password' => $hashedPassword,
            'role' => $role
        ]);

        // Set session
        $_SESSION['user'] = $username;
        $_SESSION['role'] = $role;

        // Return success instead of redirecting
        echo "success";
        exit;

        if ($role === 'admin') {
            header('Location: ../admin/dashboard.php');
        } else {
            header('Location: ../student/dashboard.php');
        }
        exit;
    } catch (PDOException $e) {
        die("Error during signup: " . $e->getMessage());
    }
}
?>

