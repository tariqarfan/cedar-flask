<?php
declare(strict_types=1);
ini_set('display_errors', '0');
$configFile = __DIR__ . '/config.php';
if (!is_file($configFile)) { http_response_code(503); exit('App configuration is missing. See the deployment instructions.'); }
$config = require $configFile;
$isHttps = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
ini_set('session.use_strict_mode', '1');
ini_set('session.gc_maxlifetime', '604800');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => (bool)($config['cookie_secure'] ?? $isHttps), 'httponly' => true, 'samesite' => 'Lax']);
session_start();
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: strict-origin-when-cross-origin');
header("Content-Security-Policy: default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'");
header('Cache-Control: no-store');
set_exception_handler(function (Throwable $error): void {
    error_log('Cedar request failed: ' . get_class($error) . ' code ' . $error->getCode());
    http_response_code(503);
    echo 'Unable to process this request. Please check the database configuration or try again later.';
});
if (isset($_SESSION['expires']) && time() > $_SESSION['expires']) { $_SESSION = []; session_regenerate_id(true); }
function e(string $value): string { return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function csrf_token(): string { return $_SESSION['csrf'] ??= bin2hex(random_bytes(32)); }
function field(string $name): string { return isset($_POST[$name]) && is_string($_POST[$name]) ? $_POST[$name] : ''; }
function redirect(string $page): never { header('Location: ' . $page); exit; }
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !hash_equals(csrf_token(), field('csrf_token'))) {
    http_response_code(400); exit('Your form expired. Reload the page and try again.');
}
function db(): PDO {
    global $config;
    static $db = null;
    if ($db) return $db;
    $db = new PDO('mysql:host=' . $config['db_host'] . ';port=' . ($config['db_port'] ?? 3306) . ';dbname=' . $config['db_name'] . ';charset=utf8mb4', $config['db_user'], $config['db_password'], [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::ATTR_EMULATE_PREPARES => false]);
    $db->exec('CREATE TABLE IF NOT EXISTS cedar_users (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(254) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    $db->exec('CREATE TABLE IF NOT EXISTS cedar_login_limits (ip_hash CHAR(64) PRIMARY KEY, attempts INT NOT NULL, window_start BIGINT NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    $db->exec('CREATE TABLE IF NOT EXISTS cedar_password_resets (user_id BIGINT UNSIGNED PRIMARY KEY, token_hash CHAR(64) NOT NULL UNIQUE, expires_at BIGINT NOT NULL, created_at BIGINT NOT NULL, INDEX reset_expiry (expires_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    return $db;
}
function rate_limit(): void {
    $db = db();
    $ip = hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'unknown');
    $now = time();
    $statement = $db->prepare('INSERT INTO cedar_login_limits (ip_hash, attempts, window_start) VALUES (?, 1, ?) ON DUPLICATE KEY UPDATE attempts = IF(window_start < ?, 1, attempts + 1), window_start = IF(window_start < ?, VALUES(window_start), window_start)');
    $statement->execute([$ip, $now, $now - 900, $now - 900]);
    $statement = $db->prepare('SELECT attempts FROM cedar_login_limits WHERE ip_hash = ?');
    $statement->execute([$ip]);
    if ((int)$statement->fetchColumn() > 30) { http_response_code(429); exit('Too many attempts. Try again in 15 minutes.'); }
    if (random_int(1, 100) === 1) { $statement = $db->prepare('DELETE FROM cedar_login_limits WHERE window_start < ?'); $statement->execute([$now - 900]); }
}
require __DIR__ . '/password.php';
require __DIR__ . '/reset.php';
$messages = $_SESSION['messages'] ?? [];
unset($_SESSION['messages']);
function handle_login(): void {
    global $messages;
    if (isset($_SESSION['user_id'])) redirect('dashboard.php');
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') return;
    rate_limit();
    $password = field('password');
    $email = strtolower(trim(field('email')));
    $user = false;
    if (strlen($password) <= 128 && strlen($email) <= 254) {
        $statement = db()->prepare('SELECT id, password_hash FROM cedar_users WHERE email = ?');
        $statement->execute([$email]); $user = $statement->fetch();
    }
    if (!$user || !verify_password($password, $user['password_hash'])) { http_response_code(401); $messages = ['Invalid email or password.']; return; }
    if (strlen($password) <= 72 && (str_starts_with($user['password_hash'], 'pbkdf2:') || password_needs_rehash($user['password_hash'], PASSWORD_DEFAULT))) {
        $statement = db()->prepare('UPDATE cedar_users SET password_hash = ? WHERE id = ?');
        $user['password_hash'] = password_hash($password, PASSWORD_DEFAULT);
        $statement->execute([$user['password_hash'], $user['id']]);
    }
    session_regenerate_id(true); $_SESSION = ['user_id' => $user['id'], 'auth_hash' => hash('sha256', $user['password_hash']), 'expires' => time() + (field('remember') === 'on' ? 604800 : 86400)];
    if (field('remember') === 'on') { $params = session_get_cookie_params(); setcookie(session_name(), session_id(), ['expires' => time() + 604800, 'path' => $params['path'], 'secure' => $params['secure'], 'httponly' => true, 'samesite' => 'Lax']); }
    redirect('dashboard.php');
}
function handle_register(): void {
    global $messages;
    if (isset($_SESSION['user_id'])) redirect('dashboard.php');
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') return;
    rate_limit();
    $name = trim(field('name')); $email = strtolower(trim(field('email'))); $password = field('password');
    $error = '';
    if (!$name || strlen($name) > 100) $error = 'Enter a name between 1 and 100 bytes.';
    elseif (strlen($email) > 254 || !filter_var($email, FILTER_VALIDATE_EMAIL)) $error = 'Enter a valid email address.';
    elseif (strlen($password) < 8 || strlen($password) > 72) $error = 'Use a password between 8 and 72 bytes.';
    elseif ($password !== field('confirm')) $error = 'Passwords do not match.';
    if ($error) { http_response_code(400); $messages = [$error]; return; }
    try {
        $statement = db()->prepare('INSERT INTO cedar_users (name, email, password_hash) VALUES (?, ?, ?)');
        $statement->execute([$name, $email, password_hash($password, PASSWORD_DEFAULT)]);
    } catch (PDOException $error) {
        if (($error->errorInfo[1] ?? null) !== 1062) throw $error;
        http_response_code(409); $messages = ['An account with that email already exists.']; return;
    }
    $_SESSION['messages'] = ['Account created. Sign in to continue.']; redirect('login.php');
}
function handle_dashboard(): void {
    global $user;
    if (!isset($_SESSION['user_id'])) redirect('login.php');
    $statement = db()->prepare('SELECT name, email, password_hash FROM cedar_users WHERE id = ?');
    $statement->execute([$_SESSION['user_id']]); $user = $statement->fetch();
    if (!$user || !hash_equals($_SESSION['auth_hash'] ?? '', hash('sha256', $user['password_hash']))) { $_SESSION = []; session_regenerate_id(true); redirect('login.php'); }
}
