# coding: utf-8

from scratch import app

# 微信页面
from .views.web import scratch_home
from scratch.restful.verify import weixin
app.add_url_rule('/scratch', 'weixin', weixin, methods=('GET', 'POST'))
app.add_url_rule('/scratch/home', 'scratch_home', scratch_home, methods=('GET', 'POST'))
