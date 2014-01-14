# coding: utf-8

import datetime


def allowed_file_extension(filename, allowed_extension):
    """检查文件名后缀格式
    :para filename: 文件名
    :para allowed_extension: 允许后缀列表 ['png', 'txt']
    """

    extension = []
    for i in allowed_extension:
        extension.append(i.lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension


def time_file_name(filename, sign=''):
    """返回一个独一无二的文件名，基本就是这样
    :para filename: 原始的文件名
    :para sign: 一个标记，可以是任何的标记，更加保证了独一无二的概率
    """

    for name in ['png', 'gif', 'jpg', 'jpeg']:
        if filename.upper() == name.upper():
            filename = filename + '.' + filename
            break

    return str(datetime.datetime.now()).replace(' ', '_').replace('-', '_').replace(':', '_').replace('.', '_') \
        + str(sign) + filename