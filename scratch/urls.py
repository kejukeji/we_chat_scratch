# coding: utf-8

from scratch import app

# 微信页面
from .views.web import scratch_home
app.add_url_rule('/scratch', 'scratch_home', scratch_home, methods=('GET', 'POST'))
