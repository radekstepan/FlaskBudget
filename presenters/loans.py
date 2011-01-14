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
    if request.method == 'POST':
        l = Loan(request.form['user'], session.get('logged_in_user'), request.form['date'],
                 request.form['credit_to'], request.form['description'], request.form['amount'])
        db_session.add(l)

        # transfer money
        __account_transfer(from_user=request.form['user'], to_user=session.get('logged_in_user'),
                           amount=request.form['amount'], to_account=request.form['credit_to'])

        # update/create loan type account (us & them)
        __make_loan(request.form['user'], session.get('logged_in_user'), request.form['amount'])

        flash('Loan received')

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    return render_template('admin_get_loan.html', **locals())

@loans.route('/loan/give', methods=['GET', 'POST'])
@login_required
def give():
    if request.method == 'POST':
        l = Loan(session.get('logged_in_user'), request.form['user'], request.form['date'],
                 request.form['deduct_from'], request.form['description'], request.form['amount'])
        db_session.add(l)

        # transfer money
        __account_transfer(from_user=session.get('logged_in_user'), to_user=request.form['user'],
                           amount=request.form['amount'], from_account=request.form['deduct_from'])

        # update/create loan type account (us & them)
        __make_loan(session.get('logged_in_user'), request.form['user'], request.form['amount'])

        flash('Loan given')

    # user's users ;) and accounts
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
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