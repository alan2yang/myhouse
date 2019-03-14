# 扩展功能
from functools import wraps

from flask import session, jsonify
from werkzeug.routing import BaseConverter

from ihome.libs.utils.response_code import RET

try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

from flask import request, redirect, url_for,g


def is_safe_url(target):
    """
    url安全验证
    :param target:
    :return:
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default='index.index', **kwargs):
    """
    重定向到上一个请求
    :param default:
    :param kwargs: 
    :return:
    """
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


# 路由转换器
class RegxConverter(BaseConverter):
    def __init__(self,map,*args):
        super(RegxConverter,self).__init__(map)
        self.regex=args[0]


# 登录验证装饰器
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args,**kwargs):
        user_id=session.get("user_id")
        if user_id is not None:
            # 登录成功
            g.user_id=user_id  # 将用户id保存在g变量中，方便在视图函数中直接使用，不用再查询redis
            return view_func(*args,**kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR,errmsg="请先登录")

    return wrapper