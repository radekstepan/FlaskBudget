#!/usr/bin/python
# -*- coding: utf -*-

# framework
from flask import Blueprint, session, render_template, redirect, request, flash, url_for
from functools import wraps

# models
from models.users import UsersTable

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''User login'''

    error = None
    if request.method == 'POST':
        u = UsersTable.query\
        .filter(UsersTable.username == request.form['username'])\
        .filter(UsersTable.password == request.form['password'])\
        .filter(UsersTable.is_private == False)\
        .first()
        if u:
            session['logged_in_user'] = u.id
            session['user_name'] = u.name
            flash('You were logged in')
            return redirect(url_for('dashboard.index'))
        else:
            error = 'Invalid username and/or password'
    return render_template('login.html', error=error)

@auth.route('/logout')
def logout():
    '''User logout'''

    session.pop('logged_in_user', None)
    return redirect(url_for('login'))

def login_required(f):
    '''Decorator for functions needing user authentication'''

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in_user'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function