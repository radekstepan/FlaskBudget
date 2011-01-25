# framework
from flask import Module, session, render_template, redirect, request, flash
from flask.helpers import url_for
from flaskext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required

# models
from models.users import Users
from models.loans import Loans
from models.accounts import Accounts

# utils
from utils import *

loans = Module(__name__)

''' Loans '''
@loans.route('/loans/')
@loans.route('/loans/made/<direction>')
@loans.route('/loans/with/<user>')
@loans.route('/loans/for/<date>')
@loans.route('/loans/page/<int:page>')
@loans.route('/loans/made/<direction>/page/<int:page>')
@loans.route('/loans/with/<user>/page/<int:page>')
@loans.route('/loans/for/<date>/page/<int:page>')
@loans.route('/loans/made/<direction>/with/<user>')
@loans.route('/loans/made/<direction>/with/<user>/page/<int:page>')
@loans.route('/loans/made/<direction>/for/<date>')
@loans.route('/loans/made/<direction>/for/<date>/page/<int:page>')
@loans.route('/loans/with/<user>/for/<date>')
@loans.route('/loans/with/<user>/for/<date>/page/<int:page>')
@loans.route('/loans/made/<direction>/with/<user>/for/<date>')
@loans.route('/loans/made/<direction>/with/<user>/for/<date>/page/<int:page>')
@login_required
def index(direction=None, user=None, date=None, page=1, items_per_page=10):
    current_user_id = session.get('logged_in_user')

    loa = Loans(current_user_id)
    usr = Users(current_user_id)

    # fetch loans
    loans = loa.get_loans()

    # fetch users from connections from us
    users = usr.get_connections()

    # provided user?
    if user:
        # valid slug?
        user_id = usr.is_connection(slug=user)
        if user_id: loans = loa.get_loans(user_id=user_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        loans = loa.get_loans(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # provided a direction?
    if direction: loans = loa.get_loans(direction=direction)

    # build a paginator
    paginator = Pagination(loans, page, items_per_page, loans.count(),
                           loans.offset((page - 1) * items_per_page).limit(items_per_page))

    return render_template('admin_show_loans.html', **locals())

@loans.route('/loan/get', methods=['GET', 'POST'])
@login_required
def get():
    error = None
    current_user_id = session.get('logged_in_user')

    acc_us = Accounts(current_user_id)
    usr = Users(current_user_id)

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'user' in request.form: from_user = request.form['user']
        else: error = 'You need to specify from whom to borrow'
        if 'date' in request.form: date = request.form['date']
        else: error = 'You need to provide a date'
        if 'credit_to' in request.form: credit_to_account = request.form['credit_to']
        else: error = 'You need to provide an account to credit to'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if acc_us.is_account(account_id=credit_to_account):

                        acc_them = Accounts(from_user)
                        loa = Loans(from_user)

                        # add loans entry
                        loa.add_loan(other_user_id=current_user_id, date=date, account_id=credit_to_account,
                                     description=description, amount=amount)

                        # transfer money from/to respective accounts
                        acc_us.modify_user_balance(account_id=credit_to_account, amount=amount)
                        acc_them.modify_user_balance(amount=-float(amount))

                        # fudge loan 'account' monies
                        acc_us.modify_loan_balance(amount=-float(amount), with_user_id=from_user)
                        acc_them.modify_loan_balance(amount=amount, with_user_id=current_user_id)

                        flash('Loan received')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch users from connections from us
    users = usr.get_connections()
    accounts = acc_us.get_accounts()

    return render_template('admin_get_loan.html', **locals())

@loans.route('/loan/give', methods=['GET', 'POST'])
@login_required
def give():
    error = None
    current_user_id = session.get('logged_in_user')

    acc_us = Accounts(current_user_id)
    usr = Users(current_user_id)

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'user' in request.form: to_user = request.form['user']
        else: error = 'You need to specify to whom to loan'
        if 'date' in request.form: date = request.form['date']
        else: error = 'You need to provide a date'
        if 'deduct_from' in request.form: deduct_from_account = request.form['deduct_from']
        else: error = 'You need to provide an account to deduct from'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if acc_us.is_account(account_id=deduct_from_account):

                        acc_them = Accounts(to_user)
                        loa = Loans(current_user_id)

                        # add loans entry
                        loa.add_loan(other_user_id=to_user, date=date, account_id=deduct_from_account,
                                     description=description, amount=amount)

                        # transfer money from/to respective accounts
                        acc_us.modify_user_balance(account_id=deduct_from_account, amount=-float(amount))
                        acc_them.modify_user_balance(amount=amount)

                        # fudge loan 'account' monies
                        acc_us.modify_loan_balance(amount=amount, with_user_id=to_user)
                        acc_them.modify_loan_balance(amount=-float(amount), with_user_id=current_user_id)

                        flash('Loan given')

                    else: error = 'Not a valid source account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch users from connections from us
    users = usr.get_connections()
    accounts = acc_us.get_accounts()

    return render_template('admin_give_loan.html', **locals())

@loans.route('/loans/edit/<loan_id>', methods=['GET', 'POST'])
@login_required
def edit_loan(loan_id):
    current_user_id = session.get('logged_in_user')

    loa = Loans(current_user_id)

    # is it valid?
    loan = loa.get_loan(loan_id)
    if loan:

        # fetch users from connections from us
        usr = Users(current_user_id)
        acc = Accounts(current_user_id)

        users = usr.get_connections()
        accounts = acc.get_accounts()

        if loan.from_user != current_user_id:
            return __edit_get_loan(**locals())
        else:
            return __edit_give_loan(**locals())

    else: return redirect(url_for('loans.index'))

def __edit_get_loan(loan_id, loa, loan, current_user_id, acc, usr, accounts, users):
    if request.method == 'POST': # POST
        error = None

        # fetch values and check they are actually provided
        if 'user' in request.form: from_user = request.form['user']
        else: error = 'You need to specify from whom to borrow'
        if 'date' in request.form: date = request.form['date']
        else: error = 'You need to provide a date'
        if 'credit_to' in request.form: credit_to_account = request.form['credit_to']
        else: error = 'You need to provide an account to credit to'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if acc.is_account(account_id=credit_to_account):

                        acc_them = Accounts(loan.from_user)

                        # first roll back user balances
                        acc.modify_user_balance(account_id=loan.account, amount=-float(loan.amount))
                        acc_them.modify_user_balance(amount=amount)

                        # now roll back loan account monies
                        acc.modify_loan_balance(amount=loan.amount, with_user_id=loan.from_user)
                        acc_them.modify_loan_balance(amount=-float(loan.amount), with_user_id=current_user_id)

                        # the user might have changed...
                        if loan.from_user != from_user:
                            acc_them = Accounts(from_user)

                        # transfer money from/to respective accounts
                        acc.modify_user_balance(account_id=credit_to_account, amount=amount)
                        acc_them.modify_user_balance(amount=-float(amount))

                        # fudge loan 'account' monies
                        acc.modify_loan_balance(amount=-float(amount), with_user_id=from_user)
                        acc_them.modify_loan_balance(amount=amount, with_user_id=current_user_id)

                        # update loans entry
                        loa.edit_loan(other_user_id=from_user, date=date, account_id=credit_to_account,
                                     description=description, amount=amount, loan_id=loan_id)

                        flash('Loan edited')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    return render_template('admin_edit_get_loan.html', **locals())

def __edit_give_loan(loan_id, loa, loan, current_user_id, acc, usr, accounts, users):
    if request.method == 'POST': # POST
        error = None

        # fetch values and check they are actually provided
        if 'user' in request.form: to_user = request.form['user']
        else: error = 'You need to specify to whom to loan'
        if 'date' in request.form: date = request.form['date']
        else: error = 'You need to provide a date'
        if 'deduct_from' in request.form: deduct_from_account = request.form['deduct_from']
        else: error = 'You need to provide an account to deduct from'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if acc.is_account(account_id=deduct_from_account):

                        acc_them = Accounts(loan.to_user)

                        # first roll back user balances
                        acc.modify_user_balance(account_id=loan.account, amount=loan.amount)
                        acc_them.modify_user_balance(amount=-float(loan.amount))

                        # now roll back loan account monies
                        acc.modify_loan_balance(amount=loan.amount, with_user_id=loan.to_user)
                        acc_them.modify_loan_balance(amount=amount, with_user_id=current_user_id)

                        # the user might have changed...
                        if loan.to_user != to_user:
                            acc_them = Accounts(to_user)

                        # transfer money from/to respective accounts
                        acc.modify_user_balance(account_id=deduct_from_account, amount=-float(amount))
                        acc_them.modify_user_balance(amount=amount)

                        # fudge loan 'account' monies
                        acc.modify_loan_balance(amount=amount, with_user_id=to_user)
                        acc_them.modify_loan_balance(amount=-float(amount), with_user_id=current_user_id)

                        # update loans entry
                        loa.edit_loan(other_user_id=to_user, date=date, account_id=deduct_from_account,
                                     description=description, amount=amount, loan_id=loan_id)

                        flash('Loan edited')

                    else: error = 'Not a valid source account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    return render_template('admin_edit_give_loan.html', **locals())