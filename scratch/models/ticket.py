# coding: utf-8

from sqlalchemy import (Column, Integer, String, DATETIME, Boolean, ForeignKey)
from sqlalchemy.orm import relationship
from .database import Base
from .pub import Pub
from .user import User
from .base_class import InitUpdate
from ..utils.ex_time import todayfstr


class Ticket(Base, InitUpdate):
    """
    id
    title 标题
    intro 介绍
    start_time 有效的开始时间
    stop_time 有效的结束时间
    status 状态 0 没有上线 1 上线
    base_path 图片的基路径
    rel_path 图片的相对路径
    pic_name 图片名
    number 优惠券已经领取的人数
    max_number 限量领取的人数 - 如果为0，不限量
    pub_id 优惠券隶属酒吧
    repeat 是否可以重复领取 0不能 1可以
    """

    __tablename__ = 'ticket'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    title = Column(String(32), nullable=False)
    intro = Column(String(256), nullable=False)
    start_time = Column(DATETIME, nullable=False)
    stop_time = Column(DATETIME, nullable=False)
    status = Column(Boolean, nullable=False)
    repeat = Column(Boolean, nullable=False, default=0, server_default='0')
    base_path = Column(String(128), nullable=True)
    rel_path = Column(String(128), nullable=True)
    pic_name = Column(String(128), nullable=True)
    number = Column(Integer, nullable=False, default=0, server_default='0')
    max_number = Column(Integer, nullable=False, default=0, server_default='0')
    pub_id = Column(Integer, ForeignKey(Pub.id, ondelete='cascade', onupdate='cascade'), nullable=False)
    pub = relationship(Pub)

    def __init__(self, **kwargs):
        self.init_value(('title', 'intro', 'start_time', 'stop_time',
                         'status', 'number', 'max_number', 'pub_id', 'repeat'), kwargs)

    def update(self, **kwargs):
        self.update_value(('title', 'intro', 'start_time', 'stop_time',
                           'status', 'number', 'max_number', 'repeat'), kwargs)

    def picture_url(self):
        """返回图片的url，相对路径"""
        return str(self.rel_path) + '/' + str(self.pic_name)


class UserTicket(Base, InitUpdate):
    """
    id
    ticket_id
    user_id
    status 优惠券是否使用 0 没有使用 1 使用
    """

    __tablename__ = 'user_ticket'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey(Ticket.id, ondelete='cascade', onupdate='cascade'), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id, ondelete='cascade', onupdate='cascade'), nullable=False)
    status = Column(Boolean, nullable=False, default=0, server_default='0')