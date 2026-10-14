<?php
declare(strict_types=1);
function verify_password(string $password, string $stored): bool {
    if (!str_starts_with($stored, 'pbkdf2:sha256:')) return password_verify($password, $stored);
    $parts = explode('$', $stored);
    if (count($parts) !== 3 || !preg_match('/^pbkdf2:sha256:(\d+)$/', $parts[0], $match) || !preg_match('/^[a-f0-9]{64}$/i', $parts[2])) return false;
    $rounds = (int)$match[1];
    return $rounds > 0 && $rounds <= 2000000 && hash_equals(strtolower($parts[2]), hash_pbkdf2('sha256', $password, $parts[1], $rounds, 64));
}
