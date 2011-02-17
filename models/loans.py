#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import desc, and_

# db
from db.database import db_session
from db.database import Base

# models
from models.slugs import SlugsTable
from models.users import UsersTable
from models.accounts import AccountsTable, Accounts

class Loans(object):

    object = None

    def __init__(self, user_id, user_type=None):
        # determine user type
        if not user_type:
            user_type = 'private' if UsersTable.query\
            .filter(and_(UsersTable.id == user_id, UsersTable.is_private == True)).first() else 'normal'
        if user_type == 'normal':
            self.object = NormalUserLoans(user_id)
        else:
            self.object = PrivateUserLoans(user_id)

    def __getattr__(self, name):
        print "calling: ", name, ' on ', self.object
        return getattr(self.object, name)

class LoansBase():

    user_id = None

    loans = None

    loan = None # cache

    def __init__(self, user_id):
        self.user_id = user_id

    def get_loans(self, user_id=None, date_from=None, date_to=None, direction=None):
        if not self.loans:
            # table referred to twice, create alias
            self.loans = LoansTable.query\
            .filter(LoansTable.user == self.user_id)\
            .order_by(desc(LoansTable.date)).order_by(desc(LoansTable.id))\
            .join((UsersTable, (LoansTable.other_user == UsersTable.id)))\
            .add_columns(UsersTable.name, UsersTable.slug)

        if user_id:
            self.loans = self.loans.filter(LoansTable.other_user == self.user_id)

        if date_from and date_to:
            self.loans = self.loans.filter(LoansTable.date >= date_from).filter(LoansTable.date <= date_to)

        if direction:
            if direction == 'to-us':
                self.loans = self.loans.filter(LoansTable.amount.startswith('-'))
            elif direction == 'to-them':
                self.loans = self.loans.filter(not LoansTable.amount.startswith('-'))

        return self.loans

    def add_loan(self, other_user_id, date, description, amount, account_id=None):
        # if an account id is not provided, get a 'default' account
        if not account_id:
            accounts = Accounts(self.user_id)
            account_id = accounts.get_default_account()
            # create a default account if no joy getting a default account
            if not account_id:
                account_id = accounts.add_default_account()
        l = LoansTable(self.user_id, other_user_id, date, account_id, description, amount)
        db_session.add(l)
        db_session.commit()

        return l.id

    def get_loan(self, loan_id):
        # if there is no cache or cache id does not match
        if loan_id:
            if not self.loan or self.loan.id != loan_id:
                self.loan = LoansTable.query\
                .filter(and_(LoansTable.user == self.user_id, LoansTable.id == loan_id))\
                .first()

        return self.loan

    def get_loan_slug(self, loan_id):
        s = SlugsTable.query\
        .filter(and_(SlugsTable.object_id == loan_id, SlugsTable.type == 'loan', SlugsTable.user == self.user_id))\
        .first()

        return s.slug

    def edit_loan(self, other_user_id, date, description, amount, loan_id=None, slug=None, account_id=None):
        if slug:
            # find object id first
            s = SlugsTable.query\
            .filter(and_(SlugsTable.slug == slug, SlugsTable.type == 'loan', SlugsTable.user == self.user_id))\
            .first()

            loan_id = s.object_id

        l = self.get_loan(loan_id=loan_id)
        if l:
            # save new values
            l.other_user, l.date, l.description, l.amount = other_user_id, date, description, amount
            # changing the account?
            if account_id: l.account = account_id

            db_session.add(l)
            db_session.commit()

            return l # return so we see the updated values

    def delete_loan(self, loan_id=None, slug=None):
        if slug:
            # find object id first
            s = SlugsTable.query\
            .filter(and_(SlugsTable.slug == slug, SlugsTable.type == 'loan', SlugsTable.user == self.user_id))\
            .first()

            loan_id = s.object_id

        LoansTable.query.filter(and_(LoansTable.user == self.user_id, LoansTable.id == loan_id)).delete()

        SlugsTable.query\
        .filter(and_(SlugsTable.object_id == loan_id, SlugsTable.type == 'loan', SlugsTable.user == self.user_id))\
        .delete()

        db_session.commit()

class NormalUserLoans(LoansBase):
    pass

class PrivateUserLoans(LoansBase):

    def get_loans(self, user_id=None, date_from=None, date_to=None, direction=None):
        return None

    def add_loan(self, other_user_id, date, description, amount, account_id=None):
        return None

    def get_loan(self, loan_id):
        return None

    def get_loan_slug(self, loan_id):
        return None

    def edit_loan(self, other_user_id, date, description, amount, loan_id=None, slug=None, account_id=None):
        return None

    def delete_loan(self, loan_id=None, slug=None):
        return None

class LoansTable(Base):
    """A loan entry for the user
    A loan between two users will correspond to two loan entries where the direction of transfer
    is signified by the positive (user to other_user)/negative (other_user to user)
    """

    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    other_user = Column('other_user_id', Integer, ForeignKey('users.id'))
    date = Column(Integer)
    account = Column('account_id', Integer, ForeignKey('accounts.id'))
    description = Column(String(50))
    amount = Column(Float(precision=2))

    def __init__(self, user=None, other_user=None, date=None, account=None, description=None, amount=None):
        self.user = user
        self.other_user = other_user
        self.date = date
        self.account = account
        self.description = description
        self.amount = amount