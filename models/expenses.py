# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String

# db
from db.database import Base

# utils
from utils import *
from sqlalchemy.sql.expression import desc

class Expenses():

    user_id = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_uncategorized(self):
        return ExpensesTable.query.filter(ExpensesTable.user == self.user_id)\
        .join(ExpenseCategoriesTable).add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug)\
        .filter(ExpenseCategoriesTable.name == 'Uncategorized').order_by(desc(ExpensesTable.date))

    def get_latest(self):
        return ExpensesTable.query.filter(ExpensesTable.user == self.user_id)\
        .join(ExpenseCategoriesTable).add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug)\
        .order_by(desc(ExpensesTable.date)).limit(5)

class ExpenseCategoriesTable(Base):
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

class ExpensesTable(Base):
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