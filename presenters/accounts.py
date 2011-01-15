# framework
from flask import Module, session, render_template, redirect, request, flash, url_for
from sqlalchemy.sql.expression import asc, desc, or_
from sqlalchemy.orm import aliased

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models import *

# utils
from utils import *

accounts = Module(__name__)

''' Accounts '''
@accounts.route('/account-transfers/')
@accounts.route('/account-transfers/for/<date>')
@accounts.route('/account-transfers/with/<account>')
@accounts.route('/account-transfers/with/<account>/for/<date>')
@login_required
def index(account=None, date=None):
    current_user_id = session.get('logged_in_user')

    # table referred to twice, create alias
    from_account_alias = aliased(Account)
    to_account_alias = aliased(Account)
    # fetch account transfers
    transfers = AccountTransfer.query.filter(AccountTransfer.user == current_user_id)\
    .order_by(desc(AccountTransfer.date)).order_by(desc(AccountTransfer.id))\
    .join(
            (from_account_alias, (AccountTransfer.from_account == from_account_alias.id)),\
            (to_account_alias, (AccountTransfer.to_account == to_account_alias.id)))\
    .add_columns(from_account_alias.name, to_account_alias.name)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        transfers = transfers\
        .filter(AccountTransfer.date >= date_range['low']).filter(AccountTransfer.date <= date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # fetch accounts
    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')

    # provided an account?
    if account:
        # search for the slug
        for acc in accounts:
            if acc.slug == account:
                transfers = transfers.add_columns(from_account_alias.slug, to_account_alias.slug)\
                .filter(or_(from_account_alias.slug == account, to_account_alias.slug == account))
                break

    return render_template('admin_show_transfers.html', **locals())

@accounts.route('/account/add', methods=['GET', 'POST'])
@login_required
def add():
    error = None
    if request.method == 'POST':
        new_account_name, account_type, account_balance, current_user_id =\
        request.form['name'], request.form['type'], request.form['balance'], session.get('logged_in_user')

        # blank name?
        if new_account_name:
            # type?
            if account_type == 'asset' or account_type == 'liability':\
                # if balance blank, pass in 0
                if not account_balance: account_balance = 0
                # is balance a valid float?
                if is_float(account_balance):
                    # already exists?
                    if not Account.query\
                        .filter(Account.user == current_user_id)\
                        .filter(Account.name == new_account_name).first():

                        # create new account
                        a = Account(current_user_id, new_account_name, account_type, account_balance)
                        db_session.add(a)
                        db_session.commit()
                        flash('Account added')

                    else: error = 'You already have an account under that name'
                else: error = 'The initial balance needs to be a floating number'
            else: error = 'The account needs to either be an asset or a liability'
        else: error = 'You need to provide a name for the account'

    return render_template('admin_add_account.html', **locals())

@accounts.route('/account/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    error = None
    current_user_id = session.get('logged_in_user')

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'date' in request.form: date = request.form['date']
        else: error = 'You need to provide a date'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'deduct_from' in request.form: deduct_from_account = request.form['deduct_from']
        else: error = 'You need to provide an account to deduct from'
        if 'credit_to' in request.form: credit_to_account = request.form['credit_to']
        else: error = 'You need to provide an account to credit to'

        # 'heavier' checks
        if not error:
            # source and target the same?
            if not deduct_from_account == credit_to_account:
                # valid amount?
                if is_float(amount):
                    # valid date?
                    if is_date(date):
                        # valid debit account?
                        debit_a = Account.query\
                        .filter(Account.user == current_user_id)\
                        .filter(Account.type != 'loan')\
                        .filter(Account.id == deduct_from_account).first()
                        if debit_a:
                            # valid credit account?
                            credit_a = Account.query\
                            .filter(Account.user == current_user_id)\
                            .filter(Account.type != 'loan')\
                            .filter(Account.id == credit_to_account).first()
                            if credit_a:

                                # add a new transfer row
                                t = AccountTransfer(current_user_id, date, deduct_from_account, credit_to_account,
                                                    amount)
                                db_session.add(t)

                                # modify accounts
                                __account_transfer(current_user_id, current_user_id, amount, deduct_from_account,
                                                   credit_to_account)

                                db_session.commit()
                                flash('Monies transferred')

                            else: error = 'Not a valid target account'
                        else: error = 'Not a valid source account'
                    else: error = 'Not a valid date'
                else: error = 'Not a valid amount'
            else: error = 'Source and target accounts cannot be the same'

    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')

    return render_template('admin_add_transfer.html', **locals())

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