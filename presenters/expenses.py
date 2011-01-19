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
from models.accounts import AccountsTable
from models.users import UsersConnectionsTable, UsersTable
from models.loans import LoansTable

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
                    debit_a = AccountsTable.query\
                    .filter(AccountsTable.user == current_user_id)\
                    .filter(AccountsTable.type != 'loan')\
                    .filter(AccountsTable.id == account_id).first()
                    if debit_a:
                    # valid category?
                        if ExpenseCategoriesTable.query\
                        .filter(ExpenseCategoriesTable.user == current_user_id)\
                        .filter(ExpenseCategoriesTable.id == category_id)\
                        .first():

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
                                        if UsersConnectionsTable.query.filter(and_(
                                                UsersConnectionsTable.from_user == current_user_id,
                                                UsersConnectionsTable.to_user == shared_with_user)).first():

                                            # figure out percentage split
                                            loaned_amount = (float(amount)*(100-float(split)))/100
                                            # create a loan
                                            l = LoansTable(current_user_id, shared_with_user, date, account_id,
                                                     description, loaned_amount)
                                            db_session.add(l)
                                            flash('Loan given')

                                            # add new expense (loaner)
                                            e1 = ExpensesTable(current_user_id, date, category_id, description,
                                                         account_id, float(amount) - loaned_amount)
                                            db_session.add(e1)

                                            # add "uncategorized" category if not already present
                                            c = ExpenseCategoriesTable.query\
                                            .filter(ExpenseCategoriesTable.user == shared_with_user)\
                                            .filter(ExpenseCategoriesTable.name == "Uncategorized").first()
                                            if not c:
                                                c = ExpenseCategoriesTable(shared_with_user, u'Uncategorized')
                                                db_session.add(c)
                                                db_session.commit()

                                            # fetch default category (for the borrower)
                                            a = AccountsTable.query\
                                            .filter(AccountsTable.user == shared_with_user)\
                                            .order_by(asc(AccountsTable.id)).first()
                                            deduct_from = a.id

                                            # add new expense (borrower)
                                            e2 = ExpensesTable(shared_with_user, date, c.id, description, deduct_from,
                                                         loaned_amount)
                                            db_session.add(e2)

                                            # add loan account types
                                            __make_loan(current_user_id, shared_with_user, loaned_amount)

                                        else: error = 'Not a valid user sharing with'
                                    else: error = 'Not a valid % split'

                            else:
                            # add new expense
                                e = ExpensesTable(current_user_id, date, category_id, description, account_id, amount)
                                db_session.add(e)

                            if not error:
                            # debit from account
                                debit_a.balance -= float(amount)
                                db_session.add(debit_a)

                                db_session.commit()
                                flash('Expense added')

                        else: error = 'Not a valid category'
                    else: error = 'Not a valid account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch user's categories, accounts and users
    categories = ExpenseCategoriesTable.query.filter(ExpenseCategoriesTable.user == current_user_id).order_by(ExpenseCategoriesTable.name)
    if not categories: error = 'You need to define at least one category'

    accounts = AccountsTable.query.filter(AccountsTable.user == current_user_id).filter(AccountsTable.type != 'loan')
    if not accounts: error = 'You need to define at least one account'

    # fetch users from connections from us
    users = UsersTable.query.join((UsersConnectionsTable, (UsersTable.id == UsersConnectionsTable.to_user)))\
    .filter(UsersConnectionsTable.from_user == current_user_id)

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