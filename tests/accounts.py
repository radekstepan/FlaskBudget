#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class AccountsTestCases(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:///:memory:')
        self.app = budget.app.test_client()

        # cleanup
        #self.app.get('/test/wipe-tables')

        # setup our test user
        self.app.get('/test/create-user/admin')

    def tearDown(self):
        # cleanup
        from db.database import Base, engine
        Base.metadata.drop_all(bind=engine)

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
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;666.65</span>
            <a>Privátní</a>
        ''' in rv.data

    def test_make_and_edit_transfer(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name=u"Privátní", type="asset", balance=666.65),
                           follow_redirects=True)

        # make account transfer
        self.app.post('/account/transfer', data=dict(date="2011-02-01", deduct_from=1, credit_to=2, amount=310.11),
                           follow_redirects=True)

        # make account transfer
        self.app.post('/account/transfer/edit/1', data=dict(date="2011-02-01", deduct_from=1, credit_to=3,
                                                            amount=412.65), follow_redirects=True)

        # make account transfer
        self.app.post('/account/transfer', data=dict(date="2011-02-01", deduct_from=2, credit_to=3, amount=14.7),
                           follow_redirects=True)

        # make account transfer
        self.app.post('/account/transfer/edit/1', data=dict(date="2011-02-01", deduct_from=3, credit_to=2,
                                                            amount=255.79), follow_redirects=True)

        # list them on account transfers page
        rv = self.app.get('/account-transfers', follow_redirects=True)
        assert '''
                From <a href="/account-transfers/with/privatni">Privátní</a>
                to <a href="/account-transfers/with/credit-card">Credit Card</a>
                <span class="amount">&pound;255.79</span>
        ''' in rv.data
        assert '''
                From <a href="/account-transfers/with/credit-card">Credit Card</a>
                to <a href="/account-transfers/with/privatni">Privátní</a>
                <span class="amount">&pound;14.70</span>
        ''' in rv.data

        # check out dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;241.09</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;425.56</span>
            <a>Privátní</a>
        ''' in rv.data
        