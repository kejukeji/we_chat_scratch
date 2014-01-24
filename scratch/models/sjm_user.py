# coding: UTF-8

from sqlalchemy import Column, String, Integer
from .database import Base,db
from .base_class import InitUpdate




class   SjmUser(Base, InitUpdate):
    """
    id
    name
    password
    picture
    email
    """
    __tablename__ = 'scra_user'
    
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=True)
    password = Column(String(20), nullable=True)
    picture = Column(String(20), nullable=True)
    email = Column(String(20), nullable=True)

    def __init__(self, **kwargs):
        self.name = kwargs.pop('name','admin')
        self.password = kwargs.pop('password','password')
        self.picture = kwargs.pop('picture','picture')
        self.email = kwargs.pop('email','email')


def query(name, password):
    user = SjmUser.query.filter(SjmUser.name == name, SjmUser.password == password).first()
    if user:
        return True
    else:
        return False

def add(name,password):

    user =SjmUser(name=name,password=password)
    db.add(user)
    try:
        db.commit()
    except:
        return False
    return True

def get_user_all():
    ''''''

    user_count = SjmUser.query.filter().count()
    if user_count > 1:
        users =  SjmUser.query.filter().all()
        return users
    else:
        user = SjmUser.query.filter().first()
        return user


def get_user_by_id(id):
    users =  SjmUser.query.filter(SjmUser.id==id).first()
    return users
def get_user_by_name(name):
    name = '%' +name + '%'

    users_count =SjmUser.query.filter(SjmUser.name.like(name)).count()
    if users_count > 1:
         users =SjmUser.query.filter(SjmUser.name.like(name)).all()
         return users
    else:
         users =SjmUser.query.filter(SjmUser.name.like(name)).first()
         return users



