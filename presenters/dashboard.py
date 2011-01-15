# framework
from flask import Module, session, render_template
from sqlalchemy.sql.expression import desc, asc

# presenters
from presenters.auth import login_required

# models
from models import *

dashboard = Module(__name__)

''' Dashboard '''
@dashboard.route('/')
@login_required
def index():
    # get uncategorized expenses
    uncategorized_expenses = Expense.query.filter(Expense.user == session.get('logged_in_user'))\
    .join(ExpenseCategory).add_columns(ExpenseCategory.name, ExpenseCategory.slug)\
    .filter(ExpenseCategory.name == 'Uncategorized').order_by(desc(Expense.date))

    # get latest expenses
    latest_expenses = Expense.query.filter(Expense.user == session.get('logged_in_user'))\
    .join(ExpenseCategory).add_columns(ExpenseCategory.name, ExpenseCategory.slug).order_by(desc(Expense.date)).limit(5)

    # get accounts
    accounts=Account.query.filter(Account.user == session.get('logged_in_user'))\
    .filter(Account.balance != 0)\
    .outerjoin((User, Account.name == User.id))\
    .add_columns(User.name, User.slug)\
    .order_by(asc(Account.type)).order_by(asc(Account.id))

    # split, get totals
    assets, liabilities, loans, assets_total, liabilities_total = [], [], [], 0, 0
    for a in accounts:
        if a[0].type == 'asset':
            assets.append(a)
            assets_total += float(a[0].balance)
        elif a[0].type == 'liability':
            liabilities.append(a)
            liabilities_total += float(a[0].balance)
        elif a[0].type == 'loan':
            # if we owe someone, it is our liability
            if (float(a[0].balance) < 0):
                liabilities.append(a)
                liabilities_total += float(a[0].balance)
            else:
                assets.append(a)

    return render_template('admin_dashboard.html', **locals())