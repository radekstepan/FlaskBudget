#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy import Column, Integer, String
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql.expression import and_

# db
from db.database import db_session
from db.database import Base

# models
from models.users import UsersTable

# utils
from utils import *

class Slugs(object):

    object = None

    def __init__(self, user_id, user_type=None):
        # determine user type
        if not user_type:
            user_type = 'private' if UsersTable.query\
            .filter(and_(UsersTable.id == user_id, UsersTable.is_private == True)).first() else 'normal'
        if user_type == 'normal':
            self.object = NormalUserSlugs(user_id)
        else:
            self.object = PrivateUserSlugs(user_id)

    def __getattr__(self, name):
        print "calling: ", name, ' on ', self.object
        return getattr(self.object, name)

class SlugsBase:

    user_id = None

    def __init__(self, user_id):
        self.user_id = user_id

    def get_slug(self, slug=None, type=None, object_id=None):
        s = SlugsTable.query.filter(SlugsTable.user == self.user_id).first()
        if slug: s.filter(SlugsTable.slug == slug)
        if type: s.filter(SlugsTable.type == type)
        if object_id: s.filter(SlugsTable.object_id == object_id)

        return s.slug

    def add_slug(self, type, object_id, description=None, slug=None):
        s = SlugsTable(type=type, object_id=object_id, user_id=self.user_id, description=description, slug=slug)
        db_session.add(s)
        db_session.commit()

        return s.slug

class NormalUserSlugs(SlugsBase):
    pass

class PrivateUserSlugs(SlugsBase):

    def get_slug(self, slug=None, type=None, object_id=None):
        return None

    def add_slug(self, type, object_id, description=None, slug=None):
        return None

class SlugsTable(Base):
    """More user friendly slugs used for linking objects"""

    __tablename__ = 'slugs'
    id = Column(Integer, primary_key=True)
    user = Column('user_id', Integer, ForeignKey('users.id'))
    slug = Column(String(35))
    type = Column(String(20))
    object_id = Column(Integer)

    def __init__(self, type, object_id, user_id, description=None, slug=None):
        # slug not provided
        if not slug:
            if description: # slug based on description
                slug = slugify(description)[:30]
            else:
                slug = slugify(type)

            # generate unique key
            r = 'possibly not unique'
            while r:
                # create a new random key
                key = generate_random_key()[:5].lower()
                # test result uniqueness
                r = self.query.filter(SlugsTable.slug == '-'.join([slug, key])).first()
            slug = '-'.join([slug, key])

        self.slug = slug
        self.user = user_id
        self.type = type
        self.object_id = object_id