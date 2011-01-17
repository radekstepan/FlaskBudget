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

    def __init__(self, user_id):
        self.user_id = user_id

    def get_all(self):
        return AccountsTable.query.filter(AccountsTable.user == self.user_id)\
        .filter(AccountsTable.balance != 0)\
        .outerjoin((UsersTable, AccountsTable.name == UsersTable.id))\
        .add_columns(UsersTable.name, UsersTable.slug)\
        .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))

    def add_default_account(self):
        a = AccountsTable(self.user_id, "Default", 'default', 0)
        db_session.add(a)
        db_session.commit()

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