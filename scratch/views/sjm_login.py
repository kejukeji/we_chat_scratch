# coding: utf-8
from flask import request,render_template,flash
from scratch.services.to_login import login,get_user_format
from scratch.models.sjm_user import add,get_user_all
from scratch.utils.others import success_dic


def login_tohome():
    return render_template('sjm.html')


def login_in():
    name = request.form.get('name')
    password = request.form.get('password')
    if name and password:
        pass
    else:
        flash('用户名或密码为空')
        return render_template('sjm.html')

    if login(name,password):
        return render_template('scratch.html')
    else:
        flash('用户名或密码错误')
        return render_template('sjm.html')

def register():
    return render_template('register.html')
def register_action():
    name = request.form.get('name')
    password = request.form.get('password')
    repassword = request.form.get('repassword')
    if name and password and repassword :
        pass
    else:
        flash('注册信息不能为空！')
        return  render_template('register.html')
    if password != repassword:
        flash('密码不一致，请确认重输入')
        return render_template('register.html')
    else:
        pass
    if add(name,password):
         flash('注册成功，开始登陆！')
         return render_template('sjm.html')
    else:
         flash('注册失败，请重试！')
         return render_template('register.html')
def showusers():
    users = get_user_all()
    return render_template('show.html',users=users)


def oauth():
    '''授权回掉方法'''
    user_name = request.args.get('nickname')
    return render_template('sjm.html',
                           user_name=user_name)













