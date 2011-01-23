# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc
from flaskext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models.income import IncomeTable, IncomeCategoriesTable, Income
from models.accounts import AccountsTable, Accounts

# utils
from utils import *

income = Module(__name__)

''' Income '''
@income.route('/income/')
@income.route('/income/for/<date>')
@income.route('/income/in/<category>')
@income.route('/income/page/<int:page>')
@income.route('/income/for/<date>/in/<category>')
@income.route('/income/for/<date>/page/<int:page>')
@income.route('/income/in/<category>/page/<int:page>')
@income.route('/income/for/<date>/in/<category>/page/<int:page>')
@login_required
def index(date=None, category=None, page=1, items_per_page=10):
    current_user_id = session.get('logged_in_user')

    inc = Income(current_user_id)

    # fetch entries
    entries = inc.get_entries()

    # categories
    categories = inc.get_categories()
    # provided category?
    if category:
        # search for the slug
        category_id = inc.is_category(slug=category)
        if category_id:
            entries = inc.get_entries(category_id=category_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        entries = inc.get_entries(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # build a paginator
    paginator = Pagination(entries, page, items_per_page, entries.count(),
                           entries.offset((page - 1) * items_per_page).limit(items_per_page))

    return render_template('admin_show_income.html', **locals())

@income.route('/income/add', methods=['GET', 'POST'])
@login_required
def add_income():
    error = None
    current_user_id = session.get('logged_in_user')

    inc = Income(current_user_id)
    acc = Accounts(current_user_id)

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
                # valid amount?
                if is_float(amount):
                    # valid category?
                    if inc.is_category(id=category_id):
                        # valid account?
                        if acc.is_account(account_id=account_id):

                            # add new income
                            inc.add_income(account_id=account_id, amount=amount, category_id=category_id, date=date,
                                           description=description)

                            # credit to account
                            acc.modify_account_balance(account_id, amount)

                            flash('Income added')

                        else: error = 'Not a valid account'
                    else: error = 'Not a valid category'
                else: error = 'Not a valid amount'
            else: error = 'Not a valid date'

    # fetch user's categories and accounts
    categories = inc.get_categories()

    accounts = AccountsTable.query.filter(AccountsTable.user == current_user_id).filter(AccountsTable.type != 'loan')

    return render_template('admin_add_income.html', **locals())

@income.route('/income/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        inc = Income(current_user_id)

        # blank name?
        if new_category_name:
            # already exists?
            if not inc.is_category(name=new_category_name):

                # create category
                inc.add_category(new_category_name)
                flash('Income category added')

            else: error = 'You already have a category under that name'
        else: error = 'You need to provide a name'

    return render_template('admin_add_income_category.html', error=error)