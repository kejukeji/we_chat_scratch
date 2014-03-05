# coding: utf-8

import hashlib
import urllib2
import json
from .message import msg_format


class WebChat(object):
    """微信类"""

    def __init__(self, token, appid=None, secret=None, code=None):
        self.token = token
        self.appid = appid
        self.secret = secret
        self.code = code

    def update(self, appid, secret):
        self.appid = appid
        self.secret = secret

    def validate(self, timestamp, nonce, signature):
        """验证微信接入的参数，成功返回True 否则 False"""
        hash_string = ''.join(sorted([self.token, timestamp, nonce]))
        return signature == hashlib.sha1(hash_string).hexdigest()

    def create_menu(self, menu_string):
        menu_url = self.create_menu_url()
        urllib2.urlopen(menu_url, menu_string.encode('utf-8'))

    def oauth_user_info(self):
        '''得到授权后的json字符串'''
        oauth_user_info_url = self.get_oauth_user_info_url()
        result = urllib2.urlopen(oauth_user_info_url)
        return result.read()

    def get_access_token(self):
        """得到access_token"""
        access_token_url = self.token_url()
        f = urllib2.urlopen(access_token_url)
        json_string = f.read()
        return json.loads(json_string)['access_token']

    def token_url(self):
        """返回获取access_token的链接"""
        return "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" \
               % (self.appid, self.secret)

    def oauth_token_url(self):
        '''返回得到授权的access_token链接'''
        return "https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code" \
                % (self.appid, self.secret, self.code)

    def get_oauth_user_info_url(self):
        '''根据得到授权access_token得到获取用户信息url'''
        access_token, oauth_openid = self.get_oauth_access_token()
        return "https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=zh_CN" \
               % (access_token, oauth_openid)

    def get_oauth_access_token(self):
        '''获得授权的access_token'''
        access_token_url = self.oauth_token_url()
        result = urllib2.urlopen(access_token_url)
        json_string = result.read()
        return json.loads(json_string)['access_token'], json.loads(json_string)['openid']

    def create_menu_url(self):
        """返回创建菜单的url"""
        access_token = self.get_access_token()
        return "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=" + str(access_token)

    @staticmethod
    def reply(msg_type, msg_dict):
        return msg_format(msg_type, msg_dict)