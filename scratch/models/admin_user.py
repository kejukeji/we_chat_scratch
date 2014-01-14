# coding: utf-8

from sqlalchemy import (Column, Integer, String, DATETIME, ForeignKey)
from sqlalchemy.orm import relationship

from .database import Base
from .pub import Pub
from ..utils.ex_password import generate_password
from ..utils.ex_time import todayfstr
from .base_class import InitUpdate


class AdminUser(Base, InitUpdate):
    """ 对应于数据库的user表格
    id
    name 用户名，如果是管理员就是普通用户名；如果是会员，一般都是手机号
    password 管理员登陆密码；会员没有密码，手机号就OK
    sign_up_date 用户注册时间
    admin 权限控制，不是二进制，纯粹的字符
        1111 超级管理员，就是能够管理所有酒吧的管理员
        1110 普通管理员

         111 酒吧超级管理员，一个酒吧的管理员
         110 酒吧普通管理员

    pub_id 酒吧ID
        超级管理员(1111 1110)没有pub_id，可以管理所有的酒吧
        酒吧管理员需要绑定酒吧ID
    """

    __tablename__ = 'admin_user'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(16), nullable=False, unique=True)
    admin = Column(String(4), nullable=False)
    password = Column(String(64), nullable=None)
    sign_up_date = Column(DATETIME, nullable=True)
    pub_id = Column(Integer, ForeignKey(Pub.id, ondelete='cascade', onupdate='cascade'), nullable=True)
    pub = relationship(Pub)

    def __init__(self, **kwargs):
        self.init_value(('name', 'admin'), kwargs)
        self.init_none(('pub_id',), kwargs)
        self.sign_up_date = todayfstr()
        self.password = self._set_password(kwargs.pop('password'))

    def update(self, **kwargs):
        """更新用户数据的函数"""
        self.update_value(('name', 'admin', 'pub_id'), kwargs)
        self.password = self._update_password(kwargs.pop('password'), self.password)

    def _set_password(self, password):
        """如果密码合法，返回加密后的密码，否则返返回错误"""
        if not self._valid_password(password):
            raise ValueError
        return generate_password(password)

    def _update_password(self, password, enc_password):
        if not self._valid_password(password):
            return enc_password
        if password != enc_password:  # 如果和之前的一样，说明没有变动
            return generate_password(password)
        return enc_password

    def _valid_password(self, password):
        """验证password合法性，不合法返回False，合法返回True"""
        if (password is None) or (not password.strip()):
            return False
        return True

    def check_password(self, new_password):
        """检查密码的正确性"""
        if not self._valid_password(new_password):
            return False
        if self.password == generate_password(new_password):
            return True
        return False

    def is_superuser(self):
        """猫吧超级超级管理员权限"""
        if self.admin == '1111':
            return True
        return False

    def is_normal_superuser(self):
        """猫吧普通管理员权限"""
        if self.admin == '1111' or self.admin == '1110':
            return True
        return False

    def is_manageruser(self):
        """酒吧超级管理员权限"""
        if self.admin == '111':
            return True
        return False

    def is_normal_manageruser(self):
        """酒吧普通管理员权限"""
        if self.admin == '111' or self.admin == '110':
            return True
        return False

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<AdminUser(name: %s)>' % self.name