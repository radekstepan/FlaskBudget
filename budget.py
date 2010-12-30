# framework
from __future__ import with_statement
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash

# models
from db.database import db_session
from models import *

# authentication
from auth import login_required

DEBUG = True
#USERNAME = 'radek'
#PASSWORD = 'radek'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = '98320C8A14B7D50623A8AC1D78D7E9D8F8DF1D390ABEFE3D3263B135493DF250'

@app.after_request
def shutdown_session(response):
    db_session.remove()
    return response

''' Dashboard '''
@app.route('/')
@login_required
def dashboard():
    return redirect(url_for('show_expenses'))

''' Expenses '''
@app.route('/expenses/')
@login_required
def show_expenses():
    return render_template('show_expenses.html', entries=Expense.query
    .filter(Expense.user == session.get('logged_in_user')))

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    error = None
    if request.method == 'POST':
        e = Expense(session.get('logged_in_user'), request.form['date'], request.form['category'],
                    request.form['description'], request.form['amount'])
        db_session.add(e)
        db_session.commit()
        flash('Expense added')
    categories = ExpenseCategory.query.filter(ExpenseCategory.user == session.get('logged_in_user'))\
    .order_by(ExpenseCategory.name)
    return render_template('add_expense.html', **locals())

@app.route('/expense/category/add', methods=['GET', 'POST'])
@login_required
def add_expense_category():
    error = None
    if request.method == 'POST':
        c = ExpenseCategory(session.get('logged_in_user'), request.form['name'])
        db_session.add(c)
        db_session.commit()
        flash('Expense category added')
    return render_template('add_expense_category.html', error=error)

''' Auth '''
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = User.query\
        .filter(User.username == request.form['username'])\
        .filter(User.password == request.form['password']).first()
        if u:
            session['logged_in_user'] = u.id
            flash('You were logged in')
            return redirect(url_for('show_expenses'))
        else:
            error = 'Invalid username and/or password'
    return render_template('login.html', error=error)

@app.route('/add/user/<username>')
def add_user(username):
    u = User(username, username)
    db_session.add(u)
    db_session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in_user', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
