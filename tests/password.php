<?php
require __DIR__ . '/../public/includes/password.php';
$password = 'test-password';
$salt = 'existing-flask-salt';
$legacy = 'pbkdf2:sha256:1000000$' . $salt . '$' . hash_pbkdf2('sha256', $password, $salt, 1000000, 64);
foreach ([password_hash($password, PASSWORD_DEFAULT), $legacy] as $hash) {
    if (!verify_password($password, $hash) || verify_password('wrong-password', $hash)) throw new RuntimeException('Password verification failed.');
}
if (verify_password($password, 'pbkdf2:sha256:999999999$x$bad')) throw new RuntimeException('Invalid hash accepted.');
echo "PHP and Flask-compatible password checks passed.\n";
