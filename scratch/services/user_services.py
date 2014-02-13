# coding: UTF-8


from scratch.models.user import User
from scratch.models.database import db


def inert_user(name, password):
    user = User(name=name, password=password)
    db.add(user)
    try:
        db.commit()
    except:
        print 'error'


def do_login(name, password):
    user = User.query.filter(User.name == name, User.password == password).first()
    if user:
        return True
    else:
        return False


def do_delete(id):
    user = User.query.filter(User.id == id).first()
    db.delete(user)
    db.commit()


def do_update(id):
    user = User.query.filter(User.id == id).first()
    user.card_credit = 100
    db.commit()