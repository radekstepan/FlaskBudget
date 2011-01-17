# orm
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean

# db
from db.database import Base

# utils
from utils import *

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