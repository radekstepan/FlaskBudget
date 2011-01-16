# framework
from flask import Module, session, render_template, redirect, request, flash

# presenters
from presenters.auth import login_required

# models
from db.database import db_session
from models import *

# utils
from utils import *

users = Module(__name__)

''' Users '''
@users.route('/user/add-private', methods=['GET', 'POST'])
@login_required
def add_private():
    error = None
    if request.method == 'POST':
        new_user_name, current_user_id = request.form['name'], session.get('logged_in_user')

        # blank name?
        if new_user_name:
            # already exists?
            if not User.query\
                .filter(User.associated_with == current_user_id)\
                .filter(User.name == new_user_name).first():

                # create new private user
                new_user = User(new_user_name, True)
                db_session.add(new_user)
                db_session.commit()

                # give the user a default account so we can do loans
                a = Account(new_user.id, "Default", 'default', 0)
                db_session.add(a)

                # create connections from us to them and back
                c = UserConnection(current_user_id, new_user.id)
                db_session.add(c)
                c = UserConnection(new_user.id, current_user_id)
                db_session.add(c)

                db_session.commit()
                flash('Private user added')

            else:
                error = 'You already have a user under that name'
        else:
            error = 'You need to provide a name'

    return render_template('admin_add_private_user.html', **locals())

@users.route('/user/connect', methods=['GET', 'POST'])
@login_required
def connect_with_user():
    error = None
    current_user_id = session.get('logged_in_user')

    if request.method == 'POST':
        # fetch values and check they are actually provided
        if 'key' in request.form:
            key_value = request.form['key']
            key = UserKey.query.filter(UserKey.key == key_value).filter(UserKey.expires > today_timestamp()).first()
            # valid key
            if key:
                # create connections from us to them and back
                c = UserConnection(current_user_id, new_user.id)
                db_session.add(c)
                c = UserConnection(new_user.id, current_user_id)
                db_session.add(c)

                db_session.commit()
                flash('Connection made')

            else: error = 'Invalid key'
        else: error = 'You need to provide a key'

    return render_template('admin_connect_with_user.html', **locals())

@users.route('/user/generate-key', methods=['GET', 'POST'])
@login_required
def generate_key():
    current_user_id = session.get('logged_in_user')

    # fetch key
    key = UserKey.query.filter(UserKey.user == current_user_id).first()
    # generate key
    if not key:
        key = UserKey(current_user_id)
        db_session.add(key)
        db_session.commit()

    return render_template('admin_generate_user_key.html', **locals())