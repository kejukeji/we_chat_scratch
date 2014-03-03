# coding: UTF-8
from flask import request
import urllib2
from urllib import urlencode
import json
import sys
reload(sys)

def get_token():
    '''获取token'''
    code = request.args.get('code') # 得到用户同意授权的code
    get_access_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=wxd66b61798e08ff5e&secret=d04dd7c764cc9b348d390eb81340a778&code='+ code +'&grant_type=authorization_code'
    access_token = urllib2.urlopen(get_access_token_url) # 访问此url得到token
    json_token = access_token.read() # 读取token

    token = json.loads(json_token)['access_token'] # 从读取到的json中通过key得到access_token值
    open_id = json.loads(json_token)['openid'] # 获得用户的openId

    get_user_info_url = 'https://api.weixin.qq.com/sns/userinfo?access_token='+ token +'openid='+ open_id +'&lang=zh_CN'

    user_info_result = urllib2.urlopen(get_user_info_url) # 请求此url的结果
    json_user_info = user_info_result.read() # 得到json结果

    nickname = json.loads(json_user_info)['nickname'] # 得到用户的昵称
    return """
    <html>
    <head><title>用户昵称</title></head>
    <body>
    """+nickname+"""
    </body>
    </html>
    """
