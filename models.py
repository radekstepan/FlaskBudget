from sqlalchemy import Column, ForeignKey, Integer, Float, String
from db.database import Base

# utils
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    password = Column(String(20))

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    name = Column(String(50))

    def __init__(self, user=None, name=None):
        self.user = user
        self.name = name

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    category = Column('category_id', Integer, ForeignKey('expense_categories.id'))
    description = Column(String(50))
    amount = Column(Float(precision=2))

    def __init__(self, user=None, date=None, category=None, description=None, amount=None):
        self.user = user
        # convert from datetime into timestamp
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.category = category
        self.description = description
        self.amount = amount