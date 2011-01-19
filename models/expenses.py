# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import desc

# db
from db.database import db_session
from db.database import Base

# utils
from utils import *

class Expenses():

    user_id = None

    entries = None
    categories = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_entries(self, category_id=None, category_name=None, date_from=None, date_to=None, limit=None):
        if not self.entries:
            self.entries = ExpensesTable.query\
            .filter(ExpensesTable.user == self.user_id)\
            .join(ExpenseCategoriesTable)\
            .add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug)\
            .order_by(desc(ExpensesTable.date)).order_by(desc(ExpensesTable.id))

        # provided category id
        if category_id:
            self.entries = self.entries.filter(ExpensesTable.category == category_id)

        # provided category name
        if category_name:
            self.entries = self.entries.filter(ExpenseCategoriesTable.name == category_name)

        # provided date range
        if date_from and date_to:
            self.entries = self.entries.filter(ExpensesTable.date >= date_from).filter(ExpensesTable.date <= date_to)

        # provided count
        if limit:
            self.entries = self.entries.limit(5)

        return self.entries

    def get_categories(self):
        if not self.categories:
            self.categories = ExpenseCategoriesTable.query\
            .filter(ExpenseCategoriesTable.user == self.user_id).order_by(ExpenseCategoriesTable.name)
        return self.categories

    def is_category(self, slug=None, name=None):
        categories = self.get_categories()
        for cat in categories:
            if not slug:
                # assume name
                if cat.name == name:
                    return cat.id
                    break
            else:
                # assume slug
                if cat.slug == slug:
                    return cat.id
                    break

    def add_category(self, name):
        c = ExpenseCategoriesTable(self.user_id, name)
        db_session.add(c)
        db_session.commit()

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