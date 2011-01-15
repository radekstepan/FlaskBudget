# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models import *

# utils
from utils import *

income = Module(__name__)

''' Income '''
@income.route('/income/')
@login_required
def index():
    return render_template('admin_show_income.html', entries=Income.query
    .filter(Income.user == session.get('logged_in_user'))
    .join(IncomeCategory)
    .add_columns(IncomeCategory.name)
    .order_by(desc(Income.date)).order_by(desc(Income.id)))

@income.route('/income/add', methods=['GET', 'POST'])
@login_required
def add():
    error = None
    current_user_id = session.get('logged_in_user')

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'date' in request.form: date = request.form['date']
        else: error = 'Not a valid date'
        if 'category' in request.form: category_id = request.form['category']
        else: error = 'You need to provide a category'
        if 'credit_to' in request.form: account_id = request.form['credit_to']
        else: error = 'You need to provide an account'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'

        # 'heavier' checks
        if not error:
            # valid date?
            if is_date(date):
                if is_float(amount):
                # valid category?
                    if IncomeCategory.query\
                    .filter(IncomeCategory.user == current_user_id)\
                    .filter(IncomeCategory.id == category_id)\
                    .first():
                    # valid account?
                        a = Account.query\
                        .filter(Account.user == current_user_id)\
                        .filter(Account.type != 'loan')\
                        .filter(Account.id == account_id).first()
                        if a:

                            # add new income
                            i = Income(current_user_id, date, category_id, description, account_id, amount)
                            db_session.add(i)

                            # credit to account
                            a.balance += float(amount)
                            db_session.add(a)

                            db_session.commit()
                            flash('Income added')

                        else: error = 'Not a valid account'
                    else: error = 'Not a valid category'
                else: error = 'Not a valid amount'
            else: error = 'Not a valid date'

    # fetch user's categories and accounts
    categories = IncomeCategory.query.filter(IncomeCategory.user == current_user_id).order_by(IncomeCategory.name)

    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')

    return render_template('admin_add_income.html', **locals())

@income.route('/income/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        # blank name?
        if new_category_name:
            # already exists?
            if not IncomeCategory.query\
                .filter(IncomeCategory.user == current_user_id)\
                .filter(IncomeCategory.name == new_category_name).first():

                # create category
                c = IncomeCategory(current_user_id, new_category_name)
                db_session.add(c)
                db_session.commit()
                flash('Income category added')

            else:
                error = 'You already have a category under that name'
        else:
            error = 'You need to provide a name'

    return render_template('admin_add_income_category.html', error=error)