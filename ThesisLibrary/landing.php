<?php
// Start session if not already started
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$error = '';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
  $username = $_POST['username'] ?? '';
  $password = $_POST['password'] ?? '';

  // TEMPORARY: Replace with database authentication
  $users = [
    'student1' => ['password' => 'studentpass', 'role' => 'student'],
    'admin1' => ['password' => 'adminpass', 'role' => 'admin'],
  ];

  if (isset($users[$username]) && $users[$username]['password'] === $password) {
    $_SESSION['user'] = $username;
    $_SESSION['role'] = $users[$username]['role'];
    header("Location: " . ($users[$username]['role'] === 'admin' ? 'admin/dashboard.php' : 'student/dashboard.php'));
    exit;
  } else {
    $error = 'Invalid credentials.';
  }
}
?>

<?php include 'includes/landing-header.php'; ?>

<section class="hero-section">
    <div class="hero-overlay">
        <div class="hero-content">
            <h1>Welcome to Thesis Library</h1>
            <p>Discover, explore, and contribute to our growing collection of academic research</p>
            <a href="index.php" class="cta-button">Explore Theses</a>
        </div>
    </div>
</section>

<!-- Login Modal -->
<div id="authModal" class="auth-modal">
    <div class="auth-container" id="auth-container">
        <span id="closeModal" class="close-modal">&times;</span>
        <div class="form-container sign-up-container">
            <form method="POST" action="signup.php">
                <h2>Create Account</h2>
                
                <label for="signup_username">Username</label>
                <input type="text" id="signup_username" name="signup_username" placeholder="Username" required>
                
                <label for="signup_email">Email</label>
                <input type="email" id="signup_email" name="signup_email" placeholder="Email" required>
                
                <label for="signup_password">Password</label>
                <input type="password" id="signup_password" name="signup_password" placeholder="Password" required>
                
                <button type="submit">Sign Up</button>
            </form>
        </div>
        <div class="form-container sign-in-container">
            <form method="POST" action="landing.php">
                <h2>Login to Thesis Library</h2>
                <?php if ($error): ?>
                    <p class="error"><?php echo $error; ?></p>
                <?php endif; ?>
                
                <label for="username">Username or Email</label>
                <input type="text" id="username" name="username" placeholder="Username or Email" required>
                
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Password" required>
                
                <button type="submit">Login</button>
            </form>
        </div>
        <div class="overlay-container">
            <div class="overlay">
                <div class="overlay-panel overlay-left">
                    <h2>Welcome Back!</h2>
                    <p>To keep connected, please login with your personal info</p>
                    <button class="ghost" id="signIn">Sign In</button>
                </div>
                <div class="overlay-panel overlay-right">
                    <h2>Hello, Scholar!</h2>
                    <p>Enter your details and start your thesis journey</p>
                    <button class="ghost" id="signUp">Sign Up</button>
                </div>
            </div>
        </div>
    </div>
</div>

<?php include 'includes/landing-footer.php'; ?>