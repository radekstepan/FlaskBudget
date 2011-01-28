# setup
import budget
import unittest

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:////var/www/html/python/flask/budget/db/database.sqlite3.testing')
        self.app = budget.app.test_client()

    def test_main(self):
        # setup
        self.app.get('/test/create_admin')

        # TODO 1) test login
        rv = self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)
        assert 'You were logged in' in rv.data

        # cleanup
        self.app.get('/test/wipe_tables')

if __name__ == '__main__':
    unittest.main()