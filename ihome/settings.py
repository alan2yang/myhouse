import os
import sys

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

