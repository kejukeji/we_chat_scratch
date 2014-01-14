# coding: utf-8

# flask 配置参数
DEBUG = True  # 是否启动调试功能
SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmNui]LWX/,?RT^&556gh/ghj~hj/kh'  # session相关的密匙

# models 模块需要的配置参数
SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/wei_xin_pub?charset=utf8'  # 连接的数据库
SQLALCHEMY_ECHO = True  # 输出语句

## 图片管理
PICTURE_ALLOWED_EXTENSION = ('png', 'jpg', 'jpeg')
# 酒吧图片
PUB_PICTURE_BASE_PATH = "/Users/X/Dropbox/Code/weixin_pub/pub"
PUB_PICTURE_REL_PATH = "/static/system/pub_picture"
# 优惠券图片
TICKET_PICTURE_BASE_PATH = "/Users/X/Dropbox/Code/weixin_pub/pub"
TICKET_PICTURE_REL_PATH = "/static/system/ticket_picture"

# 基本的url
BASE_URL = "http://weixin.kejukeji.com"