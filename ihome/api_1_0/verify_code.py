import random

from flask import request

from . import api
from ihome.utils.captcha.captcha import captcha

from flask import current_app,make_response,jsonify
from ihome.utils.response_code import RET
from ihome.models import User
from ihome.libs.ytx.sms import CCP
from ihome import REDIS_STORE


# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    : params image_code_id:  图片验证码编号
    :return:  正常:验证码图片  异常：返回json
    """
    # 生成验证码图片
    # 名字，真实文本， 图片数据
    name, text, image_data = captcha.generate_captcha()

    try:
        REDIS_STORE.setex("image_code_%s" % image_code_id, current_app.config['IMAGE_CODE_REDIS_EXPIRES'], text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,  errmsg="保存图片验证码失败")

    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """
    获取短信验证码
    :param mobile: 手机号
    :return:
    """
    # 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    # 校验参数
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 从redis中取出真实的图片验证码
    try:
        real_image_code = REDIS_STORE.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 图片验证码没有或者过期
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
    try:
        REDIS_STORE.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值进行对比
    if real_image_code.decode().lower() != image_code.lower():
        # 表示用户填写错误
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 判断对于这个手机号的操作，在60秒内有没有操作记录，如果有，则认为用户操作频繁，不接受处理
    try:
        send_flag = REDIS_STORE.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒内之前有过发送的记录
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号已存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 如果手机号不存在数据库中，则生成短信验证码
    sms_code = "{:0>6d}".format(random.randint(0, 999999))

    # 保存真实的短信验证码
    try:
        # 将验证码保存到redis中
        REDIS_STORE.setex("sms_code_%s" % mobile, current_app.config['SMS_CODE_REDIS_EXPIRES'], sms_code)
        # 保存发送给这个手机号的记录，防止用户在60s内再次出发发送短信的操作
        REDIS_STORE.setex("send_sms_code_%s" % mobile, current_app.config['SEND_SMS_CODE_INTERVAL'], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")

    # 发送短信
    # todo 异步执行
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, int(current_app.config['SMS_CODE_REDIS_EXPIRES']/60)], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="发送异常")

    # 返回值
    if result == 0:
        # 发送成功
        return jsonify(errno=RET.OK, errmsg="短信发送成功")
    else:
        return jsonify(errno=RET.THIRDERR, errmsg="短信发送失败")