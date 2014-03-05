# coding: UTF-8
from flask import request, render_template
from scratch.weixin.webchat import *
import urllib2
from urllib import urlencode
import json
import sys
reload(sys)

def get_token():
    '''获取token'''
    code = request.args.get('code') # 得到用户同意授权的code
    appid = 'wx55970915710ceae8'
    secret = '0a9fcd79087745628d8eb5dd5fb9c418'
    weChat = WebChat('1234',appid, secret, code)
    result = weChat.oauth_user_info() # 得到授权后用户信息json字符串
    nickname = json.loads(result)['nickname']
    if result != 'None':
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>"""+ nickname +"""</h1>
        </body>
        </html>
        """
    else:
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error Internal system error</h1>
        </body>
        </html>
        """
