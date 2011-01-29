#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Module, session, render_template
from sqlalchemy.sql.expression import desc, asc

# presenters
from presenters.auth import login_required

# models
from models.expenses import Expenses
from models.accounts import Accounts

dashboard = Module(__name__)

''' Dashboard '''
@dashboard.route('/')
@login_required
def index():
    current_user_id = session.get('logged_in_user')

    # get uncategorized expenses
    exp = Expenses(current_user_id)
    uncategorized_expenses = exp.get_entries(category_name="Uncategorized")

    # get latest expenses
    exp = Expenses(current_user_id)
    latest_expenses = exp.get_entries(limit=5)

    # get accounts
    acc = Accounts(current_user_id)
    accounts = acc.get_accounts_and_loans()

    # split, get totals
    assets, liabilities, loans, assets_total, liabilities_total = [], [], [], 0, 0
    for a in accounts:
        if a[0].type == 'asset':
            assets.append(a)
            assets_total += float(a[0].balance)
        elif a[0].type == 'liability':
            liabilities.append(a)
            liabilities_total += float(a[0].balance)
        elif a[0].type == 'loan':
            # if we owe someone, it is our liability
            if (float(a[0].balance) < 0):
                liabilities.append(a)
                liabilities_total += float(a[0].balance)
            else:
                assets.append(a)

    return render_template('admin_dashboard.html', **locals())