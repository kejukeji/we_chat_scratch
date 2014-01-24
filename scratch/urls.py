# coding: utf-8

from scratch import app
from flask.ext import restful
# 微信页面
from .views.web import scratch_home
from scratch.restful.verify import weixin
from scratch.views.sjm_login import login_tohome
from scratch.views.sjm_login import login_in
from scratch.views.sjm_login import register,register_action,showusers
from scratch.restful.userlist import UserRestful,UserByNameRestful
app.add_url_rule('/scratch', 'weixin', weixin, methods=('GET', 'POST'))
app.add_url_rule('/scratch/home', 'scratch_home', scratch_home, methods=('GET', 'POST'))
app.add_url_rule('/login','login_tohome', login_tohome,methods=('GET','POST'))
app.add_url_rule('/loginto','login_in',login_in,methods=('GET','POST'))
app.add_url_rule('/register','register',register,methods=('GET','POST'))
app.add_url_rule('/registeraction','register_action',register_action,methods=('GET','POST'))
app.add_url_rule('/show','showusers',showusers,methods=('GET','POST'))


api = restful.Api(app)
api.add_resource(UserRestful, '/restful/user')
api.add_resource(UserByNameRestful,'/restful/name')