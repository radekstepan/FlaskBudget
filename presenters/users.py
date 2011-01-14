# framework
from flask import Module, session, render_template, redirect, request, flash

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models import *

users = Module(__name__)

''' Users '''
@users.route('/user/add/private', methods=['GET', 'POST'])
@login_required
def add_private():
    error = None
    if request.method == 'POST':
        # blank name?
        if request.form['name']:
            # already exists?
            if not User.query\
                .filter(User.associated_with == session.get('logged_in_user'))\
                .filter(User.name == request.form['name']).first():
                # create new private user associated with the current user
                u = User(request.form['name'], session.get('logged_in_user'), True)
                db_session.add(u)
                db_session.commit()

                # give the user a default account so we can do loans
                a = Account(u.id, "Default", 'default', 0)
                db_session.add(a)

                db_session.commit()
                flash('Private user added')
            else:
                error = 'You already have a user under that name'
        else:
            error = 'You need to provide a name'
    return render_template('admin_add_private_user.html', **locals())