#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Blueprint, session, render_template, redirect, request, flash
from flask.helpers import url_for, make_response
from flask.ext.sqlalchemy import Pagination

# presenters
from presenters.auth import login_required

# models
from models.users import Users
from models.loans import Loans, LoansTable
from models.accounts import Accounts
from models.slugs import Slugs

# utils
from utils import *

loans = Blueprint('loans', __name__)

@loans.route('/loans/')
@loans.route('/loans/made/<direction>')
@loans.route('/loans/with/<user>')
@loans.route('/loans/for/<date>')
@loans.route('/loans/page/<int:page>')
@loans.route('/loans/made/<direction>/page/<int:page>')
@loans.route('/loans/with/<user>/page/<int:page>')
@loans.route('/loans/for/<date>/page/<int:page>')
@loans.route('/loans/made/<direction>/with/<user>')
@loans.route('/loans/made/<direction>/with/<user>/page/<int:page>')
@loans.route('/loans/made/<direction>/for/<date>')
@loans.route('/loans/made/<direction>/for/<date>/page/<int:page>')
@loans.route('/loans/with/<user>/for/<date>')
@loans.route('/loans/with/<user>/for/<date>/page/<int:page>')
@loans.route('/loans/made/<direction>/with/<user>/for/<date>')
@loans.route('/loans/made/<direction>/with/<user>/for/<date>/page/<int:page>')
@login_required
def index(direction=None, user=None, date=None, page=1, items_per_page=10):
    '''List loans user has with other users'''

    current_user_id = session.get('logged_in_user')

    our_loans = Loans(current_user_id)
    our_users = Users(current_user_id)

    # fetch loans
    loans = our_loans.get_loans()

    # fetch users from connections from us
    users = our_users.get_connections()

    # provided user?
    if user:
        # valid slug?
        user_id = our_users.is_connection(slug=user)
        if user_id: loans = our_loans.get_loans(user_id=user_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        loans = our_loans.get_loans(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # provided a direction?
    if direction: loans = our_loans.get_loans(direction=direction)

    # build a paginator
    paginator = Pagination(loans, page, items_per_page, loans.count(),
                           loans.offset((page - 1) * items_per_page).limit(items_per_page))

    return render_template('admin_show_loans.html', **locals())

@loans.route('/export/loans/')
@loans.route('/export/loans/made/<direction>')
@loans.route('/export/loans/with/<user>')
@loans.route('/export/loans/for/<date>')
@loans.route('/export/loans/made/<direction>/with/<user>')
@loans.route('/export/loans/made/<direction>/for/<date>')
@loans.route('/export/loans/with/<user>/for/<date>')
@loans.route('/export/loans/made/<direction>/with/<user>/for/<date>')
@login_required
def export(direction=None, user=None, date=None):
    '''Export loan entries'''

    current_user_id = session.get('logged_in_user')

    our_loans = Loans(current_user_id)
    our_users = Users(current_user_id)

    # fetch loans
    loans = our_loans.get_loans()

    # fetch users from connections from us
    users = our_users.get_connections()

    # provided user?
    if user:
        # valid slug?
        user_id = our_users.is_connection(slug=user)
        if user_id: loans = our_loans.get_loans(user_id=user_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        loans = our_loans.get_loans(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # provided a direction?
    if direction: loans = our_loans.get_loans(direction=direction)

    response = make_response(render_template('admin_export_loans.html', **locals()))
    response.headers['Content-type'] = 'text/csv'
    response.headers['Content-disposition'] = 'attachment;filename=' + 'loans-' + str(today_date()) + '.csv'
    return response

@loans.route('/loans/search', methods=['POST'])
@login_required
def search():
    '''Search loans'''

    current_user_id = session.get('logged_in_user')

    our_loans = Loans(current_user_id)
    our_users = Users(current_user_id)

    # query
    query = request.form['q'] if 'q' in request.form else ""

    # fetch loans
    loans = our_loans.get_loans()

    # filter
    loans = loans.filter(LoansTable.description.like("%"+query+"%"))

    # fetch users from connections from us
    users = our_users.get_connections()

    # date ranges for the template
    date_ranges = get_date_ranges()

    return render_template('admin_search_loans.html', **locals())

@loans.route('/loan/get', methods=['GET', 'POST'])
@login_required
def get():
    '''Get a loan, ie I get money from someone'''

    current_user_id = session.get('logged_in_user')

    our_accounts = Accounts(current_user_id)

    if request.method == 'POST':

        dict = __validate_get_loan_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if our_accounts.is_account(account_id=credit_to_account):

                        # add our loans entry
                        our_loans = Loans(current_user_id)
                        our_loan_id = our_loans.add_loan(other_user_id=from_user, date=date, account_id=credit_to_account,
                                     description=description, amount=amount)

                        # add their loans entry
                        their_loans = Loans(from_user)
                        their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                             account_id=credit_to_account, description=description,
                                                             amount=-float(amount))

                        # generate slugs for the new loans
                        our_slugs = Slugs(current_user_id)
                        slug = our_slugs.add_slug(type='loan', object_id=our_loan_id, description=description)
                        their_slugs = Slugs(from_user)
                        their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)

                        their_accounts = Accounts(from_user)

                        # transfer money from/to respective accounts
                        our_accounts.modify_user_balance(account_id=credit_to_account, amount=amount)
                        their_accounts.modify_user_balance(amount=-float(amount))

                        # fudge loan 'account' monies
                        our_accounts.modify_loan_balance(amount=-float(amount), with_user_id=from_user)
                        their_accounts.modify_loan_balance(amount=amount, with_user_id=current_user_id)

                        flash('Loan received')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch users from connections from us
    our_users = Users(current_user_id)
    users = our_users.get_connections()
    accounts = our_accounts.get_accounts()

    return render_template('admin_get_loan.html', **locals())

@loans.route('/loan/give', methods=['GET', 'POST'])
@login_required
def give():
    '''Give a loan or pay someone back'''

    current_user_id = session.get('logged_in_user')

    our_accounts = Accounts(current_user_id)

    if request.method == 'POST':

        dict = __validate_give_loan_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if our_accounts.is_account(account_id=deduct_from_account):

                        # add our loans entry
                        our_loans = Loans(current_user_id)
                        our_loan_id = our_loans.add_loan(other_user_id=to_user, date=date, account_id=deduct_from_account,
                                     description=description, amount=-float(amount))

                        # add their loans entry
                        their_loans = Loans(to_user)
                        their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                           account_id=deduct_from_account, description=description,
                                                           amount=amount)

                        # generate slugs for the new loans
                        our_slugs = Slugs(current_user_id)
                        slug = our_slugs.add_slug(type='loan', object_id=our_loan_id, description=description)
                        their_slugs = Slugs(to_user)
                        their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)

                        their_accounts = Accounts(to_user)

                        # transfer money from/to respective accounts
                        our_accounts.modify_user_balance(account_id=deduct_from_account, amount=-float(amount))
                        their_accounts.modify_user_balance(amount=amount)

                        # fudge loan 'account' monies
                        our_accounts.modify_loan_balance(amount=amount, with_user_id=to_user)
                        their_accounts.modify_loan_balance(amount=-float(amount), with_user_id=current_user_id)

                        flash('Loan given')

                    else: error = 'Not a valid source account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch users from connections from us
    our_users = Users(current_user_id)
    users = our_users.get_connections()
    accounts = our_accounts.get_accounts()

    return render_template('admin_give_loan.html', **locals())

@loans.route('/loans/edit/<loan_id>', methods=['GET', 'POST'])
@login_required
def edit_loan(loan_id):
    '''Edit loan entry'''

    current_user_id = session.get('logged_in_user')

    our_loans = Loans(current_user_id)

    # is it valid?
    loan = our_loans.get_loan(loan_id)
    if loan:
        if float(loan.amount) > 0:
            return __edit_get_loan(**locals())
        else:
            # make sure we pass absolute value as we don't care about the direction signified anymore
            loan.amount = abs(loan.amount)
            return __edit_give_loan(**locals())

    else: return redirect(url_for('loans.index'))

def __edit_get_loan(loan_id, our_loans, loan, current_user_id):
    '''Editing of loan entries where we were getting money'''

    our_accounts = Accounts(current_user_id)

    if request.method == 'POST': # POST

        dict = __validate_get_loan_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if our_accounts.is_account(account_id=credit_to_account):

                        their_accounts = Accounts(loan.other_user)

                        # first roll back user balances
                        our_accounts.modify_user_balance(account_id=loan.account, amount=-float(loan.amount))
                        their_accounts.modify_user_balance(amount=loan.amount)

                        # now roll back loan account monies
                        our_accounts.modify_loan_balance(amount=loan.amount, with_user_id=loan.other_user)
                        their_accounts.modify_loan_balance(amount=-float(loan.amount), with_user_id=current_user_id)

                        # the user might have changed...
                        if loan.other_user != from_user:
                            their_accounts = Accounts(from_user)

                        # transfer money from/to respective accounts
                        our_accounts.modify_user_balance(account_id=credit_to_account, amount=amount)
                        their_accounts.modify_user_balance(amount=-float(amount))

                        # fudge loan 'account' monies
                        our_accounts.modify_loan_balance(amount=-float(amount), with_user_id=from_user)
                        their_accounts.modify_loan_balance(amount=amount, with_user_id=current_user_id)

                        # get slug as a unique identifier
                        slug = our_loans.get_loan_slug(loan_id=loan_id)

                        # the user might have changed...
                        their_loans = Loans(loan.other_user)
                        if loan.other_user != from_user:
                            # delete their original loan entry (and its slug)
                            their_loans.delete_loan(slug=slug)

                            # new user
                            their_loans = Loans(from_user)
                            their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                                 description=description, amount=-float(amount))

                            # save their new slug
                            their_slugs = Slugs(from_user)
                            their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)
                        else:
                            # update their loans entry
                            their_loans.edit_loan(other_user_id=current_user_id, date=date, description=description,
                                                  amount=amount, slug=slug)

                        # update our loans entry
                        our_loans.edit_loan(other_user_id=from_user, date=date, description=description,
                                              amount=amount, account_id=credit_to_account, loan_id=loan_id)

                        flash('Loan edited')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    our_users = Users(current_user_id)
    users = our_users.get_connections()
    accounts = our_accounts.get_accounts()

    return render_template('admin_edit_get_loan.html', **locals())

def __edit_give_loan(loan_id, our_loans, loan, current_user_id):
    '''Editing of loan entries where we were giving money'''

    our_accounts = Accounts(current_user_id)

    if request.method == 'POST': # POST

        dict = __validate_give_loan_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if our_accounts.is_account(account_id=deduct_from_account):

                        their_accounts = Accounts(loan.other_user)

                        # first roll back user balances
                        our_accounts.modify_user_balance(account_id=loan.account, amount=loan.amount)
                        their_accounts.modify_user_balance(amount=-float(loan.amount))

                        # now roll back loan account monies
                        our_accounts.modify_loan_balance(amount=-float(loan.amount), with_user_id=loan.other_user)
                        their_accounts.modify_loan_balance(amount=loan.amount, with_user_id=current_user_id)

                        # the user might have changed...
                        if loan.other_user != to_user:
                            their_accounts = Accounts(to_user)

                        # transfer money from/to respective accounts
                        our_accounts.modify_user_balance(account_id=deduct_from_account, amount=-float(amount))
                        their_accounts.modify_user_balance(amount=amount)

                        # fudge loan 'account' monies
                        our_accounts.modify_loan_balance(amount=amount, with_user_id=to_user)
                        their_accounts.modify_loan_balance(amount=-float(amount), with_user_id=current_user_id)

                        # get slug as a unique identifier
                        slug = our_loans.get_loan_slug(loan_id=loan_id)

                        # the user might have changed...
                        their_loans = Loans(loan.other_user)
                        if loan.other_user != to_user:
                            # delete their original loan entry (and its slug)
                            their_loans.delete_loan(slug=slug)

                            # new user
                            their_loans = Loans(to_user)
                            their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                                 description=description, amount=amount)

                            # save their new slug
                            their_slugs = Slugs(to_user)
                            their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)
                        else:
                            # update their loans entry
                            their_loans.edit_loan(other_user_id=current_user_id, date=date, description=description,
                                                  amount=amount, slug=slug)

                        # update our loans entry
                        our_loans.edit_loan(other_user_id=to_user, date=date, description=description,
                                            amount=-float(amount), account_id=deduct_from_account, loan_id=loan_id)

                        flash('Loan edited')

                    else: error = 'Not a valid target account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    our_users = Users(current_user_id)
    users = our_users.get_connections()
    accounts = our_accounts.get_accounts()

    return render_template('admin_edit_give_loan.html', **locals())

def __validate_give_loan_form():
    '''Simple validate add/edit give loan entry form'''

    error = None

    # fetch values and check they are actually provided
    if 'user' in request.form: to_user = request.form['user']
    else: error = 'You need to specify to whom to loan'
    if 'date' in request.form: date = request.form['date']
    else: error = 'You need to provide a date'
    if 'deduct_from' in request.form: deduct_from_account = request.form['deduct_from']
    else: error = 'You need to provide an account to deduct from'
    if 'amount' in request.form: amount = request.form['amount']
    else: error = 'You need to provide an amount'
    if 'description' in request.form and request.form['description']: description = request.form['description']
    else: error = 'You need to provide a description'

    return locals()

def __validate_get_loan_form():
    '''Simple validate add/edit get loan entry form'''

    error = None

    # fetch values and check they are actually provided
    if 'user' in request.form: from_user = request.form['user']
    else: error = 'You need to specify from whom to borrow'
    if 'date' in request.form: date = request.form['date']
    else: error = 'You need to provide a date'
    if 'credit_to' in request.form: credit_to_account = request.form['credit_to']
    else: error = 'You need to provide an account to credit to'
    if 'amount' in request.form: amount = request.form['amount']
    else: error = 'You need to provide an amount'
    if 'description' in request.form and request.form['description']: description = request.form['description']
    else: error = 'You need to provide a description'

    return locals()