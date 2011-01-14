import os
import budget
import unittest
import tempfile

# db
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing

DEBUG = False
DATABASE = ''
def init_db(d):
        """Creates the database tables."""
        with closing(sqlite3.connect(DATABASE)) as db:
            with budget.app.open_resource('db/schema.sqlite') as f:
                db.cursor().executescript(f.read())
            db.commit()

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, DATABASE = tempfile.mkstemp()
        self.app = budget.app.test_client()
        init_db(self.db_fd)

    def tearDown(self):
        os.close(self.db_fd)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_add_account(self):
        # login
        rv = self.login('radek', 'radek')

        # add account
        rv = self.app.post('/account/add', data=dict(
            name='HSBC',
            type='asset',
            balance='1000'
            ), follow_redirects=True)

        # test dashboard
        rv = self.app.get('/')
        assert 'Dashboard' in rv.data
        assert '1000' in rv.data
        assert 'HSBC' in rv.data

if __name__ == '__main__':
    unittest.main()