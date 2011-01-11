# framework
from __future__ import with_statement
from flask import Flask

# presenters
from presenters.dashboard import dashboard
from presenters.auth import auth
from presenters.accounts import accounts
from presenters.income import income
from presenters.expenses import expenses
from presenters.loans import loans
from presenters.users import users

# models
from db.database import db_session

# utils
from datetime import date, timedelta

DEBUG = True

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = '98320C8A14B7D50623A8AC1D78D7E9D8F8DF1D390ABEFE3D3263B135493DF250'

# register modules (presenters)
app.register_module(dashboard)
app.register_module(auth)
app.register_module(accounts)
app.register_module(income)
app.register_module(expenses)
app.register_module(loans)
app.register_module(users)

@app.after_request
def shutdown_session(response):
    db_session.remove()
    return response

# template filters
@app.template_filter('datetimeformat')
def datetimeformat(value):
    if date.today() == value:
        return 'Today'
    elif date.today() - timedelta(1) == value:
        return 'Yesterday'
    else:
        return value

if __name__ == '__main__':
    app.run()