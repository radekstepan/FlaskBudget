#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import desc, and_

# db
from db.database import db_session
from db.database import Base

# models
from models.totals import Totals

# utils
from utils import *

class Income():

    user_id = None

    entries = None
    categories = None

    entry = None # cache

    totals = None

    def __init__(self, user_id):
        self.user_id = user_id

        self.totals = Totals(user_id)

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
            self.entries = self.entries.limit(limit)

        return self.entries

    def get_categories(self):
        if not self.categories:
            self.categories = IncomeCategoriesTable.query\
            .filter(IncomeCategoriesTable.user == self.user_id).order_by(IncomeCategoriesTable.name)
        return self.categories

    def is_category(self, slug=None, name=None, id=None):
        categories = self.get_categories()
        for cat in categories:
            if slug:
                if cat.slug == slug:
                    return cat.id
                    break
            elif name:
                if cat.name == name:
                    return cat.id
                    break
            elif id:
                if cat.id == int(id):
                    return cat.id
                    break

    def add_category(self, name):
        c = IncomeCategoriesTable(self.user_id, name)
        db_session.add(c)
        db_session.commit()

    def add_income(self, account_id, category_id, date, description, amount):
        i = IncomeTable(self.user_id, date, category_id, description, account_id, amount)
        db_session.add(i)
        db_session.commit()

        # update totals
        self.totals.update_income(amount, date)

    def edit_income(self, income_id, account_id, category_id, date, description, amount):
        i = self.get_income(income_id)
        if i:
            # update totals
            self.totals.update_income(-float(i.amount), i.date)

            i.credit_to, i.category, i.date, i.description, i.amount = account_id, category_id, date, description, amount
            db_session.add(i)
            db_session.commit()

            # update totals
            self.totals.update_income(amount, date)

    def get_income(self, income_id):
        # if there is no cache or cache id does not match
        if not self.entry or self.entry.id != income_id:
            self.entry = IncomeTable.query.filter(and_(IncomeTable.user == self.user_id, IncomeTable.id == income_id)).first()

        return self.entry

    def delete_income(self, income_id):
        i = self.get_income(income_id=income_id)
        # update the totals
        self.totals.update_income(-float(i.amount), i.date)

        # delete
        IncomeTable.query.filter(IncomeTable.id == income_id).delete()
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