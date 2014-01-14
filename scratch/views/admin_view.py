# coding: utf-8

"""后台其他的视图"""

from flask.ext import login
from flask.ext.admin import AdminIndexView, expose


class HomeView(AdminIndexView):
    """定义了后台的首页视图"""

    def __init__(self):
        super(HomeView, self).__init__(template='home.html', name=u'首页')

    @expose("/")
    def index(self):
        try:
            user = login.current_user.name
        except:
            user = None

        return self.render(self._template, user=user)