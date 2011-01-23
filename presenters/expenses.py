# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc, asc, and_
from flaskext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required
from presenters.loans import __make_loan

# models
from db.database import db_session
from models.expenses import ExpenseCategoriesTable, ExpensesTable, Expenses
from models.accounts import AccountsTable, Accounts
from models.users import UsersConnectionsTable, UsersTable, Users
from models.loans import LoansTable, Loans

# utils
from utils import *

expenses = Module(__name__)

''' Expenses '''
@expenses.route('/expenses/')
@expenses.route('/expenses/for/<date>')
@expenses.route('/expenses/in/<category>')
@expenses.route('/expenses/page/<int:page>')
@expenses.route('/expenses/for/<date>/in/<category>')
@expenses.route('/expenses/for/<date>/page/<int:page>')
@expenses.route('/expenses/in/<category>/page/<int:page>')
@expenses.route('/expenses/for/<date>/in/<category>/page/<int:page>')
@login_required
def index(date=None, category=None, page=1, items_per_page=10):
    current_user_id = session.get('logged_in_user')

    exp = Expenses(current_user_id)

    # fetch entries
    entries = exp.get_entries()

    # categories
    categories = exp.get_categories()
    # provided category?
    if category:
        # search for the slug
        category_id = exp.is_category(slug=category)
        if category_id:
            entries = exp.get_entries(category_id=category_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        entries = exp.get_entries(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # build a paginator
    paginator = Pagination(entries, page, items_per_page, entries.count(),
                               entries.offset((page - 1) * items_per_page).limit(items_per_page))

    return render_template('admin_show_expenses.html', **locals())

@expenses.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    error = None
    current_user_id = session.get('logged_in_user')

    acc_us = Accounts(current_user_id)
    exp_us = Expenses(current_user_id)
    usr = Users(current_user_id)

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'amount' in request.form: amount = request.form['amount']
        else: error = 'You need to provide an amount'
        if 'date' in request.form: date = request.form['date']
        else: error = 'Not a valid date'
        if 'deduct_from' in request.form: account_id = request.form['deduct_from']
        else: error = 'You need to provide an account'
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'
        if 'category' in request.form: category_id = request.form['category']
        else: error = 'You need to provide a category'

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if acc_us.is_account(account_id=account_id):
                        # valid category?
                        if exp_us.is_category(id=category_id):

                            # is it a shared expense?
                            if 'is_shared' in request.form:
                                # fetch values and check they are actually provided
                                if 'split' in request.form: split = request.form['split']
                                else: error = 'You need to provide a % split'
                                if 'user' in request.form: shared_with_user = request.form['user']
                                else: error = 'You need to provide a user'

                                # 'heavier' checks
                                if not error:
                                    # valid percentage split?
                                    if is_percentage(split):
                                        # valid user sharing with?
                                        if usr.is_connection(user_id=shared_with_user):

                                            # figure out percentage split
                                            loaned_amount = (float(amount)*(100-float(split)))/100

                                            # create a loan
                                            loa = Loans(current_user_id)
                                            loa.add_loan(other_user_id=shared_with_user, date=date,
                                                         account_id=account_id, description=description,
                                                         amount=loaned_amount)
                                            flash('Loan given')

                                            # add new expense (loaner)
                                            exp_us.add_expense(date=date, category_id=category_id, account_id=account_id,
                                                            amount=float(amount) - loaned_amount, description=description)

                                            # add new expenses (borrower)
                                            exp_them = Expenses(shared_with_user)
                                            exp_them.add_expense(date=date, amount=loaned_amount, description=description)

                                            # fudge loan 'account' monies
                                            acc_us.modify_loan_balance(amount=loaned_amount, with_user_id=shared_with_user)
                                            acc_them = Accounts(shared_with_user)
                                            acc_them.modify_loan_balance(amount=-float(loaned_amount),
                                                                         with_user_id=current_user_id)

                                        else: error = 'Not a valid user sharing with'
                                    else: error = 'Not a valid % split'

                            else:
                                # add new expense
                                exp_us.add_expense(date=date, category_id=category_id, account_id=account_id,
                                                   amount=amount, description=description)

                            if not error:
                                # debit from account
                                acc_us.modify_user_balance(amount=-float(amount), account_id=account_id)
                                
                                flash('Expense added')

                        else: error = 'Not a valid category'
                    else: error = 'Not a valid account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch user's categories, accounts and users
    categories = exp_us.get_categories()
    if not categories: error = 'You need to define at least one category'

    accounts = acc_us.get_accounts()
    if not accounts: error = 'You need to define at least one account'

    # fetch users from connections from us
    users = usr.get_connections()

    return render_template('admin_add_expense.html', **locals())

@expenses.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        exp = Expenses(current_user_id)

        # blank name?
        if new_category_name:
            # already exists?
            if not exp.is_category(name=new_category_name):

                # create category
                exp.add_category(new_category_name)
                flash('Expense category added')

            else: error = 'You already have a category under that name'
        else: error = 'You need to provide a name'

    return render_template('admin_add_expense_category.html', error=error)