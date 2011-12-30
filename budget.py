#!/usr/bin/python
# -*- coding: utf -*-

# framework
from __future__ import with_statement
from flask import Flask, session

# models
from db.database import db_session, init_engine

DEBUG = True
app = None

def create_app(db):
    global app

    # create our little application :)
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.secret_key = '98320C8A14B7D50623A8AC1D78D7E9D8F8DF1D390ABEFE3D3263B135493DF250'

    # presenters
    from presenters.dashboard import dashboard
    from presenters.auth import auth
    from presenters.accounts import accounts
    from presenters.income import income
    from presenters.expenses import expenses
    from presenters.loans import loans
    from presenters.users import users

    # register blueprints (presenters)
    app.register_blueprint(dashboard)
    app.register_blueprint(auth)
    app.register_blueprint(accounts)
    app.register_blueprint(income)
    app.register_blueprint(expenses)
    app.register_blueprint(loans)
    app.register_blueprint(users)

    # 'unpresented' models :)
    from models.slugs import SlugsTable

    # initialize the database
    init_engine(db)

    # testing module
    if DEBUG:
        from presenters.tests import tests
        app.register_blueprint(tests)

    @app.after_request
    def shutdown_session(response):
        db_session.remove()
        return response

    # template filters
    @app.template_filter('datetimeformat')
    def date_time_format(value):
        from datetime import date, timedelta

        if date.today() == value:
            return 'Today'
        elif date.today() - timedelta(1) == value:
            return 'Yesterday'
        else:
            return value

    @app.template_filter('timestampformat')
    def timestamp_format(value):
        from datetime import date

        try:
            return date.fromtimestamp(value)
        except ValueError:
            return value

    @app.template_filter('currencyformat')
    def currency_format(value):
        import locale
        locale.setlocale(locale.LC_ALL, '')

        return locale.format("%.2f", value, grouping=True)

    @app.template_filter('csvcurrencyfilter')
    def csv_currency_filter(value):
        return value.replace(',', "")

    @app.template_filter('numberformat')
    def number_format(value):
        return str(value).rstrip('0').rstrip('.')

    @app.template_filter('trimzeroes')
    def trimzeroes(value):
        return value[:len(value)-3]

    @app.template_filter('isloggeduserid')
    def is_logged_user_id(value):
        return value == session.get('logged_in_user')

    @app.template_filter('slugify')
    def slugify(value):
        import unicodedata, re
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
        return re.sub('[-\s]+', '-', value)

    @app.template_filter('csvfilter')
    def csv_filter(value):
        # double quotes
        value = value.replace('"', '""')
        return value

    return app

if __name__ == '__main__':
    app = create_app(db='sqlite:////Volumes/Data/git/budget/db/database.sqlite3')
    app.run()
