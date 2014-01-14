# coding: utf-8

"""普通会员的类"""

from sqlalchemy import (Column, Integer, String, DATETIME, ForeignKey, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DOUBLE

from .database import Base
from .base_class import InitUpdate
from .pub import Pub
from ..utils.ex_time import todayfstr


class User(Base, InitUpdate):
    """普通会员的类
    id 这个是会员的ID同时也是会员卡卡号
    mobile 会员的注册消息，比如电话号码什么的
    sign_up_date 注册时间
    pub_id 关联的酒吧
    open_id 用户的open_id,基本上就是微信的appid
    card_date 领卡时间
    card_status 卡片状态 0 正常 1 冻结
    card_money 剩余的钱
    card_credit 卡片积分
    name 用户姓名
    """

    __tablename__ = 'user'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    mobile = Column(String(16), nullable=False, unique=True)
    sign_up_date = Column(DATETIME, nullable=True)
    pub_id = Column(Integer, ForeignKey(Pub.id, ondelete='cascade', onupdate='cascade'), nullable=False)
    pub = relationship(Pub)
    open_id = Column(String(128), nullable=False)
    card_date = Column(DATETIME, nullable=True)
    card_status = Column(Boolean, nullable=False, default=0, server_default='0')
    card_money = Column(DOUBLE, nullable=False, default=0, server_default='0')
    card_credit = Column(DOUBLE, nullable=False, default=0, server_default='0')
    name = Column(String(16), nullable=True)

    def __init__(self, **kwargs):
        self.sign_up_date = todayfstr()
        self.card_date = todayfstr()
        self.init_value(('mobile', 'pub_id', 'open_id'), kwargs)
        self.init_none(('name',), kwargs)

    def update(self, **kwargs):
        """更新用户数据的函数"""
        self.update_value(('mobile', 'card_status', 'card_money', 'card_credit', 'name'), kwargs)