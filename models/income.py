# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import desc

# db
from db.database import db_session
from db.database import Base

# utils
from utils import *

class Income():

    user_id = None

    entries = None
    categories = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_entries(self, category_id=None, category_name=None, date_from=None, date_to=None, limit=None):
        if not self.entries:
            self.entries = IncomeTable.query\
            .filter(IncomeTable.user == self.user_id)\
            .join(IncomeCategoriesTable)\
            .add_columns(IncomeCategoriesTable.name, IncomeCategoriesTable.slug)\
            .order_by(desc(IncomeTable.date)).order_by(desc(IncomeTable.id))

        # provided category id
        if category_id:
            self.entries = self.entries.filter(IncomeTable.category == category_id)

        # provided category name
        if category_name:
            self.entries = self.entries.filter(IncomeCategoriesTable.name == category_name)

        # provided date range
        if date_from and date_to:
            self.entries = self.entries.filter(IncomeTable.date >= date_from).filter(IncomeTable.date <= date_to)

        # provided count
        if limit:
            self.entries = self.entries.limit(5)

        return self.entries

    def get_categories(self):
        if not self.categories:
            self.categories = IncomeCategoriesTable.query\
            .filter(IncomeCategoriesTable.user == self.user_id).order_by(IncomeCategoriesTable.name)
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
        c = IncomeCategoriesTable(self.user_id, name)
        db_session.add(c)
        db_session.commit()

class IncomeCategoriesTable(Base):
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

class IncomeTable(Base):
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