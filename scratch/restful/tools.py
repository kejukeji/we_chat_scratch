# coding: utf-8

from scratch.models.pub import Pub


def get_token(pub_id):
    """通过酒吧id获取酒吧的token"""
    pub = get_pub(pub_id)
    if pub:
        return str(pub.token)
    raise ValueError


def parse_request(request_dict, args):
    """返回一个字典"""
    return_dict = {}
    for arg in args:
        return_dict[arg] = request_dict.get(arg)
    return return_dict


def get_pub(pub_id):
    """通过酒吧id获取酒吧"""
    return Pub.query.filter(Pub.id == pub_id).first()