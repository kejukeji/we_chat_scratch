# coding: utf-8

"""用户密码相关"""

import hashlib

SALT = '@3wE'


def generate_password(password):
    """password是用户输入的密码，通过salt生成MD5加密的密码"""

    return hashlib.md5(SALT+password).hexdigest()


def check_password(password, enc_password):
    """password是用户输入的密码，enc_password是加密之后的密码"""

    return hashlib.md5(SALT+password).hexdigest() == enc_password