#!/usr/bin/python
# -*- coding: utf -*-

# orm
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
db_session = scoped_session(lambda: create_session(bind=engine,
                                                   autoflush=False, autocommit=False, expire_on_commit=True))

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