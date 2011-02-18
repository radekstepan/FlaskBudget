#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.sql.expression import and_, asc

# db
from db.database import db_session
from db.database import Base

# utils
from datetime import datetime, timedelta

class Totals():
    '''Totals for a given user'''

    user = None

    def __init__(self, user):
        self.user = user

    def get_totals(self, wayback=6):
        # generate today's month/year string
        m = MonthYear("today")

        # generate a list of month/year strings
        l = [m.substract(x) for x in range(wayback)]
        print l

        # pass it as an IS IN query to totals and return
        return TotalsTable.query\
        .filter(and_(TotalsTable.user == self.user, TotalsTable.month.in_(l)))\
        .order_by(asc(TotalsTable.id)).all()

    def update_expense(self, amount, date):
        # generate a month/year string
        m = MonthYear(date)

        # get the corresponding entry
        t = TotalsTable.query\
        .filter(and_(TotalsTable.user == self.user, TotalsTable.month == str(m))).first()

        if not t:
            # brand spanking new
            t = TotalsTable(self.user, str(m), amount, 0)
        else:
            # update the total
            t.expenses += int(amount)

        # save
        db_session.add(t)
        db_session.commit()

    def update_income(self, amount, date):
        # generate a month/year string
        m = MonthYear(date)

        # get the corresponding entry
        t = TotalsTable.query\
        .filter(and_(TotalsTable.user == self.user, TotalsTable.month == str(m))).first()

        if not t:
            # brand spanking new
            t = TotalsTable(self.user, str(m), 0, amount)
        else:
            # update the total
            t.income += int(amount)

        # save
        db_session.add(t)
        db_session.commit()

class MonthYear():
    '''Represents a wrapper around month/year string'''

    date = None

    def __init__(self, date):
        # setup as a custom month from an entry date string or generate one from today's date
        if date == "today":
            self.date = datetime.now().strftime("%Y-%m")
        else:
            dt = datetime.strptime(date, "%Y-%m-%d")
            self.date = dt.strftime("%Y-%m")

    def __repr__(self):
        # return a string representation of the month
        return self.date

    def substract(self, months):
        # perform arithmetic on a date, -1 will get a correct previous month etc.
        # convert to datetime and substract 1 month
        dt = datetime.strptime(self.date, "%Y-%m")-timedelta(30*months)
        # convert back to string, return
        return dt.strftime("%Y-%m")

class TotalsTable(Base):
    """Monthly expense/income totals for a user"""

    __tablename__ = 'totals'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    month = Column(String(10))
    expenses = Column(Integer)
    income = Column(Integer)

    def __init__(self, user=None, month=None, expenses=None, income=None):
        self.user = user
        self.month = month
        self.expenses = expenses
        self.income = income