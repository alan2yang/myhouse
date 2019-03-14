import os
import redis

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
# WIN = sys.platform.startswith('win')
# if WIN:
#     prefix = 'sqlite:///'
# else:
#     prefix = 'sqlite:////'


class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'fdjlkjei3458fjd84dk9843dsf943')

    # 主数据库的配置
    DATABASE_NAME=os.getenv('DATABASE_NAME')
    DATABASE_PASSWORD=os.getenv('DATABASE_PASSWORD')
    DATABASE_IP = os.getenv('DATABASE_IP')
    DATABASE_PORT = os.getenv('DATABASE_PORT')

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis的配置--用于缓存和session
    REDIS_IP=os.getenv('REDIS_IP')
    REDIS_PORT=os.getenv('REDIS_PORT')

    # flask-session的配置
    SESSION_TYPE="redis"
    SESSION_REDIS=redis.StrictRedis(host=REDIS_IP,port=REDIS_PORT)
    SESSION_USE_SIGNER=True  # 对cookie中的session_id进行混淆处理
    PERMANENT_SESSION_LIFETIME= 86400

    # 图片验证码的redis有效期, 单位：秒
    IMAGE_CODE_REDIS_EXPIRES = 300

    # 短信验证码的redis有效期, 单位：秒
    SMS_CODE_REDIS_EXPIRES = 300

    # 发送短信验证码的间隔, 单位：秒
    SEND_SMS_CODE_INTERVAL = 60

    # 登录错误尝试次数
    LOGIN_ERROR_MAX_TIMES = 4

    # 登录错误限制的时间, 单位：秒
    LOGIN_ERROR_FORBID_TIME = 600

    # 七牛的域名
    QINIU_URL_DOMAIN = "http://pnxo61idw.bkt.clouddn.com/"

    # 城区信息的缓存时间, 单位：秒
    AREA_INFO_REDIS_CACHE_EXPIRES = 7200

    # 首页展示最多的房屋数量
    HOME_PAGE_MAX_HOUSES = 5

    # 首页房屋数据的Redis缓存时间，单位：秒
    HOME_PAGE_DATA_REDIS_EXPIRES = 7200

    # 房屋详情页展示的评论最大数
    HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

    # 房屋详情页面数据Redis缓存时间，单位：秒
    HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

    # 房屋列表页面每页数据容量
    HOUSE_LIST_PAGE_CAPACITY = 2

    # 房屋列表页面页数缓存时间，单位秒
    HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

    # 支付宝的网关地址（支付地址域名）
    ALIPAY_URL_PREFIX = "https://openapi.alipaydev.com/gateway.do?"

    # MAIL_SERVER = os.getenv('MAIL_SERVER')
    # MAIL_PORT = 465
    # MAIL_USE_SSL = True
    # MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    # MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    # MAIL_DEFAULT_SENDER = ('xxxx', MAIL_USERNAME)
    #


class DevelopmentConfig(BaseConfig):
    # SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data-dev.db')
    SQLALCHEMY_DATABASE_URI="mysql://{}:{}@{}:{}/ihome".format(BaseConfig.DATABASE_NAME,BaseConfig.DATABASE_PASSWORD,BaseConfig.DATABASE_IP,BaseConfig.DATABASE_PORT)


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory database


class ProductionConfig(BaseConfig):
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))
    SQLALCHEMY_DATABASE_URI = "mysql://{}:{}@{}:{}/ihome".format(BaseConfig.DATABASE_NAME, BaseConfig.DATABASE_PASSWORD,
                                                                 BaseConfig.DATABASE_IP, BaseConfig.DATABASE_PORT)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

