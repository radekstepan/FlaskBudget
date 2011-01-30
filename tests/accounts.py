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
        self.app.get('/test/wipe-tables')

        # setup our test user
        self.app.get('/test/create-user/admin')

    def test_add_accounts(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

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

        # list them on account transfers page
        rv = self.app.get('/account-transfers', follow_redirects=True)
        assert '<a href="/account-transfers/with/hsbc">HSBC</a>' in rv.data
        assert '<a href="/account-transfers/with/privatni">Privátní</a>' in rv.data
        assert '<li class="last"><a href="/account-transfers/with/credit-card">Credit Card</a>' in rv.data

        # check out dashboard
        rv = self.app.get('/', follow_redirects=True)
        assert '''
            <span class="amount">&pound;1,000</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
        <li class="green last">
            <span class="amount">&pound;666.65</span>
            <a>Privátní</a>
        </li>
        ''' in rv.data