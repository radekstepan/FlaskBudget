#!/usr/bin/python
# -*- coding: utf -*-

# setup
import budget
import unittest

class ExpensesTestCases(unittest.TestCase):

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

    def test_add_simple_expense(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        rv = self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)
        assert 'Expense category added' in rv.data

        # add expense
        rv = self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20), follow_redirects=True)
        assert 'Expense added' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;20.00</span>
                Tesco in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;980.00</span>
            <a>HSBC</a>
        ''' in rv.data

    def test_edit_simple_expense_to_simple(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # edit expense get
        rv = self.app.get('expense/edit/1')
        assert '<header><h1>Edit Expense "Tesco"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-28">' in rv.data
        assert '<option value="1" selected="selected">Shopping</option>' in rv.data
        assert '<input type=text name=description value="Tesco">' in rv.data
        assert '<option value="1" selected="selected">HSBC</option>' in rv.data
        assert '<input type=text name=amount value="20">' in rv.data

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC"), follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data

    def test_add_shared_expense_with_private(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # create expense category
        rv = self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)
        assert 'Expense category added' in rv.data

        # add expense
        rv = self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)
        assert 'Expense added' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;980.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;10.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

    def test_add_shared_expense_with_normal(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # add expense
        rv = self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)
        assert 'Expense added' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;980.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;10.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;10.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the expenses listing
        rv = self.app.get('/expenses', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
        <li class="red last">
            <p>
                <span class="amount">&pound;10.00</span>
                Tesco
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-01-28</div>
        ''' in rv.data

    def test_edit_shared_expense_with_normal_from_their_perspective(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Groceries"), follow_redirects=True)

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Groceries"), follow_redirects=True)

        # add expense
        rv = self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=3, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)
        assert 'Expense added' in rv.data

        # edit expense post, changing desc and category
        self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=4, deduct_from=1, amount=20,
                                                   description="Sainsbury's", is_shared=True, split=50, user=2),
                      follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Sainsbury&#39;s in <a href="/expenses/in/groceries">Groceries</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;980.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;10.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;10.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the expenses listing
        rv = self.app.get('/expenses', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Tesco in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
        <li class="red last">
            <p>
                <span class="amount">&pound;10.00</span>
                Tesco
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-01-29</div>
        ''' in rv.data

        # edit expense from our perspective as a "pass_thru" expense
        rv = self.app.post('/expense/edit/2', data=dict(category=1, description="Sainsbury's"), follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<option value="1" selected="selected">Shopping</option>' in rv.data
        assert '<header><h1>Edit Expense "Sainsbury&#39;s"</h1></header>' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Sainsbury&#39;s in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;10.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the expenses listing
        rv = self.app.get('/expenses', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Sainsbury&#39;s in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
        <li class="red last">
            <p>
                <span class="amount">&pound;10.00</span>
                Tesco
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-01-29</div>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;10.00</span>
                Sainsbury&#39;s in <a href="/expenses/in/groceries">Groceries</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;980.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;10.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

    def test_edit_simple_expense_to_shared_with_private(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # edit expense get
        self.app.get('expense/edit/1')

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=50, user=2),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert 'Loan given' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;250.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;250.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

    def test_edit_simple_expense_to_shared_with_normal(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # edit expense get
        self.app.get('expense/edit/1')

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=50, user=2),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert 'Loan given' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;250.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;250.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;250.00</span>
                Bought a PC in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;250.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

        # check the expenses listing
        rv = self.app.get('/expenses', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;250.00</span>
                Bought a PC in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
        <li class="red last">
            <p>
                <span class="amount">&pound;250.00</span>
                Bought a PC
            </p>
            <div class="date">from <a href="/loans/with/admin">Admin</a>
                2011-01-29</div>
        ''' in rv.data

    def test_edit_shared_expense_with_private_to_simple(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense get
        rv = self.app.get('expense/edit/1')
        assert '<header><h1>Edit Expense "Tesco"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-28">' in rv.data
        assert '<option value="1" selected="selected">Shopping</option>' in rv.data
        assert '<input type=text name=description value="Tesco">' in rv.data
        assert '<option value="1" selected="selected">HSBC</option>' in rv.data
        assert '<input type=text name=amount value="20">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' in rv.data
        assert '<option value="2" selected="selected">Barunka</option>' in rv.data
        assert '<input type=text name=split value="50">' in rv.data


        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=None),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' not in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;500.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' not in rv.data

    def test_edit_shared_expense_with_normal_to_simple(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense post
        self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=None),
                           follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;500.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert 'Tesco' not in rv.data

        # check the expenses listing
        rv = self.app.get('/expenses', follow_redirects=True)
        assert 'Tesco' not in rv.data

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert 'Tesco' not in rv.data

    def test_edit_shared_expense_to_shared_same_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense get
        self.app.get('expense/edit/1')

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=75, user=2),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' in rv.data
        assert '<option value="2" selected="selected">Barunka</option>' in rv.data
        assert '<input type=text name=split value="75">' in rv.data

        # check the loans entries table
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC
            </p>
            <div class="date">to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;375.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/barunka">Barunka</a>' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data
        assert 'Loaned from' not in rv.data

    def test_edit_shared_expense_to_shared_same_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=75, user=2),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' in rv.data
        assert '<option value="2" selected="selected">Barunka</option>' in rv.data
        assert '<input type=text name=split value="75">' in rv.data

        # check the loans entries table
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC
            </p>
            <div class="date">to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;375.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/barunka">Barunka</a>' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/barunka">Barunka</a>
        ''' in rv.data
        assert 'Loaned from' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Tesco in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/admin">Admin</a>' in rv.data

        assert 'Default' not in rv.data

        assert '''
        <li class="red last">
            <span class="amount">&minus; &pound;125.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        </li>
        ''' in rv.data

    def test_edit_shared_expense_to_shared_other_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # add second private user
        self.app.post('/user/add-private', data=dict(name="Nikki"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense get
        self.app.get('expense/edit/1')

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=75, user=3),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' in rv.data
        assert '<option value="3" selected="selected">Nikki</option>' in rv.data
        assert '<input type=text name=split value="75">' in rv.data

        # check the loans entries table
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC
            </p>
            <div class="date">to <a href="/loans/with/nikki">Nikki</a>
        ''' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;375.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/nikki">Nikki</a>' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/nikki">Nikki</a>
        ''' in rv.data
        assert 'Loaned from' not in rv.data

    def test_edit_shared_expense_to_shared_other_normal_user(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.get('/test/create-user/Nikki')

        # login
        self.app.post('/login', data=dict(username="nikki", password="nikki"), follow_redirects=True)

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
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=1, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=2, amount=500,
                                                       description="Bought a PC", is_shared=True, split=75, user=3),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data
        assert '<header><h1>Edit Expense "Bought a PC"</h1></header>' in rv.data
        assert '<input type=text name=date value="2011-01-29">' in rv.data
        assert '<option value="2" selected="selected">Purchases</option>' in rv.data
        assert '<input type=text name=description value="Bought a PC">' in rv.data
        assert '<option value="2" selected="selected">Credit Card</option>' in rv.data
        assert '<input type=text name=amount value="500">' in rv.data
        assert '<input type=checkbox name=is_shared checked>' in rv.data
        assert '<option value="3" selected="selected">Nikki</option>' in rv.data
        assert '<input type=text name=split value="75">' in rv.data
        
        # check the loans entries table
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC
            </p>
            <div class="date">to <a href="/loans/with/nikki">Nikki</a>
        ''' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        print rv.data
        assert '''
                <span class="amount">&minus; &pound;375.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/nikki">Nikki</a>' in rv.data
        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;500.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/nikki">Nikki</a>
        ''' in rv.data
        assert 'Loaned from' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the other user in the past
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert 'Tesco' not in rv.data
        assert 'Loaned' not in rv.data
        assert 'Default' not in rv.data

        # check the expenses
        rv = self.app.get('/expenses', follow_redirects=True)
        assert 'Tesco' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert 'Tesco' not in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as the current shared with user
        self.app.post('/login', data=dict(username="nikki", password="nikki"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC in <a href="/expenses/in/uncategorized">Uncategorized</a>
        ''' in rv.data
        assert 'shared with <a href="/loans/with/admin">Admin</a>' in rv.data

        assert 'Default' not in rv.data

        assert '''
            <span class="amount">&minus; &pound;125.00</span>
            Loaned from <a href="/loans/with/admin">Admin</a>
        ''' in rv.data

    def test_multiple_edit(self):
        # add normal user
        self.app.get('/test/create-user/Barunka')

        # login
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

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
        self.app.get('/test/create-user/Nikki')

        # login
        self.app.post('/login', data=dict(username="nikki", password="nikki"), follow_redirects=True)

        # fetch their key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # link with us
        self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)

        # add private users
        self.app.post('/user/add-private', data=dict(name="Tommi"), follow_redirects=True)

        self.app.post('/user/add-private', data=dict(name="Gunn"), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="HSBC", type="asset", balance=1000), follow_redirects=True)

        # create account
        self.app.post('/account/add', data=dict(name="Credit Card", type="liability", balance=0),
                           follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Shopping"), follow_redirects=True)

        # create expense category
        self.app.post('/expense/category/add', data=dict(name="Purchases"), follow_redirects=True)

        # add expense
        self.app.post('/expense/add', data=dict(
                date="2011-01-28", category=1, description="Tesco", deduct_from=4, amount=20, is_shared=True, split=50,
                user=2), follow_redirects=True)

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=2, deduct_from=3, amount=500,
                                                       description="Bought a PC", is_shared=True, split=75, user=3),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;375.00</span>
                Bought a PC in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'Tesco' not in rv.data

        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/nikki">Nikki</a>
        ''' in rv.data
        assert 'Loaned to <a href="/loans/with/barunka">Barunka</a>' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;125.00</span>
                Bought a PC
            </p>
            <div class="date">to <a href="/loans/with/nikki">Nikki</a>
                2011-01-29</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/barunka">Barunka</a>' not in rv.data
        assert '<div class="date">from <a href="/loans/with/barunka">Barunka</a>' not in rv.data

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-30", category=1, deduct_from=4, amount=1000,
                                                       description="Bought a Fridge", is_shared=True, split=50, user=4),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;500.00</span>
                Bought a Fridge in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data
        assert 'PC' not in rv.data

        assert '''
            <span class="amount">&pound;500.00</span>
            Loaned to <a href="/loans/with/tommi">Tommi</a>
        ''' in rv.data
        assert 'Loaned to <a href="/loans/with/nikki">Nikki</a>' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;500.00</span>
                Bought a Fridge
            </p>
            <div class="date">to <a href="/loans/with/tommi">Tommi</a>
                2011-01-30</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/nikki">Nikki</a>' not in rv.data
        assert '<div class="date">from <a href="/loans/with/nikki">Nikki</a>' not in rv.data

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-31", category=2, deduct_from=3, amount=250,
                                                       description="Bought an Apple", is_shared=True, split=50, user=5),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;125.00</span>
                Bought an Apple in <a href="/expenses/in/purchases">Purchases</a>
        ''' in rv.data
        assert 'Fridge' not in rv.data

        assert '''
            <span class="amount">&pound;125.00</span>
            Loaned to <a href="/loans/with/gunn">Gunn</a>
        ''' in rv.data
        assert 'Loaned to <a href="/loans/with/tommi">Tommi</a>' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '''
            <p>
                <span class="amount">&minus; &pound;125.00</span>
                Bought an Apple
            </p>
            <div class="date">to <a href="/loans/with/gunn">Gunn</a>
                2011-01-31</div>
        ''' in rv.data
        assert '<div class="date">to <a href="/loans/with/tommi">Tommi</a>' not in rv.data
        assert '<div class="date">from <a href="/loans/with/tommi">Tommi</a>' not in rv.data

        # edit expense post
        rv = self.app.post('/expense/edit/1', data=dict(date="2011-01-29", category=1, deduct_from=4, amount=20,
                                                       description="Bought a Book", is_shared=None),
                           follow_redirects=True)
        assert 'Expense edited' in rv.data

        # check the dashboard
        rv = self.app.get('/')
        assert '''
                <span class="amount">&minus; &pound;20.00</span>
                Bought a Book in <a href="/expenses/in/shopping">Shopping</a>
        ''' in rv.data

        assert '''
            <span class="amount">&pound;1,000.00</span>
            <a>HSBC</a>
        ''' in rv.data
        assert '''
            <span class="amount">&minus; &pound;20.00</span>
            <a>Credit Card</a>
        ''' in rv.data
        assert 'shared with' not in rv.data
        assert 'Loaned from' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<div class="date">to <a href="/loans/with/' not in rv.data
        assert '<div class="date">from <a href="/loans/with/' not in rv.data

        # login as barunka
        self.app.get('/logout', follow_redirects=True)
        self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert 'Default' not in rv.data
        assert '&pound;' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<div class="date">to <a href="/loans/with/admin">Admin</a>' not in rv.data
        assert '<div class="date">from <a href="/loans/with/admin">Admin</a>' not in rv.data

        # login as nikki
        self.app.get('/logout', follow_redirects=True)
        self.app.post('/login', data=dict(username="nikki", password="nikki"), follow_redirects=True)

        # check the dashboard
        rv = self.app.get('/')
        assert 'Default' not in rv.data
        assert '&pound;' not in rv.data

        # check the loans
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<div class="date">to <a href="/loans/with/admin">Admin</a>' not in rv.data
        assert '<div class="date">from <a href="/loans/with/admin">Admin</a>' not in rv.data