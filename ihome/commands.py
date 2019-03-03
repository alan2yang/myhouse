import click
from ihome.extensions import db


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