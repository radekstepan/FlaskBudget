# framework
from flask import Module, session, render_template, redirect, request, flash
from sqlalchemy.sql.expression import desc, asc

# presenters
from presenters.auth import login_required
from presenters.loans import __make_loan

# models
from db.database import db_session
from models import *

expenses = Module(__name__)

''' Expenses '''
@expenses.route('/expenses/')
@login_required
def index():
    return render_template('admin_show_expenses.html', entries=Expense.query
    .filter(Expense.user == session.get('logged_in_user'))
    .join(ExpenseCategory)
    .add_columns(ExpenseCategory.name)
    .order_by(desc(Expense.date)).order_by(desc(Expense.id)))

@expenses.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add():
    error = None
    if request.method == 'POST':
        # is it a shared expense?
        if 'is_shared' in request.form:\
            # figure out percentage split
            loaned_amount = (float(request.form['amount'])*(100-float(request.form['split'])))/100
            # create a loan
            l = Loan(session.get('logged_in_user'), request.form['user'], request.form['date'],
                     request.form['deduct_from'], request.form['description'], loaned_amount)
            db_session.add(l)
            flash('Loan given')

            # add new expense (loaner)
            e1 = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                        request.form['description'], request.form['deduct_from'],
                        float(request.form['amount']) - loaned_amount)
            db_session.add(e1)

            # add "uncategorized" category if not already present (for the borrower to sort out)
            c = ExpenseCategory.query\
            .filter(ExpenseCategory.user == request.form['user'])\
            .filter(ExpenseCategory.name == "Uncategorized").first()
            if not c:
                c = ExpenseCategory(request.form['user'], "Uncategorized")
                db_session.add(c)
                db_session.commit()

            # fetch default category (for the borrower)
            a = Account.query.filter(Account.user == request.form['user']).order_by(asc(Account.id)).first()
            deduct_from = a.id

            # add new expense (borrower)
            e2 = Expense(request.form['user'], request.form['date'], c.id, request.form['description'],
                         deduct_from, loaned_amount)
            db_session.add(e2)

            # add loan account types
            __make_loan(session.get('logged_in_user'), request.form['user'], loaned_amount)
        else:
            # add new expense
            e = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                        request.form['description'], request.form['deduct_from'], request.form['amount'])
            db_session.add(e)

        # debit from account
        a = Account.query\
        .filter(Account.user == session.get('logged_in_user'))\
        .filter(Account.id == request.form['deduct_from']).first()
        a.balance -= float(request.form['amount'])
        db_session.add(a)

        db_session.commit()
        flash('Expense added')

    # fetch user's categories, accounts and users
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == session.get('logged_in_user'))\
    .order_by(ExpenseCategory.name)
    accounts = Account.query.filter(Account.user == session.get('logged_in_user'))
    users = User.query.filter(User.associated_with == session.get('logged_in_user'))
    return render_template('admin_add_expense.html', **locals())

@expenses.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    error = None
    if request.method == 'POST':
        c = ExpenseCategory(session.get('logged_in_user'), request.form['name'])
        db_session.add(c)
        db_session.commit()
        flash('Expense category added')
    return render_template('admin_add_expense_category.html', error=error)