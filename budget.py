# framework
from __future__ import with_statement
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash

# models
from sqlalchemy.sql.expression import desc
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
    return render_template('show_accounts.html',
                           accounts=Account.query.filter(Account.user == session.get('logged_in_user')))

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
        a1 = Account.query.\
        filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['deduct_from']).first()
        a1.balance -= float(request.form['amount'])
        db_session.add(a1)

        a2 = Account.query.\
        filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['credit_to']).first()
        a2.balance += float(request.form['amount'])
        db_session.add(a2)

        db_session.commit()
        flash('Monies transferred')
    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('account_transfer.html', **locals())

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

''' Auth '''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = User.query\
        .filter(User.username == request.form['username'])\
        .filter(User.password == request.form['password']).first()
        if u:
            session['logged_in_user'] = u.id
            flash('You were logged in')
            return redirect(url_for('show_expenses'))
        else:
            error = 'Invalid username and/or password'
    return render_template('login.html', error=error)

@app.route('/add/user/<username>')
def add_user(username):
    u = User(username, username)
    db_session.add(u)
    db_session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in_user', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
