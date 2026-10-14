import unittest
from unittest.mock import MagicMock, patch

import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

from app import app


class AuthTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db = MagicMock()
        self.cursor = self.db.cursor.return_value.__enter__.return_value
        self.mock_db = patch('app.get_db', return_value=self.db)
        self.mock_db.start()
        self.addCleanup(self.mock_db.stop)

    def post(self, path, **data):
        self.client.get('/login')
        with self.client.session_transaction() as session:
            data['csrf_token'] = session['csrf_token']
        return self.client.post(path, data=data)

    def test_pages_and_access_control(self):
        for path in ('/', '/register', '/static/style.css', '/static/script.js'):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/dashboard').status_code, 302)
        self.assertEqual(self.client.post('/logout').status_code, 400)

    def test_registration_hashes_password(self):
        response = self.post('/register', name='Tariq', email='TARIQ@example.com',
                             password='test-password', confirm='test-password')
        self.assertEqual(response.status_code, 302)
        params = self.cursor.execute.call_args.args[1]
        self.assertEqual(params[:2], ('Tariq', 'tariq@example.com'))
        self.assertTrue(check_password_hash(params[2], 'test-password'))
        self.db.commit.assert_called_once()

    def test_mismatch_rejected_by_server(self):
        response = self.post('/register', name='Tariq', email='t@example.com',
                             password='test-password', confirm='different')
        self.assertIn(b'Passwords do not match', response.data)
        self.cursor.execute.assert_not_called()

    def test_duplicate_email(self):
        self.cursor.execute.side_effect = pymysql.err.IntegrityError(1062, 'duplicate')
        response = self.post('/register', name='Tariq', email='t@example.com',
                             password='test-password', confirm='test-password')
        self.assertIn(b'already exists', response.data)
        self.db.rollback.assert_called_once()

    def test_login_logout(self):
        self.cursor.fetchone.return_value = {'id': 1, 'password_hash': generate_password_hash('test-password', method='pbkdf2:sha256:1000000')}
        bad = self.post('/login', email='t@example.com', password='wrong-password')
        self.assertIn(b'Invalid email or password', bad.data)
        good = self.post('/login', email='t@example.com', password='test-password', remember='on')
        self.assertEqual(good.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertEqual(session['user_id'], 1)
            self.assertTrue(session.permanent)
        self.cursor.fetchone.return_value = {'name': '<Tariq>', 'email': 't@example.com'}
        self.assertIn(b'&lt;Tariq&gt;', self.client.get('/dashboard').data)
        with self.client.session_transaction() as session:
            token = session['csrf_token']
        self.assertEqual(self.client.post('/logout', data={'csrf_token': token}).status_code, 302)
        self.assertEqual(self.client.get('/dashboard').status_code, 302)


if __name__ == '__main__':
    unittest.main()
