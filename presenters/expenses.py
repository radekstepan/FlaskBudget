#!/usr/bin/python
# -*- coding: utf -*-

# framework
from datetime import date
from flask import Blueprint, session, render_template, redirect, request, flash
from flask.helpers import url_for, make_response

# presenters
from presenters.auth import login_required

# models
import entries
from models.expenses import Expenses, ExpensesTable
from models.accounts import Accounts
from models.users import Users
from models.loans import Loans
from models.slugs import Slugs

# utils
from utils import *

expenses = Blueprint('expenses', __name__)

@expenses.route('/expenses/')
@expenses.route('/expenses/for/<date>')
@expenses.route('/expenses/in/<category>')
@expenses.route('/expenses/page/<int:page>')
@expenses.route('/expenses/for/<date>/in/<category>')
@expenses.route('/expenses/for/<date>/page/<int:page>')
@expenses.route('/expenses/in/<category>/page/<int:page>')
@expenses.route('/expenses/for/<date>/in/<category>/page/<int:page>')
@login_required
def index(date=None, category=None, page=1, items_per_page=10):
    '''List expenses for the user'''

    model = Expenses(session.get('logged_in_user'))

    dict = entries.index(**locals())
    for key in dict.keys(): exec(key + " = dict['" + key + "']")

    return render_template('admin_show_expenses.html', **locals())

@expenses.route('/export/expenses/')
@expenses.route('/export/expenses/for/<date>')
@expenses.route('/export/expenses/in/<category>')
@expenses.route('/export/expenses/page/<int:page>')
@expenses.route('/export/expenses/for/<date>/in/<category>')
@expenses.route('/export/expenses/for/<date>/page/<int:page>')
@expenses.route('/export/expenses/in/<category>/page/<int:page>')
@expenses.route('/export/expenses/for/<date>/in/<category>/page/<int:page>')
@login_required
def export(date=None, category=None, page=1, items_per_page=10):
    '''Export expenses on a filter'''

    model = Expenses(session.get('logged_in_user'))

    dict = entries.index(**locals())
    for key in dict.keys(): exec(key + " = dict['" + key + "']")

    response = make_response(render_template('admin_export_expenses.html', **locals()))
    response.headers['Content-type'] = 'text/csv'
    response.headers['Content-disposition'] = 'attachment;filename=' + 'expenses-' + str(today_date()) + '.csv'
    return response

@expenses.route('/expense/search', methods=['POST'])
@login_required
def search():
    '''Search expenses'''

    model = Expenses(session.get('logged_in_user'))

    # query
    query = request.form['q'] if 'q' in request.form else ""

    # fetch entries
    entries = model.get_entries()

    # filter
    entries = entries.filter(ExpensesTable.description.like("%"+query+"%"))

    # categories
    categories = model.get_categories()

    # date ranges for the template
    date_ranges = get_date_ranges()

    return render_template('admin_search_expenses.html', **locals())

@expenses.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    '''Add an expense entry'''

    error = None
    current_user_id = session.get('logged_in_user')

    our_accounts = Accounts(current_user_id)
    our_expenses = Expenses(current_user_id)
    users = Users(current_user_id)

    if request.method == 'POST':
        dict = __validate_expense_form()
        for key in dict.keys(): exec(key + " = dict['" + key + "']")

        # 'heavier' checks
        if not error:
            # valid amount?
            if is_float(amount):
                # valid date?
                if is_date(date):
                    # valid account?
                    if our_accounts.is_account(account_id=account_id):
                        # valid category?
                        if our_expenses.is_category(id=category_id):

                            # is it a shared expense?
                            if 'is_shared' in request.form:
                                # fetch values and check they are actually provided
                                if 'split' in request.form: split = request.form['split']
                                else: error = 'You need to provide a % split'
                                if 'user' in request.form: shared_with_user = request.form['user']
                                else: error = 'You need to provide a user'

                                # 'heavier' checks
                                if not error:
                                    # valid percentage split?
                                    if is_percentage(split):
                                        # valid user sharing with?
                                        if users.is_connection(user_id=shared_with_user):

                                            # figure out percentage split
                                            loaned_amount = round((float(amount)*(100-float(split)))/100, 2)

                                            # create loans
                                            our_loans = Loans(current_user_id)
                                            our_loan_id = our_loans.add_loan(other_user_id=shared_with_user, date=date,
                                                         account_id=account_id, description=description,
                                                         amount=-float(loaned_amount))

                                            our_loans = Loans(shared_with_user)
                                            their_loan_id = our_loans.add_loan(other_user_id=current_user_id, date=date,
                                                         description=description, amount=loaned_amount)

                                            # generate slugs for the new loans
                                            our_slugs = Slugs(current_user_id)
                                            slug = our_slugs.add_slug(type='loan', object_id=our_loan_id,
                                                                      description=description)
                                            their_slugs = Slugs(shared_with_user)
                                            their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)

                                            flash('Loan given')

                                            # add new expense (loaner)
                                            our_expense_id = our_expenses.add_expense(date=date, category_id=category_id,
                                                                               account_id=account_id,
                                                                               amount=float(amount) - loaned_amount,
                                                                               description=description)

                                            # add new expenses (borrower)
                                            their_expenses = Expenses(shared_with_user)
                                            their_expense_id = their_expenses.add_expense(date=date, amount=loaned_amount,
                                                                                   description=description, pass_thru=True)

                                            # fudge loan 'account' monies
                                            our_accounts.modify_loan_balance(amount=loaned_amount,
                                                                             with_user_id=shared_with_user)
                                            their_accounts = Accounts(shared_with_user)
                                            their_accounts.modify_loan_balance(amount=-float(loaned_amount),
                                                                         with_user_id=current_user_id)

                                            # link loan and the expenses (through us)
                                            our_expenses.link_to_loan(expense_id=our_expense_id, loan_id=our_loan_id,
                                                                shared_with=shared_with_user, percentage=split,
                                                                original_amount=amount)
                                            their_expenses.link_to_loan(expense_id=their_expense_id, loan_id=our_loan_id,
                                                                shared_with=current_user_id, percentage=split,
                                                                original_amount=amount)

                                        else: error = 'Not a valid user sharing with'
                                    else: error = 'Not a valid % split'

                            else:
                                # add new expense
                                our_expenses.add_expense(date=date, category_id=category_id, account_id=account_id,
                                                   amount=amount, description=description)

                            if not error:
                                # debit from account
                                our_accounts.modify_user_balance(amount=-float(amount), account_id=account_id)

                                flash('Expense added')

                        else: error = 'Not a valid category'
                    else: error = 'Not a valid account'
                else: error = 'Not a valid date'
            else: error = 'Not a valid amount'

    # fetch user's categories, accounts and users
    categories = our_expenses.get_categories()
    if not categories: error = 'You need to define at least one category'

    accounts = our_accounts.get_accounts()
    if not accounts: error = 'You need to define at least one account'

    # fetch users from connections from us
    users = users.get_connections()

    return render_template('admin_add_expense.html', **locals())

@expenses.route('/expense/edit/<expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    '''Edit expense entry'''

    current_user_id = session.get('logged_in_user')

    our_expenses = Expenses(current_user_id)

    # is it valid?
    expense = our_expenses.get_expense(expense_id)
    if expense:
        error = None

        # early exit for shared expenses from the perspective of the shared with user
        if (expense[0].pass_thru):
            return __edit_pass_thru_expense(**locals())

        our_accounts = Accounts(current_user_id)
        our_users = Users(current_user_id)

        # fetch user's categories, accounts and users
        categories = our_expenses.get_categories()
        if not categories: error = 'You need to define at least one category'

        accounts = our_accounts.get_accounts()
        if not accounts: error = 'You need to define at least one account'

        # fetch users from connections from us
        users = our_users.get_connections()

        # fudge the total for the expense if we have a shared expense
        if expense[1]: expense[0].amount = expense[4]

        if request.method == 'POST':
            dict = __validate_expense_form()
            for key in dict.keys(): exec(key + " = dict['" + key + "']")

            # 'heavier' checks
            if not error:
                # valid amount?
                if is_float(amount):
                    # valid date?
                    if is_date(date):
                        # valid account?
                        if our_accounts.is_account(account_id=account_id):
                            # valid category?
                            if our_expenses.is_category(id=category_id):

                                if expense[1]:
                                    if 'is_shared' in request.form: # shared expense that will be shared
                                        return __edit_shared_expense_into_shared(**locals())
                                    else: # shared expense that will be simple
                                        return __edit_shared_expense_into_simple(**locals())
                                else:
                                    if 'is_shared' in request.form: # simple expense that will be shared
                                        return __edit_simple_expense_into_shared(**locals())
                                    else:  # simple expense that will be shared
                                        return __edit_simple_expense_into_simple(**locals())

                            else: error = 'Not a valid category'
                        else: error = 'Not a valid account'
                    else: error = 'Not a valid date'
                else: error = 'Not a valid amount'

        # show the form
        return render_template('admin_edit_expense.html', **locals())

    else: return redirect(url_for('expenses.index'))

def __edit_pass_thru_expense(current_user_id, our_expenses, expense, expense_id, error):
    '''Edit shared with expense from the perspective of shared with user'''

    # fetch user's categories
    categories = our_expenses.get_categories()
    if not categories: error = 'You need to define at least one category'

    if request.method == 'POST':
        if 'description' in request.form and request.form['description']: description = request.form['description']
        else: error = 'You need to provide a description'
        if 'category' in request.form: category_id = request.form['category']
        else: error = 'You need to provide a category'

        # valid category?
        if our_expenses.is_category(id=category_id):

            our_expenses.edit_pass_thru_expense(description, category_id, expense_id)
            flash('Expense edited')

            # do a GET otherwise category will fail
            return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

        else: error = 'Not a valid category'

    # show the form
    return render_template('admin_edit_pass_thru_expense.html', **locals())

def __edit_simple_expense_into_shared(current_user_id, our_expenses, expense, our_accounts, our_users, date, description,
                                      account_id, amount, error, category_id, categories, accounts, users, expense_id,
                                      key=None, dict=None):
    '''Edit a simple expense entry into a shared one'''

    # fetch values and check they are actually provided
    if 'split' in request.form: split = request.form['split']
    else: error = 'You need to provide a % split'
    if 'user' in request.form: shared_with_user = request.form['user']
    else: error = 'You need to provide a user'

    # 'heavier' checks
    if not error:
        # valid percentage split?
        if is_percentage(split):
            # valid user sharing with?
            if our_users.is_connection(user_id=shared_with_user):

                # figure out percentage split
                loaned_amount = round((float(amount)*(100-float(split)))/100, 2)

                # create loans
                our_loans = Loans(current_user_id)
                our_loan_id = our_loans.add_loan(other_user_id=shared_with_user, date=date,
                                                 account_id=account_id, description=description,
                                                 amount=-float(loaned_amount))

                their_loans = Loans(shared_with_user)
                their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                   description=description, amount=loaned_amount)

                # generate slugs for the new loans
                our_slugs = Slugs(current_user_id)
                slug = our_slugs.add_slug(type='loan', object_id=our_loan_id,
                                          description=description)
                their_slugs = Slugs(shared_with_user)
                their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)

                flash('Loan given')

                # is our original and current account the same?
                if expense[0].deduct_from == account_id:
                    # modify the difference between then and now
                    our_accounts.modify_user_balance(amount=expense[0].amount-float(amount), account_id=account_id)
                else:
                    # credit our original account back
                    our_accounts.modify_user_balance(amount=expense[0].amount, account_id=expense[0].deduct_from)

                    # debit from our current account
                    our_accounts.modify_user_balance(amount=-float(amount), account_id=account_id)

                # edit expense (loaner - us)
                our_expenses.edit_expense(date=date, category_id=category_id, account_id=account_id,
                                          amount=float(amount) - loaned_amount, description=description,
                                          expense_id=expense_id)

                their_expenses = Expenses(shared_with_user)
                their_accounts = Accounts(shared_with_user)

                # add new expenses (borrower)
                their_expense_id = their_expenses.add_expense(date=date, amount=loaned_amount,
                                                              description=description, pass_thru=True)

                # modify their loan account balance
                their_accounts.modify_loan_balance(amount=-float(loaned_amount), with_user_id=current_user_id)

                # modify our loan account balance
                our_accounts.modify_loan_balance(amount=loaned_amount, with_user_id=shared_with_user)

                # link loan and the expenses
                our_expenses.link_to_loan(expense_id=expense_id, loan_id=our_loan_id, shared_with=shared_with_user,
                                          percentage=split, original_amount=amount)
                their_expenses.link_to_loan(expense_id=their_expense_id, loan_id=our_loan_id,
                                            shared_with=current_user_id, percentage=split, original_amount=amount)

                flash('Expense edited')

                # do a GET otherwise category will fail
                return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

            else: error = 'Not a valid user sharing with'
        else: error = 'Not a valid % split'

    # show the form
    return render_template('admin_edit_expense.html', **locals())

def __edit_simple_expense_into_simple(current_user_id, our_expenses, expense, our_accounts, our_users, date, description,
                                      account_id, amount, error, category_id, categories, accounts, users, expense_id,
                                      key=None, dict=None):
    '''Edit a simple expense entry into a simple one, ie without sharing with a user'''

    # credit our account back
    our_accounts.modify_user_balance(amount=expense[0].amount, account_id=expense[0].deduct_from)

    # debit from account
    our_accounts.modify_user_balance(amount=-float(amount), account_id=account_id)

    # edit expense
    our_expenses.edit_expense(date=date, category_id=category_id, account_id=account_id, amount=amount,
                              description=description, expense_id=expense_id)

    flash('Expense edited')

    # do a GET otherwise category will fail
    return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

def __edit_shared_expense_into_shared(current_user_id, our_expenses, expense, our_accounts, our_users, date, description,
                                      account_id, amount, error, category_id, categories, accounts, users, expense_id,
                                      key=None, dict=None):
    '''Edit a shared expense entry into a shared entry still'''

    # fetch values and check they are actually provided
    if 'split' in request.form: split = request.form['split']
    else: error = 'You need to provide a % split'
    if 'user' in request.form: shared_with_user = request.form['user']
    else: error = 'You need to provide a user'

    # 'heavier' checks
    if not error:
        # valid percentage split?
        if is_percentage(split):
            # valid user sharing with?
            if our_users.is_connection(user_id=shared_with_user):

                # figure out percentage split
                loaned_amount = round((float(amount) * (100-float(split)))/100, 2)
                loaned_then_amount = round((float(expense[0].amount) * (100-float(expense[3])))/100, 2)

                # is our original and current account the same?
                if expense[0].deduct_from == account_id:
                    # modify the difference between then and now
                    our_accounts.modify_user_balance(amount=expense[0].amount-float(amount), account_id=account_id)
                else:
                    # credit our original account back
                    our_accounts.modify_user_balance(amount=expense[0].amount, account_id=expense[0].deduct_from)

                    # debit from our current account
                    our_accounts.modify_user_balance(amount=-float(amount), account_id=account_id)

                our_loans = Loans(current_user_id)
                their_loans = Loans(expense[2])

                # get slug as a unique identifier
                slug = our_loans.get_loan_slug(loan_id=expense[1])

                # are we sharing the expense with the same user as before?
                if expense[2] == int(shared_with_user):

                    # edit the loan entries
                    our_loans.edit_loan(other_user_id=shared_with_user, account_id=account_id, description=description,
                                        amount=-float(loaned_amount), date=date, loan_id=expense[1])

                    their_loans.edit_loan(other_user_id=current_user_id, amount=loaned_amount, date=date, slug=slug)

                    # modify our loan account balance difference with the user
                    our_accounts.modify_loan_balance(amount=loaned_amount - loaned_then_amount,
                                                     with_user_id=shared_with_user)

                    # now for the user we share with
                    their_expenses = Expenses(shared_with_user)
                    their_accounts = Accounts(shared_with_user)

                    # the user now and then is the same, get their expense
                    their_expense = their_expenses.get_expense(loan_id=expense[1])

                    # modify their loan account balance
                    their_accounts.modify_loan_balance(amount=-loaned_amount + loaned_then_amount,
                                                       with_user_id=current_user_id)

                    # edit their expense amount
                    their_expenses.edit_expense(date=date, account_id=account_id, amount=loaned_amount,
                                                expense_id=their_expense[0].id, pass_thru=True)

                    # update loan links
                    our_expenses.modify_loan_link(loan_id=expense[1], percentage=split, original_amount=amount)
                    their_expenses.modify_loan_link(loan_id=expense[1], percentage=split, original_amount=amount)

                else:
                    # the other user we WERE sharing with
                    their_expenses = Expenses(expense[2])
                    their_accounts = Accounts(expense[2])

                    # credit our loan account
                    our_accounts.modify_loan_balance(amount=-float(loaned_then_amount), with_user_id=expense[2])

                    # fetch their expense
                    their_expense = their_expenses.get_expense(loan_id=expense[1])

                    # delete the shared user's expense
                    their_expenses.delete_expense(expense_id=their_expense[0].id)

                    # modify their loan status towards us
                    their_accounts.modify_loan_balance(amount=loaned_then_amount, with_user_id=current_user_id)

                    # unlink expenses to loan entries
                    our_expenses.unlink_loan(loan_id=expense[1])

                    # delete the original loans
                    our_loans.delete_loan(loan_id=expense[1])
                    their_loans.delete_loan(slug=slug)

                    flash('Loan reverted')

                    # create a loan from us to the new user
                    our_loan_id = our_loans.add_loan(other_user_id=shared_with_user, date=date, account_id=account_id,
                                                 description=description, amount=-float(loaned_amount))

                    # create a loan entry for the new user
                    their_loans = Loans(shared_with_user)
                    their_loan_id = their_loans.add_loan(other_user_id=current_user_id, date=date,
                                                       description=description, amount=loaned_amount)

                    # generate slugs for the new loans
                    our_slugs = Slugs(current_user_id)
                    slug = our_slugs.add_slug(type='loan', object_id=our_loan_id, description=description)
                    their_slugs = Slugs(shared_with_user)
                    their_slugs.add_slug(type='loan', object_id=their_loan_id, slug=slug)

                    flash('Loan given')

                    # modify loan monies for us
                    our_accounts.modify_loan_balance(amount=loaned_amount, with_user_id=shared_with_user)

                    # the CURRENT user we are sharing with
                    their_accounts = Accounts(shared_with_user)

                    # fudge loan 'account' monies for them
                    their_accounts.modify_loan_balance(amount=-float(loaned_amount), with_user_id=current_user_id)

                    their_expenses = Expenses(shared_with_user)

                    # add new expenses (borrower)
                    their_expense_id = their_expenses.add_expense(date=date, amount=loaned_amount,
                                                                  description=description, pass_thru=True)

                    # create new loan - expense links
                    our_expenses.link_to_loan(expense_id=expense_id, loan_id=our_loan_id, shared_with=shared_with_user,
                                              percentage=split, original_amount=amount)
                    their_expenses.link_to_loan(expense_id=their_expense_id, loan_id=our_loan_id, shared_with=current_user_id,
                                                percentage=split, original_amount=amount)

                # edit expense (loaner - us)
                our_expenses.edit_expense(date=date, category_id=category_id, account_id=account_id,
                                          amount=float(amount) - loaned_amount, description=description,
                                          expense_id=expense_id)

                flash('Expense edited')

                # do a GET otherwise category will fail
                return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

            else: error = 'Not a valid user sharing with'
        else: error = 'Not a valid % split'

    # show the form
    return render_template('admin_edit_expense.html', **locals())

def __edit_shared_expense_into_simple(current_user_id, our_expenses, expense, our_accounts, our_users, date, description,
                                      account_id, amount, error, category_id, categories, accounts, users, expense_id,
                                      key=None, dict=None):
    '''Edit a shared expense entry into a simple expense entry'''

    our_loans = Loans(current_user_id)

    # percentage split
    loaned_then_amount = round((float(expense[0].amount) * (100-float(expense[3])))/100, 2)

    # credit our loan account
    our_accounts.modify_loan_balance(amount=-float(loaned_then_amount), with_user_id=expense[2])

    their_expenses = Expenses(expense[2])
    their_accounts = Accounts(expense[2])
    their_loans = Loans(expense[2])

    # fetch their expense
    their_expense = their_expenses.get_expense(loan_id=expense[1])

    # delete the shared user's expense
    their_expenses.delete_expense(expense_id=their_expense[0].id)

    # delete their loan status towards us
    their_accounts.modify_loan_balance(amount=expense[4], with_user_id=current_user_id)

    # unlink expenses to loan entries
    our_expenses.unlink_loan(loan_id=expense[1])

    # get slug as a unique identifier
    slug = our_loans.get_loan_slug(loan_id=expense[1])

    # delete the original loans
    our_loans.delete_loan(loan_id=expense[1])
    their_loans.delete_loan(slug=slug)

    flash('Loan reverted')

    # credit our account back with the full amount (expense amount + loaned amount)
    our_accounts.modify_user_balance(amount=float(expense[0].amount), account_id=expense[0].deduct_from)

    # debit from account
    our_accounts.modify_user_balance(amount=-float(amount), account_id=account_id)

    # edit expense
    our_expenses.edit_expense(date=date, category_id=category_id, account_id=account_id, amount=amount,
                              description=description, expense_id=expense_id)

    flash('Expense edited')

    # do a GET otherwise category will fail
    return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

@expenses.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    '''Add an expense category'''

    error = None
    if request.method == 'POST':
        new_category_name, current_user_id = request.form['name'], session.get('logged_in_user')

        exp = Expenses(current_user_id)

        error = entries.add_category(exp, new_category_name)
        if not error: flash('Expense category added')

    return render_template('admin_add_expense_category.html', error=error)

def __validate_expense_form():
    '''Basic validation and fetch from an edit expense form'''

    error = None

    # fetch values and check they are actually provided
    if 'amount' in request.form: amount = request.form['amount']
    else: error = 'You need to provide an amount'
    if 'date' in request.form: date = request.form['date']
    else: error = 'Not a valid date'
    if 'deduct_from' in request.form: account_id = request.form['deduct_from']
    else: error = 'You need to provide an account'
    if 'description' in request.form and request.form['description']: description = request.form['description']
    else: error = 'You need to provide a description'
    if 'category' in request.form: category_id = request.form['category']
    else: error = 'You need to provide a category'

    return locals()