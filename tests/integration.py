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

php = os.environ.get('PHP_BIN', 'php')
config_path = Path('public/includes/config.php')
original = config_path.read_bytes() if config_path.exists() else None
config = {'db_host': os.getenv('DB_HOST', '127.0.0.1'), 'db_port': int(os.getenv('DB_PORT', '8889')), 'db_name': os.getenv('DB_NAME', 'tariq'), 'db_user': os.getenv('DB_USER', 'tariq'), 'db_password': os.environ['DB_PASSWORD'], 'cookie_secure': False}
payload = base64.b64encode(json.dumps(config).encode()).decode()
config_path.write_text("<?php return json_decode(base64_decode('" + payload + "'), true);")
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
    print('PHP/MySQL registration, duplicate email, login, escaping, CSRF, dashboard, and logout passed.')
finally:
    server.terminate()
    server.wait(timeout=10)
    subprocess.run([php, '-r', "$c=require 'public/includes/config.php';$d=new PDO('mysql:host='.$c['db_host'].';port='.$c['db_port'].';dbname='.$c['db_name'],$c['db_user'],$c['db_password']);$s=$d->prepare('DELETE FROM cedar_users WHERE email=?');$s->execute([$argv[1]]);", email], check=True)
    if original is None: config_path.unlink(missing_ok=True)
    else: config_path.write_bytes(original)
