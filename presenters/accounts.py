# framework
from flask import Module, session, render_template, redirect, request, flash, url_for
from sqlalchemy.sql.expression import asc, desc
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
@accounts.route('/accounts')
@login_required
def index():
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

                    else:
                        error = 'You already have an account under that name'
                else:
                    error = 'The initial balance needs to be a floating number'
            else:
                error = 'The account needs to either be an asset or a liability'
        else:
            error = 'You need to provide a name for the account'

    return render_template('admin_add_account.html', **locals())

@accounts.route('/account/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
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