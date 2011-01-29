#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean

# db
from db.database import db_session
from db.database import Base

# utils
from utils import *

class Users():

    user_id = None
    connections = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_connections(self):
        if not self.connections:
            # fetch users from connections from us
            self.connections = UsersTable.query\
            .join((UsersConnectionsTable, (UsersTable.id == UsersConnectionsTable.to_user)))\
            .filter(UsersConnectionsTable.from_user == self.user_id)
        return self.connections

    def is_connection(self, name=None, user_id=None, slug=None):
        connections = self.get_connections()
        if name:
            for usr in connections:
                if usr.name == name:
                    return usr.id

        elif user_id:
            for usr in connections:
                if usr.id == int(user_id):
                    return usr.id

        elif slug:
            for usr in connections:
                if usr.slug == slug:
                    return usr.id

        return False

    def is_private(self, name=None, user_id=None, slug=None):
        connections = self.get_connections()
        if name:
            for usr in connections:
                if usr.name == name:
                    return True if usr.is_private else False

        elif user_id:
            for usr in connections:
                if usr.id == int(user_id):
                    return True if usr.is_private else False

        elif slug:
            for usr in connections:
                if usr.slug == slug:
                    return True if usr.is_private else False

        return False

    def add_private_user(self, name):
        u = UsersTable(name, True)
        db_session.add(u)
        db_session.commit()
        return u.id

    def add_connection(self, user_id):
        c = UsersConnectionsTable(self.user_id, user_id)
        db_session.add(c)
        c = UsersConnectionsTable(user_id, self.user_id)
        db_session.add(c)
        db_session.commit()

    def validate_key(self, key_value):
        k = UsersKeysTable.query\
        .filter(UsersKeysTable.key == key_value)\
        .filter(UsersKeysTable.expires > today_timestamp()).first()
        return k.user if k else None

    def get_key(self):
        k = UsersKeysTable.query\
        .filter(UsersKeysTable.user == self.user_id)\
        .filter(UsersKeysTable.expires > today_timestamp()).first()
        # generate key
        if not k:
            k = UsersKeysTable(self.user_id)
            db_session.add(k)
            db_session.commit()
        return k

class UsersTable(Base):
    """User account"""

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    is_private = Column(Boolean)
    username = Column(String(20))
    password = Column(String(20))
    slug = Column(String(50))

    def __init__(self, name=None, is_private=None, username=None, password=None):
        self.name = name
        self.is_private = is_private
        self.username = username
        self.password = password
        self.slug = slugify(name)

class UsersConnectionsTable(Base):
    """User connection"""

    __tablename__ = 'users_connections'
    id = Column(Integer, primary_key=True)
    from_user = Column('from_user_id', Integer, ForeignKey('users.id'))
    to_user = Column('to_user_id', Integer, ForeignKey('users.id'))

    def __init__(self, from_user=None, to_user=None):
        self.from_user = from_user
        self.to_user = to_user

class UsersKeysTable(Base):
    """Key generated for a user to connect to"""

    __tablename__ = 'users_keys'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    key = Column(String(50))
    expires = Column(Integer)

    def __init__(self, user=None):
        self.user = user
        # generate random key
        self.key = generate_random_key()
        # expire in 24 hours
        self.expires = tomorrow_timestamp()