#  -*- coding: utf-8 -*-

import os

import click
import redis
from flask import Flask,render_template
from flask_wtf.csrf import CSRFError
from ihome.settings import config
from ihome.extensions import bootstrap, db, moment,  csrf, migrate, new_session
from ihome.api_1_0.index import api

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('ihome')
    config_class=config[config_name]
    app.config.from_object(config_class)

    # redis的配置
    REDIS_STORE = redis.StrictRedis(host=config_class.REDIS_IP, port=config_class.REDIS_PORT)

    # 导入注册函数
    from ihome.mylogs import register_logging

    register_extensions(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_blueprints(app)
    register_logging(app)

    return app


def register_blueprints(app):
    """
    注册蓝图
    :param app:
    :return:
    """
    app.register_blueprint(api,url_prefix='/api/v1.0')


def register_extensions(app):
    """
    注册第三方扩展
    :param app:
    :return:
    """
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app,db)
    new_session.init_app(app)


def register_template_context(app):
    """
    添加模板上下文变量，方便在多个模板中共同使用
    :param app:
    :return:
    """

    @app.context_processor
    def make_template_context():

        return dict()


def register_shell_context(app):
    """
    向flask shell中添加变量
    :param app:
    :return:
    """
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db)


def register_errors(app):
    """
    注册异常页面
    :param app:
    :return:
    """
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 400


def register_commands(app):
    """
    自定义flask命令
    :param app:
    :return:
    """

    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """
        初始化数据库
        :param drop:
        :return:
        """
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    # @app.cli.command()
    # @click.option('--username', prompt=True, help='The username used to login.')
    # @click.option('--password', prompt=True, hide_input=True,
    #               confirmation_prompt=True, help='The password used to login.')
    # def init(username, password):
    #     """
    #     注册管理员
    #     :param username:
    #     :param password:
    #     :return:
    #     """
    #
    #     click.echo('Initializing the database...')
    #     db.create_all()
    #
    #     admin = Admin.query.first()
    #     if admin is not None:
    #         click.echo('The administrator already exists, updating...')
    #         admin.username = username
    #         admin.set_password(password)
    #     else:
    #         click.echo('Creating the temporary administrator account...')
    #         admin = Admin(
    #             username=username,
    #             name='Admin',
    #             about='Anything about you.'
    #         )
    #         admin.set_password(password)
    #         db.session.add(admin)
    #
    #     db.session.commit()
    #     click.echo('Done.')
    #
    # @app.cli.command()
    # @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    # @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    # @click.option('--comment', default=500, help='Quantity of comments, default is 500.')
    # def forge(category, post, comment):
    #     """
    #     生成虚拟数据
    #     :param category:
    #     :param post:
    #     :param comment:
    #     :return:
    #     """
    #     from ihome.fakes import fake_admin
    #
    #     db.drop_all()
    #     db.create_all()
    #
    #     click.echo('Generating the administrator...')
    #     fake_admin()
    #
    #     click.echo('Done.')










