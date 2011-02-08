#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class LoansTestCases(unittest.TestCase):

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

    def test_give_loan_to_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # give loan
        rv = self.app.post('/loan/give', data=dict(user=2, date="2011-02-06", deduct_from=1,
                                                   description="I give you money", amount=11.10), follow_redirects=True)
        assert 'Loan given' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;988.90</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;11.10</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;11.10</span>
                I give you money
            </p>
            <div class="date">to <a href="/loans/with/barunka">Barunka</a>
                2011-02-06</div>
        ''' in rv.data

    def test_edit_give_loan_from_private_to_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name="ING Direct", type="asset", balance=300.57),
                           follow_redirects=True)
        assert 'Account added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Radek"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # give loan
        rv = self.app.post('/loan/give', data=dict(user=2, date="2011-02-06", deduct_from=1,
                                                   description="I give you money", amount=11.10), follow_redirects=True)
        assert 'Loan given' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Giving Loan "I give you money"' in rv.data
        assert '<option value="2" selected>Barunka</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="1" selected>HSBC</option>' in rv.data
        assert '<input type=text name=amount value="11.1">' in rv.data

        # edit loan post
        rv = self.app.post('/loans/edit/1', data=dict(user=3, date="2011-02-06", deduct_from=2,
                                                      description="I rather give you money", amount=6.89),
                           follow_redirects=True)
        assert 'Loan edited' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Giving Loan "I rather give you money"' in rv.data
        assert '<option value="3" selected>Radek</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="2" selected>ING Direct</option>' in rv.data
        assert '<input type=text name=amount value="6.89">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;293.68</span>
            <a>ING Direct</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;6.89</span>
            Loaned to <a href="/loans/with/radek">Radek</a>
        ''' in rv.data
        assert 'Barunka' not in rv.data
        assert '<span class="amount"><strong>&pound;1,293.68</strong></span>' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;6.89</span>
                I rather give you money
            </p>
            <div class="date">to <a href="/loans/with/radek">Radek</a>
                2011-02-06</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/barunka">Barunka</a>' not in rv.data

    def test_get_loan_from_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # give loan
        rv = self.app.post('/loan/get', data=dict(user=2, date="2011-02-06", credit_to=1,
                                                   description="You give me money", amount=11.10), follow_redirects=True)
        assert 'Loan received' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,011.10</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
        <li class="red last">
            <span class="amount">&minus; &pound;11.10</span>
            Loaned from <a href="/loans/with/barunka">Barunka</a>
        </li>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;11.10</span>
                You give me money
            </p>
            <div class="date">from <a href="/loans/with/barunka">Barunka</a>
                2011-02-06</div>
        ''' in rv.data

    def test_edit_get_loan_from_private_to_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name="ING Direct", type="asset", balance=300.57),
                           follow_redirects=True)
        assert 'Account added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Radek"), follow_redirects=True)
        assert 'Private user added' in rv.data

        # give loan
        rv = self.app.post('/loan/get', data=dict(user=2, date="2011-02-06", credit_to=1,
                                                   description="You give me money", amount=11.10), follow_redirects=True)
        assert 'Loan received' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Getting Loan "You give me money"' in rv.data
        assert '<option value="2" selected>Barunka</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="1" selected>HSBC</option>' in rv.data
        assert '<input type=text name=amount value="11.1">' in rv.data

        # edit loan post
        rv = self.app.post('/loans/edit/1', data=dict(user=3, date="2011-02-06", credit_to=2,
                                                      description="You rather give me money", amount=6.89),
                           follow_redirects=True)
        assert 'Loan edited' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Getting Loan "You rather give me money"' in rv.data
        assert '<option value="3" selected>Radek</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="2" selected>ING Direct</option>' in rv.data
        assert '<input type=text name=amount value="6.89">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;307.46</span>
            <a>ING Direct</a>
        ''' in rv.data
        assert '''
        <li class="red last">
            <span class="amount">&minus; &pound;6.89</span>
            Loaned from <a href="/loans/with/radek">Radek</a>
        </li>
        ''' in rv.data
        assert 'Barunka' not in rv.data
        assert '<span class="amount"><strong>&pound;1,307.46</strong></span>' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;6.89</span>
                You rather give me money
            </p>
            <div class="date">from <a href="/loans/with/radek">Radek</a>
                2011-02-06</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/barunka">Barunka</a>' not in rv.data

    def test_give_loan_to_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Barclays", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # give loan
        rv = self.app.post('/loan/give', data=dict(user=2, date="2011-02-06", deduct_from=2,
                                                   description="I give you money", amount=11.10), follow_redirects=True)
        assert 'Loan given' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;988.90</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;11.10</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;11.10</span>
                I give you money
            </p>
            <div class="date">to <a href="/loans/with/barunka">Barunka</a>
                2011-02-06</div>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,011.10</span>
            <a>Barclays</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;11.10</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;11.10</span>
                I give you money
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-02-06</div>
        ''' in rv.data

    def test_get_loan_from_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Barclays", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # give loan
        rv = self.app.post('/loan/get', data=dict(user=2, date="2011-02-06", credit_to=2,
                                                   description="You give me money", amount=11.10), follow_redirects=True)
        assert 'Loan received' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,011.10</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
        <li class="red last">
            <span class="amount">&minus; &pound;11.10</span>
            Loaned from <a href="/loans/with/barunka">Barunka</a>
        </li>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;11.10</span>
                You give me money
            </p>
            <div class="date">from <a href="/loans/with/barunka">Barunka</a>
                2011-02-06</div>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;988.90</span>
            <a>Barclays</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;11.10</span>
            Loaned to <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;11.10</span>
                You give me money
            </p>
            <div class="date">to <a href="/loans/with/admin">Admin</a>
                2011-02-06</div>
        ''' in rv.data

    def test_edit_give_loan_from_normal_to_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Barclays", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # logout
        self.app.get('/logout', follow_redirects=True)

        # add normal user
        self.app.get('/test/create-user/Jára')

        # login
        self.app.post('/login', data=dict(username="jara", password="jara"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Měšec", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name="ING Direct", type="asset", balance=300.57),
                           follow_redirects=True)
        assert 'Account added' in rv.data

        # give loan
        rv = self.app.post('/loan/give', data=dict(user=2, date="2011-02-06", deduct_from=3,
                                                   description="I give you money", amount=11.10), follow_redirects=True)
        assert 'Loan given' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Giving Loan "I give you money"' in rv.data
        assert '<option value="2" selected>Barunka</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="3" selected>HSBC</option>' in rv.data
        assert '<input type=text name=amount value="11.1">' in rv.data

        # edit loan post
        rv = self.app.post('/loans/edit/1', data=dict(user=3, date="2011-02-06", deduct_from=4,
                                                      description="I rather give you money", amount=6.89),
                           follow_redirects=True)
        assert 'Loan edited' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Giving Loan "I rather give you money"' in rv.data
        assert '<option value="3" selected>Jára</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="4" selected>ING Direct</option>' in rv.data
        assert '<input type=text name=amount value="6.89">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;293.68</span>
            <a>ING Direct</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;6.89</span>
            Loaned to <a href="/loans/with/jara">Jára</a>
        ''' in rv.data
        assert 'Barunka' not in rv.data
        assert '<span class="amount"><strong>&pound;1,293.68</strong></span>' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;6.89</span>
                I rather give you money
            </p>
            <div class="date">to <a href="/loans/with/jara">Jára</a>
                2011-02-06</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/barunka">Barunka</a>' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>Barclays</a>
        ''' in rv.data
        assert 'Loaned from <a href="/loans/with/admin">Admin</a>' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<div class="date">from <a href="/loans/with/admin">Admin</a>' not in rv.data
        assert '<div class="date">to <a href="/loans/with/admin">Admin</a>' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="jara", password="jara"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,006.89</span>
            <a>Měšec</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;6.89</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;6.89</span>
                I rather give you money
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-02-06</div>
        ''' in rv.data

    def test_edit_get_loan_from_normal_to_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Barclays", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # logout
        self.app.get('/logout', follow_redirects=True)

        # add normal user
        self.app.get('/test/create-user/Jára')

        # login
        self.app.post('/login', data=dict(username="jara", password="jara"), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="Měšec", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # create account
        rv = self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)
        assert 'Account added' in rv.data

        # create account
        rv = self.app.post('/account/add', data=dict(name="ING Direct", type="asset", balance=300.57),
                           follow_redirects=True)
        assert 'Account added' in rv.data

        # give loan
        rv = self.app.post('/loan/get', data=dict(user=2, date="2011-02-06", credit_to=3,
                                                   description="You give me money", amount=11.10), follow_redirects=True)
        assert 'Loan received' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Getting Loan "You give me money"' in rv.data
        assert '<option value="2" selected>Barunka</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="3" selected>HSBC</option>' in rv.data
        assert '<input type=text name=amount value="11.1">' in rv.data

        # edit loan post
        rv = self.app.post('/loans/edit/1', data=dict(user=3, date="2011-02-06", credit_to=4,
                                                      description="You rather give me money", amount=6.89),
                           follow_redirects=True)
        assert 'Loan edited' in rv.data

        # edit loan get
        rv = self.app.get('/loans/edit/1', follow_redirects=True)
        assert 'Editing Getting Loan "You rather give me money"' in rv.data
        assert '<option value="3" selected>Jára</option>' in rv.data
        assert '<input type=text name=date value="2011-02-06">' in rv.data
        assert '<option value="4" selected>ING Direct</option>' in rv.data
        assert '<input type=text name=amount value="6.89">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;307.46</span>
            <a>ING Direct</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;6.89</span>
            Loaned from <a href="/loans/with/jara">Jára</a>
        ''' in rv.data
        assert 'Barunka' not in rv.data
        assert '<span class="amount"><strong>&pound;1,307.46</strong></span>' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&pound;6.89</span>
                You rather give me money
            </p>
            <div class="date">from <a href="/loans/with/jara">Jára</a>
                2011-02-06</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/barunka">Barunka</a>' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>Barclays</a>
        ''' in rv.data
        assert 'Loaned to <a href="/loans/with/admin">Admin</a>' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<div class="date">from <a href="/loans/with/admin">Admin</a>' not in rv.data
        assert '<div class="date">to <a href="/loans/with/admin">Admin</a>' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="jara", password="jara"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
            <span class="amount">&pound;993.11</span>
            <a>Měšec</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;6.89</span>
            Loaned to <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;6.89</span>
                You rather give me money
            </p>
            <div class="date">to <a href="/loans/with/admin">Admin</a>
                2011-02-06</div>
        ''' in rv.data