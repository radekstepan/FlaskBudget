#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class UsersTestCases(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:////var/www/html/python/flask/budget/db/database.sqlite3.testing')
        self.app = budget.app.test_client()

        # cleanup
        self.app.get('/test/wipe_tables')

        # setup
        self.app.get('/test/create_admin')

    def test_login(self):
        # login
        rv = self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)
        assert 'You were logged in' in rv.data

    def test_add_private_user(self):
        # login
        rv = self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data