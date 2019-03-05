from ihome.utils.utils import login_required
from . import api
from flask import request,jsonify,current_app,session
from ihome.utils.response_code import RET
import re
from ihome.models import User
from ihome import REDIS_STORE
from ihome.extensions import db
from sqlalchemy.exc import IntegrityError


@api.route("/users", methods=["POST"])
def register():
    """注册
    请求的参数： 手机号、短信验证码、密码、确认密码
    参数格式：json
    """
    # 获取请求的json数据，返回字典
    req_dict = request.get_json()

    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 表示格式不对
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = REDIS_STORE.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取真实短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        REDIS_STORE.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    if real_sms_code.decode() != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 保存用户的注册数据到数据库中
    user = User(name=mobile, mobile=mobile)

    user.password = password  # 设置属性

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        # 表示手机号出现了重复值，即手机号已注册过(手机号字段为唯一值，一旦重复则无法插入，并报错)
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    # 保存登录状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """用户登录
    参数： 手机号、密码， json
    """
    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 校验参数
    # 参数完整的校验
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 手机号的格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断错误次数是否超过限制，如果超过限制，则返回
    # redis记录： "access_nums_请求的ip": "次数"
    user_ip = request.remote_addr  # 用户的ip地址
    try:
        access_nums = REDIS_STORE.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= current_app.config['LOGIN_ERROR_MAX_TIMES']:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

    # 从数据库中根据手机号查询用户的数据对象
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 用数据库的密码与用户填写的密码进行对比验证－－－－保证前端无法获得是哪个错误
    if user is None or not user.check_password(password):
        # 如果验证失败，记录错误次数，返回信息
        try:
            # redis的incr可以对字符串类型的数字数据进行加一操作，如果数据一开始不存在，则会初始化为1
            REDIS_STORE.incr("access_num_%s" % user_ip)
            # 设置解禁时间
            REDIS_STORE.expire("access_num_%s" % user_ip, current_app.config['LOGIN_ERROR_FORBID_TIME'])
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 如果验证相同成功，保存登录状态， 在session中
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session",methods=['GET'])
def get_session():
    """
    首页用户登录状态
    :return:
    """
    name=session.get("name")

    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session",methods=['DELETE'])
@login_required
def logout():
    """
    登出
    :return:
    """
    csrf_token = session.get("csrf_token")  #　保证csrf正常
    session.clear()
    session["csrf_token"] = csrf_token
    return jsonify(errno=RET.OK, errmsg="OK")