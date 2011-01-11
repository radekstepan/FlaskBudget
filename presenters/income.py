# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models import *

income = Module(__name__)

''' Income '''
@income.route('/income/')
@login_required
def index():
    return render_template('show_income.html', entries=Income.query
    .filter(Income.user == session.get('logged_in_user'))
    .join(IncomeCategory)
    .add_columns(IncomeCategory.name)
    .order_by(desc(Income.date)).order_by(desc(Income.id)))

@income.route('/income/add', methods=['GET', 'POST'])
@login_required
def add():
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

@income.route('/income/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        c = IncomeCategory(session.get('logged_in_user'), request.form['name'])
        db_session.add(c)
        db_session.commit()
        flash('Income category added')
    return render_template('add_income_category.html', error=error)