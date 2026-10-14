<?php
declare(strict_types=1);
require_once __DIR__ . '/phpmailer/Exception.php';
require_once __DIR__ . '/phpmailer/PHPMailer.php';
require_once __DIR__ . '/phpmailer/SMTP.php';

function reset_email_html(string $name, string $link): string {
    $name = htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    $link = htmlspecialchars($link, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    return <<<HTML
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reset your Cedar password</title></head>
<body style="margin:0;background:#f5f8ff;font-family:Arial,sans-serif;color:#203653;">
<div style="display:none;max-height:0;overflow:hidden;">Your secure password reset link expires in 30 minutes.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border:1px solid #d9e2f1;border-radius:12px;overflow:hidden;">
<tr><td style="background:#12316b;padding:28px 32px;color:#ffffff;font-size:28px;font-weight:bold;">c. &nbsp;cedar</td></tr>
<tr><td style="padding:32px;"><p style="color:#607ba4;font-size:11px;letter-spacing:2px;">YOUR ACCOUNT, PROTECTED</p>
<h1 style="font-size:28px;line-height:1.3;margin:16px 0;">A fresh start for your password.</h1>
<p style="font-size:15px;line-height:1.7;">Hi {$name},</p>
<p style="font-size:15px;line-height:1.7;color:#61738e;">We received a request to reset your Cedar password. Use the button below to choose a new one.</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td bgcolor="#2563eb" style="border-radius:7px;"><a href="{$link}" style="display:inline-block;padding:15px 24px;color:#ffffff;text-decoration:none;font-size:15px;font-weight:bold;">Reset my password &rarr;</a></td></tr></table>
<p style="font-size:13px;line-height:1.7;color:#61738e;margin-top:24px;">This link expires in <strong>30 minutes</strong> and can only be used once. If you didn’t request a reset, you can ignore this email. Your password will stay the same.</p>
<hr style="border:0;border-top:1px solid #d9e2f1;margin:24px 0;">
<p style="font-size:12px;color:#61738e;">Button not working? Copy this link into your browser:</p><p style="font-size:12px;line-height:1.6;word-break:break-all;"><a href="{$link}" style="color:#2563eb;">{$link}</a></p>
</td></tr><tr><td style="padding:20px 32px;background:#eaf2ff;color:#61738e;font-size:12px;">Cedar &middot; A simpler way forward.</td></tr></table></td></tr></table></body></html>
HTML;
}
function send_reset_email(string $email, string $name, string $link): void {
    global $config;
    $mail = new PHPMailer\PHPMailer\PHPMailer(true);
    $mail->isSMTP();
    $mail->Host = $config['smtp_host'] ?? 'smtp.gmail.com';
    $mail->Port = (int)($config['smtp_port'] ?? 587);
    $mail->SMTPAuth = true;
    $mail->Username = $config['smtp_username'] ?? '';
    $mail->Password = $config['smtp_password'] ?? '';
    $mail->SMTPSecure = $config['smtp_security'] ?? PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_STARTTLS;
    $mail->SMTPAutoTLS = $mail->SMTPSecure !== '';
    $mail->Timeout = 15;
    $mail->CharSet = 'UTF-8';
    $mail->setFrom($mail->Username, 'Cedar');
    $mail->addAddress($email, $name);
    $mail->Subject = 'Reset your Cedar password';
    $mail->isHTML(true);
    $mail->Body = reset_email_html($name, $link);
    $mail->AltBody = "Hi {$name},\n\nReset your Cedar password using this link:\n{$link}\n\nThis link expires in 30 minutes and can only be used once. If you did not request this reset, ignore this email. Your password will stay the same.\n\nCedar — A simpler way forward.";
    $mail->send();
}
