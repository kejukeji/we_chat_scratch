# coding: utf-8

"""创建数据库"""

from scratch.models import Base, engine

# 必须import类，不然无法创建
from scratch.models.pub import Pub
from scratch.models.admin_user import AdminUser
from scratch.models.user import User
from scratch.models.ticket import Ticket, UserTicket


if __name__ == '__main__':
    Base.metadata.create_all(engine)