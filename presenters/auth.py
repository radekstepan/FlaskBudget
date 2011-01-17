# framework
from flask import Module, session, render_template, redirect, request, flash, url_for
from functools import wraps

# models
from models.user import UsersTable

auth = Module(__name__)

''' Auth '''
@auth.route('/login', methods=['GET', 'POST'])
def login():
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
    session.pop('logged_in_user', None)
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in_user'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function