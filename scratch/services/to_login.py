# coding: utf-8
from scratch.models.sjm_user import query, get_user_all, get_user_by_id,get_user_by_name
from scratch.models.sjm_user import add
from scratch.utils.others import flatten

def login(name,password):
    is_true = query(name,password)
    return is_true

def get_user_format(success):
    ''''''
    user = get_user_all()
    success['list'] = []
    if user:
        if type(user) is list:
            for u in user:
                user_pic = flatten(u)
                success['list'].append(user_pic)
        else:
            user_pic = flatten(user)
            success['list'].append(user_pic)

def get_user_by_id_format(id, success):
    user = get_user_by_id(id)
    success['list'] = []
    if user:
        user_pic = flatten(user)
        success['list'].append(user_pic)

def get_user_by_name_format(name,success):
    users = get_user_by_name(name)
    success['list'] = []
    if type(users) is list:
        for u in users:
            users_name = flatten(u)
            success['list'].append(users_name)

    else:
        users_name = flatten(users)
        success['list'].append(users_name)





