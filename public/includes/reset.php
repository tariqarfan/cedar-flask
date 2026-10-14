<?php
declare(strict_types=1);
require_once __DIR__ . '/mailer.php';
function handle_forgot(): void {
    global $messages, $config;
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') return;
    rate_limit();
    $email = strtolower(trim(field('email')));
    if (strlen($email) > 254 || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400); $messages = ['Enter a valid email address.']; return;
    }
    $messages = ['If an account exists with that email, you’ll receive a password reset link shortly. Please check your spam folder too.'];
    $db = db();
    $statement = $db->prepare('SELECT id, name, email FROM cedar_users WHERE email = ?');
    $statement->execute([$email]); $user = $statement->fetch();
    if (!$user) return;
    $token = bin2hex(random_bytes(32)); $hash = hash('sha256', $token); $now = time();
    // Serializing by user row prevents concurrent requests from bypassing cooldown.
    $db->beginTransaction();
    try {
        $statement = $db->prepare('SELECT id FROM cedar_users WHERE id = ? FOR UPDATE'); $statement->execute([$user['id']]);
        $statement = $db->prepare('SELECT created_at FROM cedar_password_resets WHERE user_id = ?'); $statement->execute([$user['id']]);
        $created = $statement->fetchColumn();
        if ($created !== false && (int)$created > $now - 60) { $db->commit(); return; }
        $statement = $db->prepare('INSERT INTO cedar_password_resets (user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE token_hash = VALUES(token_hash), expires_at = VALUES(expires_at), created_at = VALUES(created_at)');
        $statement->execute([$user['id'], $hash, $now + 1800, $now]); $db->commit();
    } catch (Throwable $error) { if ($db->inTransaction()) $db->rollBack(); throw $error; }
    $base = rtrim($config['app_url'] ?? 'https://kabir.marmareen.com', '/');
    try { send_reset_email($user['email'], $user['name'], $base . '/reset-password.php?token=' . $token); }
    catch (Throwable $error) {
        // Keep public responses identical for registered and unregistered addresses.
        error_log('Cedar password-reset email could not be sent.');
        $statement = $db->prepare('DELETE FROM cedar_password_resets WHERE user_id = ? AND token_hash = ?'); $statement->execute([$user['id'], $hash]);
    }
}
function handle_reset(): void {
    global $messages, $resetToken, $resetValid;
    header('Referrer-Policy: no-referrer');
    $resetToken = $_SERVER['REQUEST_METHOD'] === 'POST' ? field('token') : (is_string($_GET['token'] ?? null) ? $_GET['token'] : '');
    $resetValid = false;
    if (!preg_match('/^[a-f0-9]{64}$/', $resetToken)) { $messages = ['This reset link is invalid or has expired. Request a new link.']; return; }
    $db = db(); $hash = hash('sha256', $resetToken);
    $statement = $db->prepare('SELECT user_id FROM cedar_password_resets WHERE token_hash = ? AND expires_at > ?'); $statement->execute([$hash, time()]);
    if (!$statement->fetch()) { $messages = ['This reset link is invalid or has expired. Request a new link.']; return; }
    $resetValid = true;
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') return;
    rate_limit();
    $password = field('password');
    if (strlen($password) < 8 || strlen($password) > 72) { http_response_code(400); $messages = ['Use a password between 8 and 72 bytes.']; return; }
    if ($password !== field('confirm')) { http_response_code(400); $messages = ['Passwords do not match.']; return; }
    $newHash = password_hash($password, PASSWORD_DEFAULT);
    $db->beginTransaction();
    try {
        $statement = $db->prepare('SELECT user_id FROM cedar_password_resets WHERE token_hash = ? AND expires_at > ? FOR UPDATE'); $statement->execute([$hash, time()]); $reset = $statement->fetch();
        if (!$reset) { $db->rollBack(); $resetValid = false; $messages = ['This reset link is invalid or has expired. Request a new link.']; return; }
        $statement = $db->prepare('UPDATE cedar_users SET password_hash = ? WHERE id = ?'); $statement->execute([$newHash, $reset['user_id']]);
        $statement = $db->prepare('DELETE FROM cedar_password_resets WHERE user_id = ?'); $statement->execute([$reset['user_id']]);
        $db->commit();
    } catch (Throwable $error) { if ($db->inTransaction()) $db->rollBack(); throw $error; }
    $_SESSION = ['messages' => ['Your password has been reset. Sign in with your new password.']]; session_regenerate_id(true);
    redirect('login.php');
}
