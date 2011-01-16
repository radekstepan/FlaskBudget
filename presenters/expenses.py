# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc, asc
from flaskext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required
from presenters.loans import __make_loan

# models
from db.database import db_session
from models import *

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
def index(date=None, category=None, page=1, items_per_page=15):
    current_user_id = session.get('logged_in_user')

    # fetch entries
    entries=Expense.query\
    .filter(Expense.user == current_user_id)\
    .join(ExpenseCategory)\
    .add_columns(ExpenseCategory.name, ExpenseCategory.slug)\
    .order_by(desc(Expense.date)).order_by(desc(Expense.id))

    # categories
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == current_user_id).order_by(ExpenseCategory.name)
    # provided category?
    if category:
        # search for the slug
        for cat in categories:
            if cat.slug == category:
                entries = entries.filter(Expense.category == cat.id)
                break

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        entries = entries.filter(Expense.date >= date_range['low']).filter(Expense.date <= date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # build a paginator
    paginator = Pagination(entries, page, items_per_page, entries.count(),
                               entries.offset((page - 1) * items_per_page).limit(items_per_page))

    return render_template('admin_show_expenses.html', **locals())

@expenses.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add():
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
                    debit_a = Account.query\
                    .filter(Account.user == current_user_id)\
                    .filter(Account.type != 'loan')\
                    .filter(Account.id == account_id).first()
                    if debit_a:
                    # valid category?
                        if ExpenseCategory.query\
                        .filter(ExpenseCategory.user == current_user_id)\
                        .filter(ExpenseCategory.id == category_id)\
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
                                        if User.query\
                                        .filter(User.associated_with == current_user_id)\
                                        .filter(User.id == shared_with_user).first():

                                            # figure out percentage split
                                            loaned_amount = (float(amount)*(100-float(split)))/100
                                            # create a loan
                                            l = Loan(current_user_id, shared_with_user, date, account_id,
                                                     description, loaned_amount)
                                            db_session.add(l)
                                            flash('Loan given')

                                            # add new expense (loaner)
                                            e1 = Expense(current_user_id, date, category_id, description,
                                                         account_id, float(amount) - loaned_amount)
                                            db_session.add(e1)

                                            # add "uncategorized" category if not already present
                                            c = ExpenseCategory.query\
                                            .filter(ExpenseCategory.user == shared_with_user)\
                                            .filter(ExpenseCategory.name == "Uncategorized").first()
                                            if not c:
                                                c = ExpenseCategory(shared_with_user, "Uncategorized")
                                                db_session.add(c)
                                                db_session.commit()

                                            # fetch default category (for the borrower)
                                            a = Account.query\
                                            .filter(Account.user == shared_with_user)\
                                            .order_by(asc(Account.id)).first()
                                            deduct_from = a.id

                                            # add new expense (borrower)
                                            e2 = Expense(shared_with_user, date, c.id, description, deduct_from,
                                                         loaned_amount)
                                            db_session.add(e2)

                                            # add loan account types
                                            __make_loan(current_user_id, shared_with_user, loaned_amount)

                                        else: error = 'Not a valid user sharing with'
                                    else: error = 'Not a valid % split'

                            else:
                            # add new expense
                                e = Expense(current_user_id, date, category_id, description, account_id, amount)
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
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == current_user_id).order_by(ExpenseCategory.name)
    if not categories: error = 'You need to define at least one category'

    accounts = Account.query.filter(Account.user == current_user_id).filter(Account.type != 'loan')
    if not accounts: error = 'You need to define at least one account'

    users = User.query.filter(User.associated_with == current_user_id)

    return render_template('admin_add_expense.html', **locals())

@expenses.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        # blank name?
        if new_category_name:
            # already exists?
            if not ExpenseCategory.query\
                .filter(ExpenseCategory.user == current_user_id)\
                .filter(ExpenseCategory.name == new_category_name).first():

                # create category
                c = ExpenseCategory(current_user_id, new_category_name)
                db_session.add(c)
                db_session.commit()
                flash('Expense category added')

            else:
                error = 'You already have a category under that name'
        else:
            error = 'You need to provide a name'

    return render_template('admin_add_expense_category.html', error=error)