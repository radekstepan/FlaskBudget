#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class IncomeTestCases(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:////var/www/html/python/flask/budget/db/database.sqlite3.testing')
        self.app = budget.app.test_client()

        # cleanup
        self.app.get('/test/wipe-tables')

        # setup our test user
        self.app.get('/test/create-user/admin')

    def test_add_income(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create income category
        rv = self.app.post('/income/category/add', data=dict(name="Salary"), follow_redirects=True)
        assert 'Income category added' in rv.data

        # add income
        rv = self.app.post('/income/add', data=dict(
                date="2011-01-28", category=1, description="January", credit_to=1, amount=500
                ), follow_redirects=True)
        assert 'Income added' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,500</span>
            <a>HSBC</a>
        ''' in rv.data

    def test_edit_income(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create income category
        self.app.post('/income/category/add', data=dict(name="Salary"), follow_redirects=True)

        # add income
        self.app.post('/income/add', data=dict(
                date="2011-01-28", category=1, description="January", credit_to=1, amount=500
                ), follow_redirects=True)

        # create income category
        rv = self.app.post('/income/category/add', data=dict(name="eBay Sales"), follow_redirects=True)
        assert 'Income category added' in rv.data

        # edit income get
        rv = self.app.get('income/edit/1')
        assert '<header><h1>Edit Income "January"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-28">' in rv.data
        assert '<option value="1" selected="selected">Salary</option>' in rv.data
        assert '<input type=text name=description value="January">' in rv.data
        assert '<option value="1" selected="selected">HSBC</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data

        # edit income post
        rv = self.app.post('/income/edit/1', data=dict(date="2011-01-29", category=2, credit_to=2, amount=1000,
                                                       description="Sale of PC"), follow_redirects=True)
        assert 'Income edited' in rv.data
        assert '<header><h1>Edit Income "Sale of PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">eBay Sales</option>' in rv.data
        assert '<input type=text name=description value="Sale of PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="1000">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;1,000</span>
            <a>Credit Card</a>
        ''' in rv.data