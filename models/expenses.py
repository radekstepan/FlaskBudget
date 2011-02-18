#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import desc, and_

# db
from db.database import db_session
from db.database import Base

# models
from models.accounts import Accounts
from models.totals import Totals
from models.users import UsersTable

# utils
from utils import *

class Expenses(object):

    object = None

    def __init__(self, user_id, user_type=None):
        # determine user type
        if not user_type:
            user_type = 'private' if UsersTable.query\
            .filter(and_(UsersTable.id == user_id, UsersTable.is_private == True)).first() else 'normal'
        if user_type == 'normal':
            self.object = NormalUserExpenses(user_id)
        else:
            self.object = PrivateUserExpenses(user_id)

    def __getattr__(self, name):
        print "calling: ", name, ' on ', self.object
        return getattr(self.object, name)

class ExpensesBase():

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
            self.entries = ExpensesTable.query\
            .filter(ExpensesTable.user == self.user_id)\
            .join(ExpenseCategoriesTable)\
            .add_columns(ExpenseCategoriesTable.name, ExpenseCategoriesTable.slug)\
            .order_by(desc(ExpensesTable.date)).order_by(desc(ExpensesTable.id))\
            .outerjoin(ExpensesToLoansTable)\
            .outerjoin((UsersTable, (UsersTable.id == ExpensesToLoansTable.shared_with)))\
            .add_columns(UsersTable.name, UsersTable.slug)

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
        c = ExpenseCategoriesTable(self.user_id, name)
        db_session.add(c)
        db_session.commit()

    def add_expense(self, date, description, amount, category_id=None, account_id=None):
        # add into uncategorized expenses if category not provided
        if not category_id:
            category_id = self.is_category(name="Uncategorized")
            if not category_id:
                # crete a new one
                c = ExpenseCategoriesTable(self.user_id, u'Uncategorized')
                db_session.add(c)
                db_session.commit()
                category_id = c.id

        # find default account if not provided
        if not account_id:
            acc = Accounts(self.user_id)
            account_id = acc.get_default_account()
            if not account_id:
                account_id = acc.add_default_account()

        # add the actual expense
        e = ExpensesTable(self.user_id, date, category_id, description, account_id, amount)
        db_session.add(e)
        db_session.commit()

        # update the totals
        self.totals.update_expense(amount, date)

        return e.id

    def edit_expense(self, date, description, amount, category_id, account_id, expense_id):
        e = self.get_simple_expense(expense_id)
        if e:
            # update the totals
            self.totals.update_expense(-float(e.amount), e.date)

            e.date, e.category, e.description, e.deduct_from, e.amount = date, category_id, description, account_id,\
                                                                           amount
            db_session.add(e)
            db_session.commit()

            # update the totals
            self.totals.update_expense(amount, date)

            return e # return so we see the updated values

    def get_simple_expense(self, expense_id):
        return ExpensesTable.query\
        .filter(and_(ExpensesTable.user == self.user_id, ExpensesTable.id == expense_id)).first()

    def get_expense(self, expense_id=None, loan_id=None):
        if loan_id:
            # fetch the expense through a loan
            self.entry = ExpensesTable.query\
            .outerjoin(ExpensesToLoansTable)\
            .filter(and_(ExpensesTable.user == self.user_id, ExpensesToLoansTable.loan == loan_id))\
            .add_columns(ExpensesToLoansTable.loan, ExpensesToLoansTable.shared_with, ExpensesToLoansTable.percentage,
                         ExpensesToLoansTable.original_amount)\
            .first()
        else:
            # if there is no cache or cache id does not match
            if not self.entry or self.entry[0].id != expense_id:
                self.entry = ExpensesTable.query\
                .filter(and_(ExpensesTable.user == self.user_id, ExpensesTable.id == expense_id))\
                .outerjoin(ExpensesToLoansTable).add_columns(ExpensesToLoansTable.loan, ExpensesToLoansTable.shared_with,
                                                             ExpensesToLoansTable.percentage,
                                                             ExpensesToLoansTable.original_amount)\
                .first()

        return self.entry

    def delete_expense(self, expense_id):
        e = self.get_expense(expense_id=expense_id)
        # update the totals
        self.totals.update_expense(-float(e[0].amount), e[0].date)

        # delete
        ExpensesTable.query.filter(ExpensesTable.id == expense_id).delete()
        db_session.commit()

    # blindly obey
    def link_to_loan(self, expense_id, loan_id, shared_with, percentage, original_amount):
        l = ExpensesToLoansTable(expense=expense_id, loan=loan_id, shared_with=shared_with, percentage=percentage,
                                 original_amount=original_amount)
        db_session.add(l)
        db_session.commit()

    # blindly obey and delete records for all entries associated with this loan
    def unlink_loan(self, loan_id):
        ExpensesToLoansTable.query\
        .filter(ExpensesToLoansTable.loan == loan_id).delete()
        db_session.commit()

    # blindly obey and delete records for all entries associated with this loan
    def modify_loan_link(self, loan_id, percentage, original_amount):
        le = ExpensesToLoansTable.query.filter(ExpensesToLoansTable.loan == loan_id)
        if le:
            for i in le:
                i.percentage, i.original_amount = percentage, original_amount
                db_session.add(i)
            db_session.commit()

class NormalUserExpenses(ExpensesBase):
    pass

class PrivateUserExpenses(ExpensesBase):
    
    def add_expense(self, date, description, amount, category_id=None, account_id=None):
        return None

    def link_to_loan(self, expense_id, loan_id, shared_with, percentage, original_amount):
        return None

    def get_expense(self, expense_id=None, loan_id=None):
        # so we match the returned list in normal call...
        class Temp(): id=None
        return [Temp()]

    def edit_expense(self, date, description, amount, category_id, account_id, expense_id):
        return None

    def delete_expense(self, expense_id):
        return None

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

class ExpensesToLoansTable(Base):
    """Linking shared expenses together"""

    __tablename__ = 'expenses_to_loans'
    id = Column(Integer, primary_key=True)
    expense = Column('expense_id', Integer, ForeignKey('expenses.id'))
    loan = Column('loan_id', Integer, ForeignKey('loans.id'))
    shared_with = Column('shared_with_user_id', Integer, ForeignKey('users.id')) # shortcut
    percentage = Column(Float(precision=2))
    original_amount = Column(Float(precision=2))

    def __init__(self, expense=None, loan=None, shared_with=None, percentage=None, original_amount=None):
        self.expense = expense
        self.loan = loan
        self.shared_with = shared_with
        self.percentage = percentage
        self.original_amount = original_amount