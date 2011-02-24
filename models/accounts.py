#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.sql.expression import asc, desc, or_, and_
from sqlalchemy.orm import aliased

# db
from db.database import db_session
from db.database import Base

# models
from models.users import UsersTable

# utils
from utils import *

class Accounts(object):

    object = None

    def __init__(self, user_id, user_type=None):
        # determine user type
        if not user_type:
            user_type = 'private' if UsersTable.query\
            .filter(and_(UsersTable.id == user_id, UsersTable.is_private == True)).first() else 'normal'
        if user_type == 'normal':
            self.object = NormalUserAccounts(user_id)
        else:
            self.object = PrivateUserAccounts(user_id)

    def __getattr__(self, name):
        print "calling: ", name, ' on ', self.object
        return getattr(self.object, name)

class AccountsBase():

    user_id = None

    accounts = None
    accounts_and_loans = None
    transfers = None

    # preserve aliases when aliasing AccountsTable
    alias1 = None
    alias2 = None

    transfer = None # cache

    def __init__(self, user_id):
        self.user_id = user_id

    def get_accounts(self):
        if not self.accounts:
            self.accounts = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.type != "loan")\
            .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))
        return self.accounts

    def get_accounts_and_loans(self):
        if not self.accounts_and_loans:
            self.accounts_and_loans = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.balance != 0)\
            .outerjoin((UsersTable, AccountsTable.name == UsersTable.id))\
            .add_columns(UsersTable.name, UsersTable.slug)\
            .order_by(asc(AccountsTable.type)).order_by(asc(AccountsTable.id))
        return self.accounts_and_loans

    def change_account_balance(self, account_id, amount):
        a = AccountsTable.query.filter(AccountsTable.id == account_id).first()
        if a:
            a.balance = float(amount)

            db_session.add(a)
            db_session.commit()

    def modify_account_balance(self, account_id, amount):
        a = AccountsTable.query.filter(AccountsTable.id == account_id).first()
        if a:
            a.balance += float(amount)

            db_session.add(a)
            db_session.commit()

    def modify_user_balance(self, amount, account_id=None):
        if not account_id:
            a = AccountsTable.query.filter(AccountsTable.user == self.user_id).filter(AccountsTable.type != "loan")\
            .order_by(asc(AccountsTable.id)).first()
        else:
            a = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
            .filter(AccountsTable.id == account_id).first()

        if a:
            a.balance += float(amount)

            db_session.add(a)
            db_session.commit()

    def modify_loan_balance(self, amount, with_user_id):
        a = AccountsTable.query.filter(AccountsTable.user == self.user_id)\
        .filter(AccountsTable.type == "loan")\
        .filter(AccountsTable.name == with_user_id).first()
        if not a:
            a = AccountsTable(self.user_id, with_user_id, 'loan', float(amount)) # create new
        else:
            a.balance += float(amount) # update

        db_session.add(a)
        db_session.commit()

    def get_default_account(self):
        a = AccountsTable.query.filter(AccountsTable.user == self.user_id).order_by(asc(AccountsTable.id)).first()
        if a: return a.id

    def add_default_account(self):
        a = AccountsTable(self.user_id, "Default", 'default', 0)
        db_session.add(a)
        db_session.commit()

        return a.id

    def add_account(self, name, type, balance):
        a = AccountsTable(self.user_id, name, type, balance)
        db_session.add(a)
        db_session.commit()

    def is_account(self, account_id=None, account_slug=None):
        accounts = self.get_accounts()

        if account_id:
            for acc in accounts:
                if acc.id == int(account_id):
                    return acc.id

        elif account_slug:
            for acc in accounts:
                if acc.slug == account_slug:
                    return acc.id

    def add_account_transfer(self, date, deduct_from_account, credit_to_account, amount):
        t = AccountTransfersTable(self.user_id, date, deduct_from_account, credit_to_account, amount)
        db_session.add(t)
        db_session.commit()

    def edit_account_transfer(self, date, deduct_from_account, credit_to_account, amount, transfer_id):
        t = self.get_transfer(transfer_id)
        if t:
            t.date, t.from_account, t.to_account, t.amount = date, deduct_from_account, credit_to_account, amount
            db_session.add(t)
            db_session.commit()

            return t # return so we see the updated values

    def get_account_transfers(self, date_from=None, date_to=None, account_slug=None):
        if not self.transfers:
            # table referred to twice, create alias
            self.alias1, self.alias2 = aliased(AccountsTable), aliased(AccountsTable)
            # fetch account transfers
            self.transfers = AccountTransfersTable.query.filter(AccountTransfersTable.user == self.user_id)\
            .order_by(desc(AccountTransfersTable.date)).order_by(desc(AccountTransfersTable.id))\
            .join(
                    (self.alias1, (AccountTransfersTable.from_account == self.alias1.id)),\
                    (self.alias2, (AccountTransfersTable.to_account == self.alias2.id)))\
            .add_columns(self.alias1.name, self.alias1.slug, self.alias2.name, self.alias2.slug)

        if date_from and date_to:
            self.transfers = self.transfers\
            .filter(AccountTransfersTable.date >= date_from).filter(AccountTransfersTable.date <= date_to)

        if account_slug:
            self.transfers = self.transfers\
            .filter(or_(self.alias1.slug == account_slug, self.alias2.slug == account_slug))

        return self.transfers

    def get_transfer(self, transfer_id):
        # if there is no cache or cache id does not match
        if not self.transfer or self.transfer.id != transfer_id:
            self.transfer = AccountTransfersTable.query\
            .filter(and_(AccountTransfersTable.user == self.user_id, AccountTransfersTable.id == transfer_id)).first()

        return self.transfer

    def delete_transfer(self, transfer_id):
        AccountTransfersTable.query\
            .filter(and_(AccountTransfersTable.user == self.user_id, AccountTransfersTable.id == transfer_id)).delete()
        db_session.commit()

class NormalUserAccounts(AccountsBase):
    pass

class PrivateUserAccounts(AccountsBase):

    def modify_loan_balance(self, amount, with_user_id):
        return None

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