import os
import re
import secrets
from datetime import timedelta

import click
import pymysql
from dotenv import load_dotenv
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ['SECRET_KEY'],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    MAX_CONTENT_LENGTH=16 * 1024,
)


def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '8889')),
            user=os.getenv('DB_USER', 'tariq'),
            password=os.environ['DB_PASSWORD'],
            database=os.getenv('DB_NAME', 'tariq'),
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5,
        )
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db:
        db.close()


@app.cli.command('init-db')
def init_db():
    """Create the users table in the configured existing MySQL database."""
    with get_db().cursor() as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS cedar_users (
            id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(254) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
    get_db().commit()
    click.echo('Database initialized: cedar_users table is ready.')


def csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


app.jinja_env.globals['csrf_token'] = csrf_token


@app.before_request
def protect_forms():
    if request.method == 'POST':
        expected = session.get('csrf_token', '')
        if not expected or not secrets.compare_digest(expected, request.form.get('csrf_token', '')):
            return 'Your form expired. Reload the page and try again.', 400


@app.errorhandler(pymysql.MySQLError)
def database_error(error):
    app.logger.error('MySQL request failed (code %s)', error.args[0] if error.args else 'unknown')
    return 'Database unavailable. Check MySQL settings and run flask --app app init-db.', 503


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        with get_db().cursor() as cursor:
            cursor.execute('SELECT id, password_hash FROM cedar_users WHERE email = %s', (email,))
            user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session.permanent = request.form.get('remember') == 'on'
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not 1 <= len(name) <= 100:
            flash('Enter a name between 1 and 100 characters.')
        elif len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            flash('Enter a valid email address.')
        elif not 8 <= len(password) <= 128:
            flash('Use a password between 8 and 128 characters.')
        elif password != request.form.get('confirm', ''):
            flash('Passwords do not match.')
        else:
            db = get_db()
            try:
                with db.cursor() as cursor:
                    cursor.execute('INSERT INTO cedar_users (name, email, password_hash) VALUES (%s, %s, %s)',
                                   (name, email, generate_password_hash(password, method='pbkdf2:sha256:1000000')))
                db.commit()
            except pymysql.err.IntegrityError as error:
                db.rollback()
                if error.args[0] != 1062:
                    raise
                flash('An account with that email already exists.')
            else:
                flash('Account created. Sign in to continue.')
                return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    with get_db().cursor() as cursor:
        cursor.execute('SELECT name, email FROM cedar_users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
    if not user:
        session.clear()
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)


@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
