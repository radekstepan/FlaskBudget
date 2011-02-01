#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Module, session
from flask.helpers import make_response

# db
from db.database import db_session
from db.database import Base
from sqlalchemy import Column, Integer, String

# models
from models.accounts import AccountsTable, AccountTransfersTable
from models.expenses import ExpenseCategoriesTable, ExpensesTable, ExpensesToLoansTable
from models.income import IncomeTable, IncomeCategoriesTable
from models.loans import LoansTable
from models.users import UsersTable, UsersConnectionsTable, UsersKeysTable, Users

# utils
from string import capitalize

tests = Module(__name__)

@tests.route('/test/create-user/<name>')
def create_user(name):
    name = name.lower()
    u = UsersTable(name.capitalize(), False, name, name)
    db_session.add(u)
    db_session.commit()

    return make_response("User created", 200)

@tests.route('/test/get-key')
def get_key():
    u = Users(session.get('logged_in_user'))
    # fetch/generate key
    key = u.get_key()

    return make_response(key.key, 200)

@tests.route('/test/wipe-tables')
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
    #SQLiteSequenceTable.query.delete()
    #db_session.commit()

    return make_response("Tables wiped clean", 200)

#class SQLiteSequenceTable(Base):
#    """SQLite sequence table"""
#
#    __tablename__ = 'sqlite_master'
#    rowid = Column(Integer, primary_key=True)
#    name = Column(String(200))
#    seq = Column(Integer)