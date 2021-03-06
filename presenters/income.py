#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Blueprint, session, render_template, redirect, request, flash
from flask.helpers import url_for, make_response

# presenters
from presenters.auth import login_required
import entries

# models
from models.income import Income, IncomeTable
from models.accounts import Accounts

# utils
from utils import *

income = Blueprint('income', __name__)

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
    '''List income entries for the user'''

    model = Income(session.get('logged_in_user'))

    dict = entries.index(**locals())
    for key in dict.keys(): exec(key + " = dict['" + key + "']")

    return render_template('admin_show_income.html', **locals())

@income.route('/export/income/')
@income.route('/export/income/for/<date>')
@income.route('/export/income/in/<category>')
@income.route('/export/income/page/<int:page>')
@income.route('/export/income/for/<date>/in/<category>')
@income.route('/export/income/for/<date>/page/<int:page>')
@income.route('/export/income/in/<category>/page/<int:page>')
@income.route('/export/income/for/<date>/in/<category>/page/<int:page>')
@login_required
def export(date=None, category=None, page=1, items_per_page=10):
    '''Export income entries on a filter'''

    model = Income(session.get('logged_in_user'))

    dict = entries.index(**locals())
    for key in dict.keys(): exec(key + " = dict['" + key + "']")

    response = make_response(render_template('admin_export_income.html', **locals()))
    response.headers['Content-type'] = 'text/csv'
    response.headers['Content-disposition'] = 'attachment;filename=' + 'income-' + str(today_date()) + '.csv'
    return response

@income.route('/income/search', methods=['POST'])
@login_required
def search():
    '''Search income'''

    model = Income(session.get('logged_in_user'))

    # query
    query = request.form['q'] if 'q' in request.form else ""

    # fetch entries
    entries = model.get_entries()

    # filter
    entries = entries.filter(IncomeTable.description.like("%"+query+"%"))

    # categories
    categories = model.get_categories()

    # date ranges for the template
    date_ranges = get_date_ranges()

    return render_template('admin_search_income.html', **locals())

@income.route('/income/add', methods=['GET', 'POST'])
@login_required
def add_income():
    '''Add an income entry'''

    current_user_id = session.get('logged_in_user')

    inc = Income(current_user_id)
    acc = Accounts(current_user_id)

    if request.method == 'POST':

        dict = __validate_income_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

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
    accounts = acc.get_accounts()

    return render_template('admin_add_income.html', **locals())

@income.route('/income/edit/<income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    '''Edit income entry'''

    current_user_id = session.get('logged_in_user')

    inc = Income(current_user_id)

    # is it valid?
    income = inc.get_income(income_id)
    if income:
        # fetch user's categories and accounts
        categories = inc.get_categories()

        acc = Accounts(current_user_id)
        accounts = acc.get_accounts()

        if request.method == 'POST': # POST

            dict = __validate_income_form()
            for key in dict.keys(): exec(key + " = dict['" + key + "']")

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

                                # debit the original account
                                acc.modify_account_balance(income.credit_to, -float(income.amount))

                                # credit the 'new' account
                                acc.modify_account_balance(account_id, amount)

                                # edit income entry
                                inc.edit_income(account_id=account_id, amount=amount, category_id=category_id,
                                                             date=date, description=description, income_id=income.id)

                                flash('Income edited')

                                return redirect(url_for('income.edit_income', income_id=income_id))

                            else: error = 'Not a valid account'
                        else: error = 'Not a valid category'
                    else: error = 'Not a valid amount'
                else: error = 'Not a valid date'

        return render_template('admin_edit_income.html', **locals())

    else: return redirect(url_for('income.index'))

@income.route('/income/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    '''Add an income category'''

    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        inc = Income(current_user_id)

        error = entries.add_category(inc, new_category_name)
        if not error: flash('Income category added')

    return render_template('admin_add_income_category.html', error=error)

@income.route('/income/delete/<income_id>')
@login_required
def delete_income(income_id):
    '''Delete income entry'''

    current_user_id = session.get('logged_in_user')
    incomes = Income(current_user_id)

    # is it valid?
    income = incomes.get_income(income_id)
    if income:
        # revert
        accounts = Accounts(current_user_id)
        accounts.modify_account_balance(amount=-float(income.amount), account_id=income.credit_to)

        incomes.delete_income(income_id)

        flash('Income deleted')
    else:
        flash('Not a valid income entry', 'error')


    return redirect(url_for('income.index'))

def __validate_income_form():
    '''Perform basic validation/fetch of add/edit income entry form'''

    error = None

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

    return locals()