"""Exercise PHP pages against local/test MySQL without changing deployment config."""
import base64
import http.cookiejar
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import socketserver
import threading
from email import policy
from email.parser import BytesParser
from queue import Queue

mailbox = Queue()
class SMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 test SMTP ready\r\n')
        while line := self.rfile.readline():
            command = line.decode().strip().upper()
            if command.startswith('EHLO'):
                self.wfile.write(b'250-test\r\n250 AUTH PLAIN\r\n')
            elif command.startswith('AUTH'):
                self.wfile.write(b'334 \r\n')
                self.rfile.readline()
                self.wfile.write(b'235 Authenticated\r\n')
            elif command == 'DATA':
                self.wfile.write(b'354 Send message\r\n')
                lines = []
                while (part := self.rfile.readline()) != b'.\r\n':
                    if not part: return
                    lines.append(part)
                mailbox.put(BytesParser(policy=policy.default).parsebytes(b''.join(lines)))
                self.wfile.write(b'250 Accepted\r\n')
            elif command == 'QUIT': self.wfile.write(b'221 Bye\r\n'); return
            else: self.wfile.write(b'250 OK\r\n')
smtp = socketserver.ThreadingTCPServer(('127.0.0.1', 0), SMTPHandler)
threading.Thread(target=smtp.serve_forever, daemon=True).start()
php = os.environ.get('PHP_BIN', 'php')
config_path = Path('public/includes/config.php')
original = config_path.read_bytes() if config_path.exists() else None
config = {'db_host': os.getenv('DB_HOST', '127.0.0.1'), 'db_port': int(os.getenv('DB_PORT', '8889')), 'db_name': os.getenv('DB_NAME', 'tariq'), 'db_user': os.getenv('DB_USER', 'tariq'), 'db_password': os.environ['DB_PASSWORD'], 'cookie_secure': False}
config.update(smtp_host='127.0.0.1', smtp_port=smtp.server_address[1], smtp_security='', smtp_username='sender@example.com', smtp_password='test-only', app_url='https://reset.example.com')
payload = base64.b64encode(json.dumps(config).encode()).decode()
config_path.write_text("<?php return json_decode(base64_decode('" + payload + "'), true);")
subprocess.run([php, '-r', "$c=require 'public/includes/config.php';$d=new PDO('mysql:host='.$c['db_host'].';port='.$c['db_port'].';dbname='.$c['db_name'],$c['db_user'],$c['db_password']);$d->exec('CREATE TABLE IF NOT EXISTS cedar_login_limits (ip_hash CHAR(64) PRIMARY KEY, attempts INT NOT NULL, window_start BIGINT NOT NULL)');$s=$d->prepare('DELETE FROM cedar_login_limits WHERE ip_hash=?');$s->execute([hash('sha256','127.0.0.1')]);"], check=True)
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
server = subprocess.Popen([php, '-S', f'127.0.0.1:{port}', '-t', 'public'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
base = f'http://127.0.0.1:{port}'
email = f'php-test-{time.time_ns()}@example.com'
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(page, data=None):
    try:
        with client.open(base + '/' + page, None if data is None else urllib.parse.urlencode(data).encode(), timeout=10) as response:
            return response.status, response.read().decode(), response.url
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(), error.url
def token(html):
    return re.search(r'name="csrf_token" value="([a-f0-9]+)"', html)[1]
try:
    for _ in range(50):
        try: request('login.php'); break
        except OSError: time.sleep(.1)
    status, html, _ = request('register.php')
    assert status == 200
    csrf = token(html)
    form = dict(name='Test <User>', email=email, password='test-password', confirm='test-password', csrf_token=csrf)
    assert request('register.php', {**form, 'confirm': 'mismatch'})[0] == 400
    status, html, _ = request('register.php', form)
    assert status == 200 and 'Account created' in html
    assert request('register.php', form)[0] == 409
    assert request('login.php', dict(email=email, password='wrong', csrf_token=csrf))[0] == 401
    status, html, url = request('login.php', dict(email=email, password='test-password', csrf_token=csrf))
    assert status == 200 and url.endswith('dashboard.php') and 'Test &lt;User&gt;' in html
    assert 'current-time' in html
    assert request('logout.php', {'csrf_token': 'bad-token'})[0] == 400
    assert request('logout.php', {'csrf_token': token(html)})[2].endswith('login.php')
    assert request('dashboard.php')[2].endswith('login.php')
    csrf = token(request('login.php')[1])
    assert request('login.php', {'email': email, 'password': 'test-password', 'csrf_token': csrf})[2].endswith('dashboard.php')
    old_client = client
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    # Unknown accounts receive the same message, with no mail sent.
    status, html, _ = request('forgot-password.php')
    csrf = token(html)
    status, unknown, _ = request('forgot-password.php', {'email': 'unknown@example.com', 'csrf_token': csrf})
    assert status == 200 and 'If an account exists' in unknown and mailbox.empty()
    status, known, _ = request('forgot-password.php', {'email': email, 'csrf_token': csrf})
    assert status == 200 and 'If an account exists' in known
    message = mailbox.get(timeout=3)
    assert message['Subject'] == 'Reset your Cedar password'
    plain = message.get_body(preferencelist=('plain',)).get_content()
    themed = message.get_body(preferencelist=('html',)).get_content()
    assert '#12316b' in themed and 'Test &lt;User&gt;' in themed
    reset_token = re.search(r'https://reset.example.com/reset-password.php\?token=([a-f0-9]{64})', plain)[1]
    request('forgot-password.php', {'email': email, 'csrf_token': csrf})
    assert mailbox.empty(), 'Account cooldown must prevent repeated emails'
    assert 'invalid or has expired' in request('reset-password.php?token=bad-token')[1]
    reset_page = 'reset-password.php?token=' + reset_token
    status, html, _ = request(reset_page)
    csrf = token(html)
    assert request('reset-password.php', {'token': reset_token, 'csrf_token': csrf, 'password': 'new-password', 'confirm': 'mismatch'})[0] == 400
    status, html, _ = request('reset-password.php', {'token': reset_token, 'csrf_token': csrf, 'password': 'new-password', 'confirm': 'new-password'})
    assert status == 200 and 'Your password has been reset' in html
    assert 'invalid or has expired' in request(reset_page)[1], 'Reset tokens must be single-use'
    reset_client = client
    client = old_client
    assert request('dashboard.php')[2].endswith('login.php'), 'Reset must invalidate existing sign-ins'
    client = reset_client
    csrf = token(request('login.php')[1])
    assert request('login.php', {'email': email, 'password': 'test-password', 'csrf_token': csrf})[0] == 401
    status, html, url = request('login.php', {'email': email, 'password': 'new-password', 'csrf_token': csrf})
    assert url.endswith('dashboard.php')
    subprocess.run([php, '-r', "$c=require 'public/includes/config.php';$d=new PDO('mysql:host='.$c['db_host'].';port='.$c['db_port'].';dbname='.$c['db_name'],$c['db_user'],$c['db_password']);$s=$d->prepare('INSERT INTO cedar_password_resets (user_id,token_hash,expires_at,created_at) SELECT id, ?, ?, ? FROM cedar_users WHERE email=?');$s->execute([hash('sha256',str_repeat('a',64)),time()-1,time()-1801,$argv[1]]);", email], check=True)
    assert 'invalid or has expired' in request('reset-password.php?token=' + 'a' * 64)[1]
    print('Expired tokens and existing-session invalidation passed.')
    print('Reset email theme, account privacy, cooldown, CSRF, password validation, token reuse, and new-password login passed.')
    print('PHP/MySQL registration, duplicate email, login, escaping, CSRF, dashboard, and logout passed.')
finally:
    smtp.shutdown()
    smtp.server_close()
    server.terminate()
    server.wait(timeout=10)
    subprocess.run([php, '-r', "$c=require 'public/includes/config.php';$d=new PDO('mysql:host='.$c['db_host'].';port='.$c['db_port'].';dbname='.$c['db_name'],$c['db_user'],$c['db_password']);$s=$d->prepare('DELETE r FROM cedar_password_resets r JOIN cedar_users u ON r.user_id=u.id WHERE u.email=?');$s->execute([$argv[1]]);$s=$d->prepare('DELETE FROM cedar_users WHERE email=?');$s->execute([$argv[1]]);", email], check=True)
    if original is None: config_path.unlink(missing_ok=True)
    else: config_path.write_bytes(original)
