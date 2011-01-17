# framework
from flask import Module, session, render_template
from sqlalchemy.sql.expression import desc, asc

# presenters
from presenters.auth import login_required

# models
from models.expense import ExpensesTable, ExpenseCategoriesTable
from models.account import AccountsTable
from models.user import UsersTable

dashboard = Module(__name__)

''' Dashboard '''
@dashboard.route('/')
@login_required
def index():
    # get uncategorized expenses
    uncategorized_expenses = ExpensesTable.query.filter(ExpensesTable.user == session.get('logged_in_user'))\
    .join(ExpenseCategoriesTable).add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug)\
    .filter(ExpenseCategoriesTable.name == 'Uncategorized').order_by(desc(ExpensesTable.date))

    # get latest expenses
    latest_expenses = ExpensesTable.query.filter(ExpensesTable.user == session.get('logged_in_user'))\
    .join(ExpenseCategoriesTable).add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug).order_by(desc(ExpensesTable.date)).limit(5)

    # get accounts
    accounts=AccountsTable.query.filter(AccountsTable.user == session.get('logged_in_user'))\
    .filter(AccountsTable.balance != 0)\
    .outerjoin((UsersTable, AccountsTable.name == UsersTable.id))\
    .add_columns(UsersTable.name, UsersTable.slug)\
    .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))

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