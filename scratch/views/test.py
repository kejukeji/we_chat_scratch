# coding: UTF-8

from flask import  request, render_template
from scratch.services.user_services import do_login as do_login_service

def do_login():
    '''到登陆页面'''
    user_name = request.form.get('name')
    user_pass = request.form.get('pass')
    is_true = do_login_service(user_name, user_pass)
    message = 'error'
    if is_true:
        message = 'success'
        return render_template('home.html')
    else:
        return render_template('scratch.html',
                               message=message)
