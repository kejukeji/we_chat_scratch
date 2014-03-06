# coding: utf-8

"""微信验证相关的函数"""

from flask import request, make_response
from xml.etree import ElementTree as ET
from .tools import get_token, parse_request
from ..weixin.webchat import WebChat
from .tools import get_pub
from ..setting import BASE_URL
from ..models.user import User
from ..weixin.cons_string import (BIND_ERROR_FORMAT, ALREADY_BIND, BIND_SUCCESS,
                                  NOT_BIND, CHANGE_ERROR_FORMAT, CHANGE_SUCCESS, CHANGE_NONE,
                                  ALREADY_EXIST, NO_ACTIVITY)
from ..models import db
from ..models.ticket import Ticket, UserTicket
import datetime


def weixin():
    web_chat = WebChat('7072')
    if request.method == "GET":
        if web_chat.validate(**parse_request(request.args, ("timestamp", "nonce", "signature"))):
            return make_response(request.args.get("echostr"))
        raise LookupError

    if request.method == "POST":
        # 这里需要验证 #todo
        xml_recv = ET.fromstring(request.data)
        MsgType = xml_recv.find("MsgType").text

        if MsgType == "event":
            return response_event(xml_recv, web_chat, 1)
        if MsgType == "text":
            return response_text(xml_recv, web_chat, 1)
        if MsgType == 'voice':
            return response_voice(xml_recv, web_chat)


def response_voice(xml_receive, web_chat):
    '''对于用户语音进行处理'''
    recognition = xml_receive.find("Recognition").text
    toUserName = xml_receive.find("ToUserName").text # 得到接受者
    fromUserName = xml_receive.find("FromUserName").text # 得到发送者
    reply_dict = {
        "ToUserName": fromUserName,
        "FromUserName": toUserName,
        "CreateTime": 12345,
        "Content": recognition
    }
    return response(web_chat, reply_dict, 'text')


def response_text(xml_recv, web_chat, pub_id):
    """对于用户的输入进行回复"""
    Content = xml_recv.find("Content").text
    input_type = get_type(Content)

    if input_type in ('jia', 'gai'):
        return response_member_text(xml_recv, web_chat, pub_id, input_type)
    if input_type in ("授权"):
        return response_address(xml_recv, web_chat)
    if input_type in ("地址"):
        return response_address(xml_recv, web_chat)

    # 下面的句子是鹦鹉学舌，后期改过来
    ToUserName = xml_recv.find("ToUserName").text
    FromUserName = xml_recv.find("FromUserName").text

    reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "ArticleCount": 1,
            "item": [{
                "Title": '刮刮',
                "Description": '好玩',
                "PicUrl": BASE_URL + '/static/images/scratch_matter.jpg',
                "Url": BASE_URL + '/scratch/home'
            }]
    }
    return response(web_chat, reply_dict, "news")


def response_oauth(xml_receive, web_chat):
    '''授权'''
    Content = xml_receive.find("Content").text
    ToUserName = xml_receive.find("ToUserName").text
    FromUserName = xml_receive.find("FromUserName").text
    Content = '<a href="https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxd66b61798e08ff5e&redirect_uri=http%3A%2F%2Fscratch.kejukeji.com%2Foauth_info&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect">点击授权</a>'
    reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "CreateTime": 1,
            "Content": Content

    }
    return response(web_chat, reply_dict, "text")


def response_address(xml_receive, web_chat):
    '''获取地理位置'''
    ToUserName = xml_receive.find("ToUserName").text
    FromUserName = xml_receive.find("FromUserName").text
    Content = '<a href="http://www.w3school.com.cn/tiy/t.asp?f=html5_geolocation">坐标</a>'
    reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "CreateTime": 1,
            "Content": Content

    }
    return response(web_chat, reply_dict, "text")


def response_event(xml_recv, web_chat, pub_id):
    Event = xml_recv.find("Event").text
    EventKey = xml_recv.find("EventKey").text
    ToUserName = xml_recv.find("ToUserName").text
    FromUserName = xml_recv.find("FromUserName").text

    if (Event == 'CLICK') and (EventKey == 'story'):
        pub = get_pub(pub_id)
        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "ArticleCount": 1,
            "item": [{
                "Title": str(pub.name),
                "Description": str(pub.intro),
                "PicUrl": BASE_URL+pub.picture_url(),
                "Url": url(pub_id)
            }]
        }

        return response(web_chat, reply_dict, "news")

    if (Event == 'CLICK') and (EventKey == 'member'):
        old_mobile = already_bind(FromUserName, pub_id)
        if old_mobile != "None":
            message = BIND_SUCCESS
        else:
            message = NOT_BIND

        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "Content": message.replace('MOBILE', old_mobile)
        }
        return response(web_chat, reply_dict, "text")

    if (Event == 'CLICK') and (EventKey == 'activity'):
        pub = get_pub(pub_id)
        reply_dict, reply_type = activity_reply(pub, xml_recv)
        return response(web_chat, reply_dict, reply_type)


def response(web_chat, reply_dict, reply_type):
    reply = web_chat.reply(reply_type, reply_dict)
    reply_response = make_response(reply)
    reply_response.content_type = 'application/xml'
    return reply_response


def url(pub_id):
    return BASE_URL+"/pub/"+str(pub_id)


def get_type(Content):
    """返回用户输入的业务类型
    "jia" 或者 "gai" 值得是用户进行手机号码绑定与修改手机号码
    None 未知类型，不是相关的业务
    """

    if Content.startswith("jia"):
        return "jia"
    if Content.startswith("gai"):
        return "gai"
    if Content.startswith("授权"):
        return "授权"


def response_member_text(xml_recv, web_chat, pub_id, input_type):
    """如果用户输入jia或者是gai手机号码，这里进行判断"""
    Content = xml_recv.find("Content").text
    ToUserName = xml_recv.find("ToUserName").text
    FromUserName = xml_recv.find("FromUserName").text
    mobile = Content[3:]

    if not mobile.isdigit():  # 判断输入的格式是否正确
        if input_type == "jia":
            message = BIND_ERROR_FORMAT
        else:
            message = CHANGE_ERROR_FORMAT
        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "Content": message
        }
        return response(web_chat, reply_dict, "text")

    old_mobile = already_bind(FromUserName, pub_id)
    repeat = User.query.filter(User.mobile == mobile).count()

    if old_mobile != "None":  # 如果已经绑定过手机号
        if input_type == "jia":
            message = ALREADY_BIND.replace('MOBILE', old_mobile)
        else:
            if (mobile == old_mobile) or (not repeat):
                change_mobile(FromUserName, pub_id, mobile)
                message = CHANGE_SUCCESS.replace('MOBILE', mobile)
            else:
                message = ALREADY_EXIST.replace('MOBILE', mobile)

        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "Content": message
        }
        return response(web_chat, reply_dict, "text")
    else:  # 如果没有绑定过
        if input_type == 'jia':
            if not repeat:
                user = User(mobile=mobile, pub_id=pub_id, open_id=FromUserName)
                db.add(user)
                db.commit()
                message = BIND_SUCCESS.replace('MOBILE', mobile)
            else:
                message = ALREADY_EXIST.replace('MOBILE', mobile)
        else:
            message = CHANGE_NONE

        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "Content": message
        }
        return response(web_chat, reply_dict, "text")


def already_bind(open_id, pub_id):
    """判断是否绑定了手机号，如果绑定了返回手机号，如果没有返回None"""
    user = User.query.filter(User.open_id == open_id, User.pub_id == pub_id).first()
    if user:
        return str(user.mobile)
    return str(None)


def change_mobile(open_id, pub_id, mobile):
    user = User.query.filter(User.open_id == open_id, User.pub_id == pub_id).first()
    user.mobile = mobile
    db.commit()


def activity_reply(pub, xml_recv):
    """活动（优惠券）的回答列表"""

    ToUserName = xml_recv.find("ToUserName").text
    FromUserName = xml_recv.find("FromUserName").text

    tickets_list = get_tickets_list(pub.id)
    reply_dict = {
        "ToUserName": FromUserName,
        "FromUserName": ToUserName,
        "ArticleCount": len(tickets_list),
        "item": []
    }
    reply_type = "news"
    for ticket in tickets_list:
        item = {
            "Title": str(ticket.title),
            "Description": str(ticket.intro),
            "PicUrl": BASE_URL+ticket.picture_url(),
            "Url": ticket_url(ticket.id, FromUserName)
        }
        reply_dict["item"].append(item)

    if not reply_dict["item"]:  # 如果消息为空，显示没有活动
        reply_dict = {
            "ToUserName": FromUserName,
            "FromUserName": ToUserName,
            "Content": NO_ACTIVITY
        }
        reply_type = "text"

    return reply_dict, reply_type


def get_tickets_list(pub_id):
    """返回优惠券列表"""
    return Ticket.query.filter(Ticket.pub_id == pub_id, Ticket.status == 1,
                               Ticket.stop_time >= datetime.datetime.now()).all()


def valid_user(pub_id, user):
    """验证用户是否为酒吧的会员"""
    return bool(User.query.filter(User.pub_id == pub_id, User.open_id == user).first())


def ticket_url(ticket_id, open_id):
    return "http://www.baidu.com"