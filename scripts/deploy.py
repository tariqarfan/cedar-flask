"""Upload public/ via explicit FTPS. Credentials come only from environment."""
import ftplib
import os
from pathlib import Path
import ssl

for name in ('FTP_SERVER', 'FTP_USERNAME', 'FTP_PASSWORD', 'FTP_DIRECTORY'):
    if not os.environ.get(name):
        raise SystemExit('Missing deployment secret: ' + name)
root = Path('public')
ftp = ftplib.FTP_TLS(context=ssl.create_default_context(), timeout=30)
ftp.connect(os.environ['FTP_SERVER'], int(os.getenv('FTP_PORT', '21')))
# Hostinger's shared FTP certificate uses hstgr.io rather than the server IP.
# Certificate chain and hostname verification remain enabled.
ftp.host = os.getenv('FTP_TLS_HOSTNAME') or os.environ['FTP_SERVER']
ftp.login(os.environ['FTP_USERNAME'], os.environ['FTP_PASSWORD'])
ftp.prot_p()
# This path is relative to the FTP account's login directory; never guess it.
ftp.cwd(os.environ['FTP_DIRECTORY'])
base = ftp.pwd()
# Upload access protections before any configuration or application files.
paths = sorted((p for p in root.rglob('*') if p.is_file() and p.name != 'config.example.php'), key=lambda p: (p.name != '.htaccess', str(p)))
for path in paths:
    relative = path.relative_to(root)
    ftp.cwd(base)
    for directory in relative.parts[:-1]:
        try:
            ftp.cwd(directory)
        except ftplib.error_perm:
            ftp.mkd(directory)
            ftp.cwd(directory)
    temporary = relative.name + '.upload'
    with path.open('rb') as source:
        ftp.storbinary('STOR ' + temporary, source)
    ftp.rename(temporary, relative.name)
    print('Uploaded', relative)
ftp.quit()
