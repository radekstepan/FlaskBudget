from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in_user'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function