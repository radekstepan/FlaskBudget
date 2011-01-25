# orm
from sqlalchemy import Column, ForeignKey, Integer, Float, String
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import desc, or_, and_

# db
from db.database import db_session
from db.database import Base

# models
from models.users import UsersTable

class Loans():

    user_id = None

    loans = None

    # preserve aliases when aliasing UsersTable
    alias1 = None
    alias2 = None

    loan = None # cache

    def __init__(self, user_id):
        self.user_id = user_id

    def get_loans(self, user_id=None, date_from=None, date_to=None, direction=None):
        if not self.loans:
            # table referred to twice, create alias
            self.alias1, self.alias2 = aliased(UsersTable), aliased(UsersTable)
            self.loans = LoansTable.query\
            .filter(or_(LoansTable.from_user == self.user_id, LoansTable.to_user == self.user_id))\
            .order_by(desc(LoansTable.date)).order_by(desc(LoansTable.id))\
            .join(
                (self.alias1, (LoansTable.from_user == self.alias1.id)),\
                (self.alias2, (LoansTable.to_user == self.alias2.id)))\
            .add_columns(self.alias1.name, self.alias1.slug, self.alias2.name, self.alias2.slug)

        if user_id:
            self.loans = self.loans.filter(or_(
                    and_(LoansTable.from_user == self.user_id, LoansTable.to_user == user_id),
                    and_(LoansTable.from_user == user_id, LoansTable.to_user == self.user_id)
                    ))

        if date_from and date_to:
            self.loans = self.loans.filter(LoansTable.date >= date_from).filter(LoansTable.date <= date_to)

        if direction:
            if direction == 'to-us':
                self.loans = self.loans.filter(LoansTable.to_user == self.user_id)
            elif direction == 'to-them':
                self.loans = self.loans.filter(LoansTable.from_user == self.user_id)

        return self.loans

    def add_loan(self, other_user_id, date, account_id, description, amount):
        l = LoansTable(self.user_id, other_user_id, date, account_id, description, amount)
        db_session.add(l)
        db_session.commit()

    # works for users in 'both' directions!
    def get_loan(self, loan_id):
        # if there is no cache or cache id does not match
        if not self.loan or self.loan.id != loan_id:
            self.loan = LoansTable.query\
            .filter(or_(LoansTable.from_user == self.user_id, LoansTable.to_user == self.user_id))\
            .filter(LoansTable.id == loan_id).first()

        return self.loan

    # works for users in 'both' directions!
    def edit_loan(self, other_user_id, date, account_id, description, amount, loan_id):
        l = self.get_loan(loan_id)
        if l:
            if other_user_id != self.user_id: # us getting loan
                l.from_user, l.to_user = other_user_id, self.user_id
            else: # us giving a loan
                l.from_user, l.to_user = self.user_id, other_user_id

            l.date, l.account, l.description, l.amount = date, account_id, description, amount

            db_session.add(l)
            db_session.commit()

            return l # return so we see the updated values


class LoansTable(Base):
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