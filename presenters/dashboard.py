#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Blueprint, session, render_template

# presenters
from presenters.auth import login_required

# models
from models.expenses import Expenses
from models.income import Income
from models.accounts import Accounts
from models.totals import Totals

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    '''Budget dashboard'''

    current_user_id = session.get('logged_in_user')

    # get uncategorized expenses
    exp = Expenses(current_user_id)
    uncategorized_expenses = exp.get_entries(category_name="Uncategorized")

    # get latest expenses
    exp = Expenses(current_user_id)
    latest_expenses = exp.get_entries(limit=5)

    # get latest income
    inc = Income(current_user_id)
    latest_income = inc.get_entries(limit=5)

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
            if float(a[0].balance) < 0:
                liabilities.append(a)
                liabilities_total += float(a[0].balance)
            else:
                assets.append(a)

    # monthly totals
    t, totals_list, highest_bar = Totals(current_user_id), [], 0.
    # object to dict
    for total in t.get_totals():
        bar = {}
        bar['month'] = total.month
        if (float(total.expenses) > 0): bar['expenses'] = float(total.expenses)
        if (float(total.income) > 0): bar['income'] = float(total.income)
        totals_list.append(bar)

        if (total.expenses > highest_bar): highest_bar = total.expenses
        if (total.income > highest_bar): highest_bar = total.income

    # calculate height for each bar
    for total in totals_list:
        if 'expenses' in total: total['expenses-height'] = (total['expenses'] / highest_bar) * 100
        if 'income' in total: total['income-height'] = (total['income'] / highest_bar) * 100

    return render_template('admin_dashboard.html', **locals())