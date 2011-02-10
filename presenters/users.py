#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Module, session, render_template, redirect, request, flash

# presenters
from presenters.auth import login_required

# models
from models.users import Users
from models.accounts import Accounts
from models.loans import Loans

# utils
from utils import *

users = Module(__name__)

''' Users '''
@users.route('/user/add-private', methods=['GET', 'POST'])
@login_required
def add_private():
    '''Add a private user connection for a user'''

    error = None
    if request.method == 'POST':
        new_user_name,  current_user_id = request.form['name'], session.get('logged_in_user')

        # setup objects in a context
        useri = Users(current_user_id)

        # blank name?
        if new_user_name:
            # already exists?
            if not useri.is_connection(name=new_user_name):

                # create new private user
                new_user_id = useri.add_private_user(new_user_name)

                # give the user a default account so we can do loans
                acc = Accounts(new_user_id)
                acc.add_default_account()

                # have we provided initial balance?
                if 'balance' in request.form:
                    # get balance
                    balance = request.form['balance']
                    # balance could be "empty"
                    if balance != "":
                        # valid amount?
                        if is_float(balance):
                            balance = float(balance)
                            # do we have a pre-existing balance with the user?
                            if balance != 0:
                                if balance > 0: # they owe us
                                    # models
                                    loa, acc = Loans(current_user_id), Accounts(current_user_id)
                                    # add loan entry
                                    loa.add_loan(other_user_id=new_user_id, date=today_date(),
                                                 account_id=acc.get_default_account(),
                                                 description="Initial balance with the user", amount=balance)
                                    # fudge loan monies balance
                                    acc.modify_loan_balance(amount=balance, with_user_id=new_user_id)
                                else: # we owe them
                                    # models
                                    loa, acc = Loans(new_user_id), Accounts(current_user_id)
                                    # add loan entry
                                    loa.add_loan(other_user_id=current_user_id, date=today_date(),
                                                 account_id=acc.get_default_account(),
                                                 description="Initial balance with the user", amount=-balance)
                                    # fudge loan monies balance
                                    acc.modify_loan_balance(amount=balance, with_user_id=new_user_id)
                        else: error = 'Not a valid amount'

                # create connections from us to them and back
                useri.add_connection(new_user_id)

                flash('Private user added')

            else: error = 'You already have a user under that name'
        else: error = 'You need to provide a name'

    return render_template('admin_add_private_user.html', **locals())

@users.route('/user/connect', methods=['GET', 'POST'])
@login_required
def connect_with_user():
    '''Make a connection with a 'normal' user'''

    error = None
    current_user_id = session.get('logged_in_user')

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'key' in request.form:
            key_value = request.form['key']

            useri = Users(current_user_id)

            key_user_id = useri.validate_key(key_value)

            # valid key
            if key_user_id:
                # cannot connect to ourselves and make a connection that has already been made ;)
                if not key_user_id == current_user_id and not useri.is_connection(user_id=key_user_id):

                    # create connections from us to them and back
                    useri.add_connection(key_user_id)

                    flash('Connection made')

                else: error = 'I can haz myself impossible'
            else: error = 'Invalid key'
        else: error = 'You need to provide a key'

    return render_template('admin_connect_with_user.html', **locals())

@users.route('/user/generate-key', methods=['GET', 'POST'])
@login_required
def generate_key():
    '''Generate/get a user key for the current user'''

    current_user_id = session.get('logged_in_user')

    useri = Users(current_user_id)

    # fetch/generate key
    key = useri.get_key()

    return render_template('admin_generate_user_key.html', **locals())