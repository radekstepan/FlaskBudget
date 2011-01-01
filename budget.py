# framework
from __future__ import with_statement
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash
from sqlalchemy.sql.expression import desc, asc
from sqlalchemy.orm import aliased

# models
from db.database import db_session
from models import *

# authentication
from auth import login_required

DEBUG = True
#USERNAME = 'radek'
#PASSWORD = 'radek'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = '98320C8A14B7D50623A8AC1D78D7E9D8F8DF1D390ABEFE3D3263B135493DF250'

@app.after_request
def shutdown_session(response):
    db_session.remove()
    return response

''' Dashboard '''
@app.route('/')
@login_required
def dashboard():
    return redirect(url_for('show_expenses'))

''' Accounts '''
@app.route('/accounts')
@login_required
def show_accounts():
    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))

    # table referred to twice, create alias
    from_account_alias = aliased(Account)
    to_account_alias = aliased(Account)
    # fetch account transfers
    transfers=AccountTransfer.query.filter(AccountTransfer.user == session.get('logged_in_user'))\
    .order_by(desc(AccountTransfer.date))\
    .join(
            (from_account_alias, (AccountTransfer.from_account == from_account_alias.id)),\
            (to_account_alias, (AccountTransfer.to_account == to_account_alias.id)))\
    .add_columns(from_account_alias.name, to_account_alias.name)

    return render_template('show_accounts.html', **locals())

@app.route('/account/add', methods=['GET', 'POST'])
@login_required
def add_account():
    error = None
    if request.method == 'POST':
        a = Account(session.get('logged_in_user'), request.form['name'], request.form['balance'])
        db_session.add(a)
        db_session.commit()
        flash('Account added')
    return render_template('add_account.html', error=error)

@app.route('/account/transfer', methods=['GET', 'POST'])
@login_required
def account_transfer():
    error = None
    if request.method == 'POST':
        # add a new transfer row
        t = AccountTransfer(session.get('logged_in_user'), request.form['date'], request.form['deduct_from'],
                            request.form['credit_to'], request.form['amount'])
        db_session.add(t)

        # modify accounts
        __account_transfer(session.get('logged_in_user'), session.get('logged_in_user'),
                           request.form['amount'], request.form['deduct_from'], request.form['credit_to'])

        db_session.commit()
        flash('Monies transferred')

    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('account_transfer.html', **locals())

def __account_transfer(from_user, to_user, amount, from_account=None, to_account=None):
    # fetch first user's account if not provided (default)
    if not from_account:
        a = Account.query.filter(Account.user == from_user).order_by(asc(Account.id)).first()
        from_account = a.id
    if not to_account:
        a = Account.query.filter(Account.user == to_user).order_by(asc(Account.id)).first()
        to_account = a.id

    # deduct
    a1 = Account.query.filter(Account.user == from_user).filter(Account.id == from_account).first()
    a1.balance -= float(amount)
    db_session.add(a1)

    # credit
    a2 = Account.query.filter(Account.user == to_user).filter(Account.id == to_account).first()
    a2.balance += float(amount)
    db_session.add(a2)

''' Income '''
@app.route('/income/')
@login_required
def show_income():
    return render_template('show_income.html', entries=Income.query
    .filter(Income.user == session.get('logged_in_user'))
    .join(IncomeCategory)
    .add_columns(IncomeCategory.name)
    .order_by(desc(Income.date)))

@app.route('/income/add', methods=['GET', 'POST'])
@login_required
def add_income():
    error = None
    if request.method == 'POST':
        # add new income
        i = Income(session.get('logged_in_user'), request.form['date'], request.form['category'],
                    request.form['description'], request.form['credit_to'], request.form['amount'])
        db_session.add(i)

        # credit to account
        a = Account.query.\
        filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['credit_to']).first()
        a.balance += float(request.form['amount'])
        db_session.add(a)

        db_session.commit()
        flash('Income added')

    # fetch user's categories and accounts
    categories = IncomeCategory.query.filter(IncomeCategory.user == session.get('logged_in_user'))\
    .order_by(IncomeCategory.name)
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('add_income.html', **locals())

@app.route('/income/category/add', methods=['GET', 'POST'])
@login_required
def add_income_category():
    error = None
    if request.method == 'POST':
        c = IncomeCategory(session.get('logged_in_user'), request.form['name'])
        db_session.add(c)
        db_session.commit()
        flash('Income category added')
    return render_template('add_income_category.html', error=error)

''' Expenses '''
@app.route('/expenses/')
@login_required
def show_expenses():
    return render_template('show_expenses.html', entries=Expense.query
    .filter(Expense.user == session.get('logged_in_user'))
    .join(ExpenseCategory)
    .add_columns(ExpenseCategory.name)
    .order_by(desc(Expense.date)))

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    error = None
    if request.method == 'POST':
        # add new expense
        e = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                    request.form['description'], request.form['deduct_from'], request.form['amount'])
        db_session.add(e)

        # debit from account
        a = Account.query.\
        filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['deduct_from']).first()
        a.balance -= float(request.form['amount'])
        db_session.add(a)

        db_session.commit()
        flash('Expense added')

    # fetch user's categories and accounts
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == session.get('logged_in_user'))\
    .order_by(ExpenseCategory.name)
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('add_expense.html', **locals())

@app.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_expense_category():
    error = None
    if request.method == 'POST':
        c = ExpenseCategory(session.get('logged_in_user'), request.form['name'])
        db_session.add(c)
        db_session.commit()
        flash('Expense category added')
    return render_template('add_expense_category.html', error=error)

''' Loans '''
@app.route('/loan/get', methods=['GET', 'POST'])
@login_required
def get_loan():
    if request.method == 'POST':
        l = Loan(request.form['user'], session.get('logged_in_user'), request.form['date'],
                 request.form['credit_to'], request.form['description'], request.form['amount'])
        db_session.add(l)

        # transfer money
        __account_transfer(from_user=request.form['user'], to_user=session.get('logged_in_user'),
                           amount=request.form['amount'], to_account=request.form['deduct_from'])

        db_session.commit()
        flash('Loan received')

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('get_loan.html', **locals())

@app.route('/loan/give', methods=['GET', 'POST'])
@login_required
def give_loan():
    if request.method == 'POST':
        l = Loan(session.get('logged_in_user'), request.form['user'], request.form['date'],
                 request.form['deduct_from'], request.form['description'], request.form['amount'])
        db_session.add(l)

        # transfer money
        __account_transfer(from_user=session.get('logged_in_user'), to_user=request.form['user'],
                           amount=request.form['amount'], from_account=request.form['deduct_from'])

        db_session.commit()
        flash('Loan given')

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('give_loan.html', **locals())

''' Users '''
@app.route('/user/add/private', methods=['GET', 'POST'])
@login_required
def add_private_user():
    if request.method == 'POST':
        # create new private user associated with the current user
        u = User(request.form['name'], session.get('logged_in_user'), True)
        db_session.add(u)
        db_session.commit()

        # give the user a default account so we can do loans
        a = Account(u.id, "Default", 0)
        db_session.add(a)

        db_session.commit()
        flash('Private user added')
    return render_template('add_private_user.html')

''' Auth '''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = User.query\
        .filter(User.username == request.form['username'])\
        .filter(User.password == request.form['password'])\
        .filter(User.is_private == False)\
        .first()
        if u:
            session['logged_in_user'] = u.id
            flash('You were logged in')
            return redirect(url_for('show_expenses'))
        else:
            error = 'Invalid username and/or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in_user', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()