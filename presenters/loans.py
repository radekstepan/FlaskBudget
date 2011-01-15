# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc, or_
from sqlalchemy.orm import aliased

# presenters
from presenters.auth import login_required
from presenters.accounts import __account_transfer

# models
from db.database import db_session
from models import *

# utils
from utils import *

loans = Module(__name__)

''' Loans '''
@loans.route('/loans')
@login_required
def index():
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

    return render_template('admin_show_loans.html', **locals())

@loans.route('/loan/get', methods=['GET', 'POST'])
@login_required
def get():
    error = None
    current_user_id = session.get('logged_in_user')

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
                    a = Account.query\
                    .filter(Account.user == current_user_id)\
                    .filter(Account.type != 'loan')\
                    .filter(Account.id == credit_to_account).first()
                    if a:

                        l = Loan(from_user, current_user_id, date, credit_to_account, description, amount)
                        db_session.add(l)

                        # transfer money
                        __account_transfer(from_user=from_user, to_user=current_user_id, amount=amount,
                                           to_account=credit_to_account)

                        # update/create loan type account (us & them)
                        __make_loan(from_user, current_user_id, amount)

                        flash('Loan received')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == current_user_id)

    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')

    return render_template('admin_get_loan.html', **locals())

@loans.route('/loan/give', methods=['GET', 'POST'])
@login_required
def give():
    error = None
    current_user_id = session.get('logged_in_user')

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
                    a = Account.query\
                    .filter(Account.user == current_user_id)\
                    .filter(Account.type != 'loan')\
                    .filter(Account.id == deduct_from_account).first()
                    if a:

                        l = Loan(current_user_id, to_user, date,
                                 deduct_from_account, description, amount)
                        db_session.add(l)

                        # transfer money
                        __account_transfer(from_user=current_user_id, to_user=to_user,
                                           amount=amount, from_account=deduct_from_account)

                        # update/create loan type account (us & them)
                        __make_loan(current_user_id, to_user, amount)

                        flash('Loan given')

                    else: error = 'Not a valid source account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == current_user_id)

    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')

    return render_template('admin_give_loan.html', **locals())

def __make_loan(from_user, to_user, amount):
    # update/create loan type account (us & them)
    a1 = Account.query.filter(Account.user == to_user)\
    .filter(Account.type == 'loan')\
    .filter(Account.name == from_user).first()
    if not a1:
    # initial
        a1 = Account(to_user, from_user, 'loan', -float(amount))
        db_session.add(a1)
    else:
    # update
        a1.balance -= float(amount)
        db_session.add(a1)

    a2 = Account.query.filter(Account.user == from_user)\
    .filter(Account.type == 'loan')\
    .filter(Account.name == to_user).first()
    if not a2:
    # initial
        a2 = Account(from_user, to_user, 'loan', float(amount))
        db_session.add(a2)
    else:
    # update
        a2.balance += float(amount)
        db_session.add(a2)

    db_session.commit()