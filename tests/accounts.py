#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class AccountsTestCases(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:////var/www/html/python/flask/budget/db/database.sqlite3.testing')
        self.app = budget.app.test_client()

        # cleanup
        self.app.get('/test/wipe_tables')

        # setup
        self.app.get('/test/create_admin')

    def test_add_accounts(self):
        # login
        rv = self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name=u"Privátní", type="asset", balance=666.65),
                           follow_redirects=True)
        assert 'Account added' in rv.data