# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import asc

# db
from db.database import db_session
from db.database import Base

# models
from models.users import UsersTable

# utils
from utils import *

class Accounts():

    user_id = None

    accounts = None
    accounts_and_loans = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_accounts(self):
        if not self.accounts:
            self.accounts = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.type != "loan")\
            .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))
        return self.accounts

    def get_accounts_and_loans(self):
        if not self.accounts_and_loans:
            self.accounts_and_loans = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.balance != 0)\
            .outerjoin((UsersTable, AccountsTable.name == UsersTable.id))\
            .add_columns(UsersTable.name, UsersTable.slug)\
            .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))
        return self.accounts_and_loans

    def modify_account_balance(self, account_id, amount):
        account = AccountsTable.query.filter(AccountsTable.id == account_id).first()
        if account:
            account.balance += float(amount)

            db_session.add(account)
            db_session.commit()

    def modify_user_balance(self, amount, account_id=None):
        if not account_id:
            a = AccountsTable.query.filter(AccountsTable.user == self.user_id).filter(AccountsTable.type != "loan")\
            .order_by(asc(AccountsTable.id)).first()
        else:
            a = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.id == account_id).first()

        if a:
            a.balance += float(amount)

            db_session.add(a)
            db_session.commit()

    def modify_loan_balance(self, amount, with_user_id):
        a = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
        .filter(AccountsTable.type == "loan")\
        .filter(AccountsTable.name == with_user_id).first()
        if not a:
            a = AccountsTable(self.user_id, with_user_id, 'loan', float(amount)) # create new
        else:
            a.balance += float(amount) # update

        db_session.add(a)
        db_session.commit()

    def add_default_account(self):
        a = AccountsTable(self.user_id, "Default", 'default', 0)
        db_session.add(a)
        db_session.commit()

    def is_account(self, id):
        accounts = self.get_accounts()

        for acc in accounts:
            if acc.id == int(id):
                return acc.id
                break

class AccountsTable(Base):
    """Represents a user's account to/from which to add/deduct monies"""

    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(100))
    type = Column(String(100))
    balance = Column(Float(precision=2))
    slug = Column(String(100))

    def __init__(self, user=None, name=None, type=None, balance=None):
        self.user = user
        self.name = name
        self.type = type
        self.balance = balance
        # save slug on "normal" accounts
        self.slug = slugify(name) if type == 'asset' or type == 'liability' else None

class AccountTransfersTable(Base):
    """A transfer to/from the account"""

    __tablename__ = 'account_transfers'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    from_account = Column('from_id', Integer, ForeignKey('accounts.id'))
    to_account = Column('to_id', Integer, ForeignKey('accounts.id'))
    amount = Column(Float(precision=2))

    def __init__(self, user=None, date=None, from_account=None, to_account=None, amount=None):
        self.user = user
        self.date = date
        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount