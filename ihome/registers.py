from ihome.extensions import bootstrap, db, moment,  csrf, migrate, new_session
from flask import render_template
from ihome.api_1_0 import api
from flask_wtf.csrf import CSRFError
from ihome.utils.utils import RegxConverter
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