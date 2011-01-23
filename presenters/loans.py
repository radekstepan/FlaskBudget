# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc, or_, and_
from sqlalchemy.orm import aliased
from flaskext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required
from presenters.accounts import __account_transfer

# models
from db.database import db_session
from models.users import UsersTable, UsersConnectionsTable, Users
from models.loans import LoansTable, Loans
from models.accounts import AccountsTable, Accounts

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

    # table referred to twice, create alias
    from_user_alias = aliased(UsersTable)
    to_user_alias = aliased(UsersTable)
    # fetch loans
    loans = LoansTable.query\
    .filter(or_(LoansTable.from_user == current_user_id, LoansTable.to_user == current_user_id))\
    .order_by(desc(LoansTable.date)).order_by(desc(LoansTable.id))\
    .join(
            (from_user_alias, (LoansTable.from_user == from_user_alias.id)),\
            (to_user_alias, (LoansTable.to_user == to_user_alias.id)))\
    .add_columns(from_user_alias.name, from_user_alias.slug, to_user_alias.name, to_user_alias.slug)

    # fetch users from connections from us
    users = UsersTable.query.join((UsersConnectionsTable, (UsersTable.id == UsersConnectionsTable.to_user)))\
    .filter(UsersConnectionsTable.from_user == current_user_id)

    # provided user?
    if user:
        # search for the slug
        for usr in users:
            if usr.slug == user:
                loans = loans.filter(or_(
                        and_(LoansTable.from_user == current_user_id, LoansTable.to_user == usr.id),
                        and_(LoansTable.from_user == usr.id, LoansTable.to_user == current_user_id)
                        ))
                break

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        loans = loans.filter(LoansTable.date >= date_range['low']).filter(LoansTable.date <= date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # provided a direction?
    if direction:
        if direction == 'to-us':
            loans = loans.filter(LoansTable.to_user == current_user_id)
        elif direction == 'to-them':
            loans = loans.filter(LoansTable.from_user == current_user_id)

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
                    if acc_us.is_account(id=credit_to_account):

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
                    if acc_us.is_account(id=deduct_from_account):

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
    users = UsersTable.query.join((UsersConnectionsTable, (UsersTable.id == UsersConnectionsTable.to_user)))\
    .filter(UsersConnectionsTable.from_user == current_user_id)

    accounts = AccountsTable.query.filter(AccountsTable.user == current_user_id).filter(AccountsTable.type != 'loan')

    return render_template('admin_give_loan.html', **locals())

def __make_loan(from_user, to_user, amount):
    # update/create loan type account (us & them)
    a1 = AccountsTable.query.filter(AccountsTable.user == to_user)\
    .filter(AccountsTable.type == 'loan')\
    .filter(AccountsTable.name == from_user).first()
    if not a1:
    # initial
        a1 = AccountsTable(to_user, from_user, 'loan', -float(amount))
        db_session.add(a1)
    else:
    # update
        a1.balance -= float(amount)
        db_session.add(a1)

    a2 = AccountsTable.query.filter(AccountsTable.user == from_user)\
    .filter(AccountsTable.type == 'loan')\
    .filter(AccountsTable.name == to_user).first()
    if not a2:
    # initial
        a2 = AccountsTable(from_user, to_user, 'loan', float(amount))
        db_session.add(a2)
    else:
    # update
        a2.balance += float(amount)
        db_session.add(a2)

    db_session.commit()