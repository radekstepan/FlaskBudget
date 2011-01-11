# framework
from __future__ import with_statement
from flask import Flask, request, session, url_for, redirect, render_template, flash
from sqlalchemy.sql.expression import desc, asc, or_
from sqlalchemy.orm import aliased

# models
from db.database import db_session
from models import *

# authentication
from auth import login_required

# utils
from datetime import date, timedelta

DEBUG = True

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
    # get uncategorized expenses
    uncategorized_expenses = Expense.query.filter(Expense.user == session.get('logged_in_user'))\
    .join(ExpenseCategory).add_columns(ExpenseCategory.name)\
    .filter(ExpenseCategory.name == 'Uncategorized').order_by(desc(Expense.date))

    # get latest expenses
    latest_expenses = Expense.query.filter(Expense.user == session.get('logged_in_user'))\
    .join(ExpenseCategory).add_columns(ExpenseCategory.name).order_by(desc(Expense.date)).limit(5)

    # get accounts
    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))\
    .filter(Account.balance != 0)\
    .outerjoin((User, Account.name == User.id))\
    .add_columns(User.name)\
    .order_by(asc(Account.type)).order_by(asc(Account.id))

    # split, get totals
    assets, liabilities, loans, assets_total, liabilities_total = [], [], [], 0, 0
    for a in accounts:
        if a[0].type == 'asset':
            assets.append(a)
            assets_total += float(a[0].balance)
        elif a[0].type == 'liability':
            liabilities.append(a)
            liabilities_total += float(a[0].balance)
        elif a[0].type == 'loan':
            # if we owe someone, it is our liability
            if (float(a[0].balance) < 0):
                liabilities.append(a)
                liabilities_total += float(a[0].balance)
            else:
                assets.append(a)

    return render_template('admin_dashboard.html', **locals())

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
    .order_by(desc(AccountTransfer.date)).order_by(desc(AccountTransfer.id))\
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
        a = Account(session.get('logged_in_user'), request.form['name'], request.form['type'], request.form['balance'])
        db_session.add(a)
        db_session.commit()
        flash('Account added')
    return render_template('admin_add_account.html', error=error)

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
    .order_by(desc(Income.date)).order_by(desc(Income.id)))

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
    .order_by(desc(Expense.date)).order_by(desc(Expense.id)))

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    error = None
    if request.method == 'POST':
        # is it a shared expense?
        if 'is_shared' in request.form:\
            # figure out percentage split
            loaned_amount = (float(request.form['amount'])*(100-float(request.form['split'])))/100
            # create a loan
            l = Loan(session.get('logged_in_user'), request.form['user'], request.form['date'],
                     request.form['deduct_from'], request.form['description'], loaned_amount)
            db_session.add(l)
            flash('Loan given')

            # add new expense (loaner)
            e1 = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                        request.form['description'], request.form['deduct_from'],
                        float(request.form['amount']) - loaned_amount)
            db_session.add(e1)

            # add "uncategorized" category if not already present (for the borrower to sort out)
            c = ExpenseCategory.query\
            .filter(ExpenseCategory.user == request.form['user'])\
            .filter(ExpenseCategory.name == "Uncategorized").first()
            if not c:
                c = ExpenseCategory(request.form['user'], "Uncategorized")
                db_session.add(c)
                db_session.commit()

            # fetch default category (for the borrower)
            a = Account.query.filter(Account.user == request.form['user']).order_by(asc(Account.id)).first()
            deduct_from = a.id

            # add new expense (borrower)
            e2 = Expense(request.form['user'], request.form['date'], c.id, request.form['description'],
                         deduct_from, loaned_amount)
            db_session.add(e2)
        else:
            # add new expense
            e = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                        request.form['description'], request.form['deduct_from'], request.form['amount'])
            db_session.add(e)

        # debit from account
        a = Account.query\
        .filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['deduct_from']).first()
        a.balance -= float(request.form['amount'])
        db_session.add(a)

        db_session.commit()
        flash('Expense added')

    # fetch user's categories, accounts and users
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == session.get('logged_in_user'))\
    .order_by(ExpenseCategory.name)
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
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
@app.route('/loans')
@login_required
def show_loans():
    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))

    # table referred to twice, create alias
    from_user_alias = aliased(User)
    to_user_alias = aliased(User)
    # fetch loans
    loans=Loan.query\
    .filter(or_(Loan.from_user == session.get('logged_in_user'), Loan.to_user == session.get('logged_in_user')))\
    .order_by(desc(Loan.date)).order_by(desc(Loan.id))\
    .join(
            (from_user_alias, (Loan.from_user == from_user_alias.id)),\
            (to_user_alias, (Loan.to_user == to_user_alias.id)))\
    .add_columns(from_user_alias.name, to_user_alias.name)

    return render_template('show_loans.html', **locals())

@app.route('/loan/get', methods=['GET', 'POST'])
@login_required
def get_loan():
    if request.method == 'POST':
        l = Loan(request.form['user'], session.get('logged_in_user'), request.form['date'],
                 request.form['credit_to'], request.form['description'], request.form['amount'])
        db_session.add(l)

        # transfer money
        __account_transfer(from_user=request.form['user'], to_user=session.get('logged_in_user'),
                           amount=request.form['amount'], to_account=request.form['credit_to'])

        # update/create loan type account (us & them)
        a1 = Account.query.filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.type == 'loan')\
        .filter(Account.name == request.form['user']).first()
        if not a1:
            # initial
            a1 = Account(session.get('logged_in_user'), request.form['user'], 'loan', -float(request.form['amount']))
            db_session.add(a1)
        else:
            # update
            a1.balance -= float(request.form['amount'])
            db_session.add(a1)

        a2 = Account.query.filter(Account.user == request.form['user'])\
        .filter(Account.type == 'loan')\
        .filter(Account.name == session.get('logged_in_user')).first()
        if not a2:
            # initial
            a2 = Account(request.form['user'], session.get('logged_in_user'), 'loan', request.form['amount'])
            db_session.add(a2)
        else:
            # update
            a2.balance += float(request.form['amount'])
            db_session.add(a2)

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

        # update/create loan type account (us & them)
        a1 = Account.query.filter(Account.user == request.form['user'])\
        .filter(Account.type == 'loan')\
        .filter(Account.name == session.get('logged_in_user')).first()
        if not a1:
            # initial
            a1 = Account(request.form['user'], session.get('logged_in_user'), 'loan', -float(request.form['amount']))
            db_session.add(a1)
        else:
            # update
            a1.balance -= float(request.form['amount'])
            db_session.add(a1)

        a2 = Account.query.filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.type == 'loan')\
        .filter(Account.name == request.form['user']).first()
        if not a2:
            # initial
            a2 = Account(session.get('logged_in_user'), request.form['user'], 'loan', request.form['amount'])
            db_session.add(a2)
        else:
            # update
            a2.balance += float(request.form['amount'])
            db_session.add(a2)

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
        a = Account(u.id, "Default", 'private', 0)
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
            session['user_name'] = u.name
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

@app.template_filter('datetimeformat')
def datetimeformat(value):
    if date.today() == value:
        return 'Today'
    elif date.today() - timedelta(1) == value:
        return 'Yesterday'
    else:
        return value

if __name__ == '__main__':
    app.run()