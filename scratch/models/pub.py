# coding: utf-8

from sqlalchemy import (Column, Integer, String, DATETIME, Boolean)

from .database import Base
from .base_class import InitUpdate
from ..utils.ex_time import todayfstr


class Pub(Base, InitUpdate):
    """ 对应于数据库的pub表格
    id
    name 酒吧的名字
    intro 基本介绍
    token 随机的字符串
    access_token_time 获取验证的时间
    access_token  服务器获取的验证
    appid 微信号的appid
    secret 微信号的secret
    """

    __tablename__ = 'pub'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    intro = Column(String(256), nullable=True)
    token = Column(String(128), nullable=False)
    access_token = Column(String(128), nullable=True)
    access_token_time = Column(DATETIME, nullable=True)
    appid = Column(String(128), nullable=True)
    secret = Column(String(128), nullable=True)
    address = Column(String(128), nullable=True)
    tel = Column(String(64), nullable=True)
    create_time = Column(DATETIME, nullable=True)
    stop_time = Column(DATETIME, nullable=True)
    status = Column(Boolean, nullable=False)
    base_path = Column(String(128), nullable=True)
    rel_path = Column(String(128), nullable=True)
    pic_name = Column(String(128), nullable=True)
    logo = Column(String(128), nullable=True)

    def __init__(self, **kwargs):
        self.init_value(('name', 'token', 'status'), kwargs)
        self.init_none(('intro', 'stop_time'), kwargs)
        self.create_time = todayfstr()

    def update(self, **kwargs):
        self.update_value(('name', 'intro', 'access_token_time', 'access_token', 'appid', 'secret',
                           'address', 'tel', 'create_time', 'stop_time', 'status'), kwargs)

    def __repr__(self):
        return '<Pub(name: %s)>' % self.name

    def picture_url(self):
        """返回图片的url，相对路径"""
        return str(self.rel_path) + '/' + str(self.pic_name)