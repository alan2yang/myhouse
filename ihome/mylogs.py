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
