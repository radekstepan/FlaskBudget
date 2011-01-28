# framework
from flask import Module
from flask.helpers import make_response

# db
from db.database import db_session

# models
from models.accounts import AccountsTable, AccountTransfersTable
from models.expenses import ExpenseCategoriesTable, ExpensesTable, ExpensesToLoansTable
from models.income import IncomeTable, IncomeCategoriesTable
from models.loans import LoansTable
from models.users import UsersTable, UsersConnectionsTable, UsersKeysTable

tests = Module(__name__)

@tests.route('/test/create_admin')
def create_admin():
    admin = UsersTable(u"Admin", False, "admin", "admin")
    db_session.add(admin)
    db_session.commit()

    return make_response("Admin user created", 200)

@tests.route('/test/wipe_tables')
def wipe_tables():
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
    db_session.commit()

    return make_response("Tables wiped clean", 200)