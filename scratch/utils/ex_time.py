# coding: utf-8

""" 时间处理函数库

    定义了相关的时间处理函数

"""

import datetime


def todayfstr(format_str='%Y-%m-%d %H:%M:%S'):
    """ 获取今天的时间字符串
    比如 "2013-09-09 09:09:23"
    :para format_str: 一个有效的描述时间的格式
    """

    return datetime.datetime.now().strftime(format_str)