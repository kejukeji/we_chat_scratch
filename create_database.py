# coding: utf-8

"""创建数据库"""

from scratch.models import Base, engine

# 必须import类，不然无法创建
from scratch.models.sjm_user import SjmUser

if __name__ == '__main__':
    Base.metadata.create_all(engine)