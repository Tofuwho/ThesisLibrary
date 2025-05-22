<?php
session_start();
require '../db/connection.php';

$usernameOrEmail = $_POST['username'] ?? '';
$password = $_POST['password'] ?? '';

$sql = "SELECT * FROM users WHERE username = :username OR email = :email";
$stmt = $pdo->prepare($sql);
$stmt->execute([
    'username' => $usernameOrEmail,
    'email' => $usernameOrEmail
]);
$user = $stmt->fetch();

if ($user && password_verify($password, $user['password'])) {
    $_SESSION['user'] = $user['username']; // Changed this to match landing-header.php
    $_SESSION['role'] = $user['role'];
    echo 'success'; // Since you're using fetch(), do not redirect here
    exit;
}

echo "Invalid credentials.";
?>
