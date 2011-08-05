#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Blueprint, session
from flask.helpers import make_response

# db
from flask.templating import render_template
from db.database import db_session

# models
from models.accounts import AccountsTable, AccountTransfersTable, Accounts
from models.expenses import ExpenseCategoriesTable, ExpensesTable, ExpensesToLoansTable, Expenses
from models.income import IncomeTable, IncomeCategoriesTable
from models.loans import LoansTable
from models.totals import Totals
from models.users import UsersTable, UsersConnectionsTable, UsersKeysTable, Users

# utils
from utils import slugify

tests = Blueprint('tests', __name__)

@tests.route('/test/create-user/<name>')
def create_user(name):
    '''A test module for creating users in the system'''

    name = name.lower()
    slug = slugify(name)
    u = UsersTable(name.capitalize(), False, slug, slug)
    db_session.add(u)
    db_session.commit()

    return make_response("User created", 200)

@tests.route('/test/get-key')
def get_key():
    '''Get a user key for a logged in user'''

    u = Users(session.get('logged_in_user'))
    # fetch/generate key
    key = u.get_key()

    return make_response(key.key, 200)

@tests.route('/test/wipe-tables')
def wipe_tables():
    '''Make a table cleanup in a database'''

    UsersTable.query.delete()
    UsersConnectionsTable.query.delete()
    UsersKeysTable.query.delete()
    LoansTable.query.delete()
    IncomeCategoriesTable.query.delete()
    IncomeTable.query.delete()
    ExpenseCategoriesTable.query.delete()
    ExpensesTable.query.delete()
    ExpensesToLoansTable.query.delete()
    AccountsTable.query.delete()
    AccountTransfersTable.query.delete()
    #SQLiteSequenceTable.query.delete()
    #db_session.commit()

    return make_response("Tables wiped clean", 200)

@tests.route('/test/dashboard')
def dashboard():
    '''Test budget dashboard'''

    u = UsersTable(u"Admin", False, u"admin", u"admin")
    db_session.add(u)
    db_session.commit()

    current_user_id = u.id

    # get uncategorized expenses
    exp = Expenses(current_user_id)
    uncategorized_expenses = exp.get_entries(category_name="Uncategorized")

    # get latest expenses
    exp = Expenses(current_user_id)
    latest_expenses = exp.get_entries(limit=5)

    # get accounts
    acc = Accounts(current_user_id)
    accounts = acc.get_accounts_and_loans()

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
            if float(a[0].balance) < 0:
                liabilities.append(a)
                liabilities_total += float(a[0].balance)
            else:
                assets.append(a)

    # get the monthly totals
    t = Totals(current_user_id)
    totals = t.get_totals()

    return render_template('admin_dashboard.html', **locals())

#class SQLiteSequenceTable(Base):
#    """SQLite sequence table"""
#
#    __tablename__ = 'sqlite_master'
#    rowid = Column(Integer, primary_key=True)
#    name = Column(String(200))
#    seq = Column(Integer)