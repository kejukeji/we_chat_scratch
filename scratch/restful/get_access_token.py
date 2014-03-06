# coding: UTF-8
from flask import request, render_template
from scratch.weixin.webchat import *
import urllib2
from urllib import urlencode
import cookielib
import urllib
import hashlib
import time
import json
import sys
reload(sys)

def get_token():
    '''获取token'''
    code = request.args.get('code') # 得到用户同意授权的code
    appid = 'wxd66b61798e08ff5e'
    secret = 'd04dd7c764cc9b348d390eb81340a778'
    weChat = WebChat('7072',appid, secret, code)
    result = weChat.oauth_user_info() # 得到授权后用户信息json字符串
    nickname = json.loads(result)['nickname']
    header_image_url = json.loads(result)['headimgurl']
    if result != 'None':
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>%s</h1>
            <img src='%s'/>
        </body>
        </html>
        """ % (nickname, header_image_url)
    else:
        return """
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error Internal system error</h1>
        </body>
        </html>
        """




class Client(object):
    def __init__(self, email=None, password=None):
        """
        登录公共平台服务器，如果失败将报客户端登录异常错误
        :param email:
        :param password:
        :raise:
        """
        if not email or not password:
            raise ValueError
        self.setOpener()
        url_login = "http://mp.weixin.qq.com/cgi-bin/login?lang=en_US"
        #m = hashlib.md5(password[0:16])
        #m.digest()
        #password = m.hexdigest()
        body = (('username', email), ('pwd', password), ('imgcode', ''), ('f', 'json'))
        try:
            msg = json.loads(self.opener.open(url_login, urllib.urlencode(body), timeout=5).read())
        except urllib2.URLError:
            raise ClientLoginException
        if msg['ErrCode'] not in (0, 65202):
            raise ClientLoginException
        self.token = msg['ErrMsg'].split('=')[-1]


    def sendTextMsg(self, sendTo, content):
        """
        给用户发送文字内容，成功返回True，使用时注意两次发送间隔，不能少于2s
        :param sendTo:
        :param content:
        :return:
        """
        if type(sendTo) == type([]):
            for _sendTo in sendTo:
                self.sendTextMsg(_sendTo, content)
                time.sleep(2)
            return

        self.opener.addheaders = [('Referer', 'http://mp.weixin.qq.com/cgi-bin/singlemsgpage?fromfakeid={0}'
                                              '&msgid=&source=&count=20&t=wxm-singlechat&lang=zh_CN'.format(sendTo))]
        send_url = "http://mp.weixin.qq.com/cgi-bin/singlesend?t=ajax-response&lang=zh_CN"
        body = (
            ('type', 1), ('content', content), ('error', 'false'), ('token', self.token), ('tofakeid', sendTo),
            ('ajax', 1))
        try:
            msg = json.loads(self.opener.open(send_url, urllib.urlencode(body), timeout=5).read())['msg']
        except urllib2.URLError:
            return self.sendTextMsg(sendTo, content)
        return msg == 'ok'

    def setOpener(self):
        """
        设置请求头部信息模拟浏览器
        """
        cookie = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        self.opener.addheaders = [('Accept', 'application/json, text/javascript, */*; q=0.01')]
        self.opener.addheaders = [('Accept-Language', 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4')]
        self.opener.addheaders = [('Accept-Encoding', 'gzip,deflate,sdch')]
        self.opener.addheaders = [('Cache-Control', 'no-cache, must-revalidate')]
        self.opener.addheaders = [('Connection', 'keep-alive')]
        self.opener.addheaders = [('Host', 'mp.weixin.qq.com')]
        self.opener.addheaders = [('Origin', 'mp.weixin.qq.com')]
        self.opener.addheaders = [('Referer', 'https://mp.weixin.qq.com/')]
        self.opener.addheaders = [('X-Requested-With', 'XMLHttpRequest')]
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 '
                                                 '(KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36')]

class ClientLoginException(Exception):
    pass


if __name__ == '__main__':
    email = 'hr@kejukeji.com'
    password = 'da01314563c45f78a19222ccd82243a5'
    client = Client(email, password)
    content = '测试推送消息'
    client.sendTextMsg(['2105013481'],content)