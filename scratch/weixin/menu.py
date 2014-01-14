# coding: utf-8

from flask import flash
from ..models.pub import Pub
from .webchat import WebChat
from .cons_string import MENU_STRING


def create_menu(pub_id):
    pub = Pub.query.filter(Pub.id == pub_id).first()
    web_chat = WebChat(pub.token)
    web_chat.update(pub.appid, pub.secret)

    menu_string = render_string(pub_id, MENU_STRING)

    try:
        web_chat.create_menu(menu_string)
    except:
        flash(u"创建微信菜单失败，由于网速的问题会有偶尔的失败")


def render_string(pub_id, menu_string):
    url = "http://weixin.kejukeji.com/pub/" + str(pub_id)
    return menu_string.replace("$url$", url)