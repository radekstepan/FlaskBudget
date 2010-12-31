from sqlalchemy import Column, ForeignKey, Integer, Float, String
from db.database import Base

# utils
from datetime import datetime

class User(Base):
    """User account"""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    password = Column(String(20))

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

class Account(Base):
    """Represents a user's account to/from which to add/deduct monies"""

    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(100))
    balance = Column(Float(precision=2))

    def __init__(self, user=None, name=None, balance=None):
        self.user = user
        self.name = name
        self.balance = balance

class ExpenseCategory(Base):
    """Expense category of a user"""

    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(50))

    def __init__(self, user=None, name=None):
        self.user = user
        self.name = name

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
        # convert from datetime into timestamp
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.category = category
        self.description = description
        self.deduct_from = deduct_from
        self.amount = amount