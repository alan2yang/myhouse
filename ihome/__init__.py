#  -*- coding: utf-8 -*-

import os
import redis
from flask import Flask
from ihome.settings import config


basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

REDIS_STORE=None


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('ihome')
    config_class=config[config_name]
    app.config.from_object(config_class)

    # redis的配置
    global REDIS_STORE
    REDIS_STORE = redis.StrictRedis(host=config_class.REDIS_IP, port=config_class.REDIS_PORT,decode_responses=True)

    # 导入注册函数
    from ihome.mylogs import register_logging
    from ihome.registers import register_template_context,register_shell_context,register_blueprints,register_errors,register_extensions
    from ihome.commands import register_commands

    register_extensions(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_blueprints(app)
    register_logging(app)

    return app
















