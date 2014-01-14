# coding: utf-8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from ..setting import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ECHO

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=SQLALCHEMY_ECHO, pool_recycle=3600)
db = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db.query_property()