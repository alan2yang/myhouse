from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_moment import Moment
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()
csrf=CSRFProtect()
migrate=Migrate()
new_session=Session()


from ihome.api_1_0 import api
from ihome.libs.utils.utils import RegxConverter
from ihome.static_blueprint import html


def register_blueprints(app):
    """
    注册蓝图
    :param app:
    :return:
    """
    # 添加自定义转换器
    app.url_map.converters['re']=RegxConverter

    app.register_blueprint(html)
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
    # @app.errorhandler(400)
    # def bad_request(e):
    #     return render_template('errors/400.html'), 400
    #
    # @app.errorhandler(404)
    # def page_not_found(e):
    #     return render_template('errors/404.html'), 404
    #
    # @app.errorhandler(500)
    # def internal_server_error(e):
    #     return render_template('errors/500.html'), 500
    #
    # @app.errorhandler(CSRFError)
    # def handle_csrf_error(e):
    #     return render_template('errors/400.html', description=e.description), 400


import logging
from logging.handlers import RotatingFileHandler


def register_logging(app):
    # todo　通过邮件发送关键日志
    """
    注册日志功能
    :param app:
    :return:
    """
    # 日志记录器
    app.logger.setLevel(logging.INFO)  # 日志记录器等级

    formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 日志处理器
    file_handler=RotatingFileHandler('logs/index.log',maxBytes=10*1024*1024,backupCount=10)

    file_handler.setFormatter(formatter)  # 日志处理器输出的日志格式
    file_handler.setLevel(logging.INFO)  # 日志处理器接收的日志等级

    if not app.debug:  # 不是调试模式，为日志记录器添加处理器
        app.logger.addHandler(file_handler)


import click


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