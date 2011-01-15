# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String, Boolean

# db
from db.database import Base

# utils
from utils import *

class User(Base):
    """User account"""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    associated_with = Column('associated_user_id', Integer, ForeignKey('users.id'))
    is_private = Column(Boolean)
    username = Column(String(20))
    password = Column(String(20))
    slug = Column(String(50))

    def __init__(self, name=None, associated_with=None, is_private=None, username=None, password=None):
        self.name = name
        self.associated_with = associated_with
        self.is_private = is_private
        self.username = username
        self.password = password
        self.slug = slugify(name)

class Account(Base):
    """Represents a user's account to/from which to add/deduct monies"""

    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(100))
    type = Column(String(100))
    balance = Column(Float(precision=2))

    def __init__(self, user=None, name=None, type=None, balance=None):
        self.user = user
        self.name = name
        self.type = type
        self.balance = balance

class AccountTransfer(Base):
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

class IncomeCategory(Base):
    """Income category of a user"""

    __tablename__ = 'income_categories'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(50))
    slug = Column(String(50))

    def __init__(self, user=None, name=None):
        self.user = user
        self.name = name
        self.slug = slugify(name)

class Income(Base):
    """Listing of incomes of various users"""

    __tablename__ = 'income'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    category = Column('category_id', Integer, ForeignKey('income_categories.id'))
    description = Column(String(50))
    credit_to = Column('account_id', Integer, ForeignKey('accounts.id'))
    amount = Column(Float(precision=2))

    def __init__(self, user=None, date=None, category=None, description=None, credit_to=None, amount=None):
        self.user = user
        self.date = date
        self.category = category
        self.description = description
        self.credit_to = credit_to
        self.amount = amount

class ExpenseCategory(Base):
    """Expense category of a user"""

    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(50))
    slug = Column(String(50))

    def __init__(self, user=None, name=None):
        self.user = user
        self.name = name
        self.slug = slugify(name)

class Expense(Base):
    """Listing of expenses of various users"""

    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    category = Column('category_id', Integer, ForeignKey('expense_categories.id'))
    description = Column(String(50))
    deduct_from = Column('account_id', Integer, ForeignKey('accounts.id'))
    amount = Column(Float(precision=2))

    def __init__(self, user=None, date=None, category=None, description=None, deduct_from=None, amount=None):
        self.user = user
        self.date = date
        self.category = category
        self.description = description
        self.deduct_from = deduct_from
        self.amount = amount

class Loan(Base):
    """A loan from one user to another"""

    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    from_user = Column('from_user_id', Integer, ForeignKey('users.id'))
    to_user = Column('to_user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    account = Column('account_id', Integer, ForeignKey('accounts.id'))
    description = Column(String(50))
    amount = Column(Float(precision=2))

    def __init__(self, from_user=None, to_user=None, date=None, account=None, description=None, amount=None):
        self.from_user = from_user
        self.to_user = to_user
        self.date = date
        self.account = account
        self.description = description
        self.amount = amount