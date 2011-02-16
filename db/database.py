#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
# autoflush=False will not update items in a database before query call
# autocommit=False leaves sessions' transaction state on
# expire_on_commit=False will not give us the most recent state of an item after commit()
db_session = scoped_session(lambda: create_session(bind=engine,
                                                   autoflush=False, autocommit=False, expire_on_commit=False))

Base = declarative_base()
Base.query = db_session.query_property()

def init_engine(uri, **kwargs):
    global engine
    engine = create_engine(uri, **kwargs)

    Base.metadata.create_all(bind=engine)

    return engine

# logging
#import logging
#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)