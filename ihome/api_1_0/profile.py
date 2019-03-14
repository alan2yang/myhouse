from flask import g,current_app,jsonify,request
from flask import session
from ihome.libs.utils.image_storage import storage
from ihome.libs.utils.response_code import RET

from ihome.libs.utils.utils import login_required
from ihome.models.models import User
from ihome.registers import db
from . import api


@api.route("/users/avatar",methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :return:
    """
    user_id =g.user_id

    image_file=request.files.get("avatar")

    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = image_file.read()

    # 调用七牛上传图片, 返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    # 最好返回保存的文件信息
    avatar_url=current_app.config["QINIU_URL_DOMAIN"]+file_name

    return jsonify(errno=RET.OK,errmsg="保存成功",data={"avatar_url":avatar_url})


@api.route("/user")
@login_required
def get_user_profile():
    """
    用户名获取
    :return:
    """
    user_id = g.user_id
    try:
        user=User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK,errmsg="OK", data = user.to_dict())


@api.route("/users/name",methods=["PUT"])
@login_required
def change_user_name():
    """
    用户名修改
    :return:
    """

    req_json=request.get_json()
    if not req_json:
        return jsonify(errno=RET.PARAMERR,errmsg="名字不能为空")

    new_name=req_json.get("name")

    # 判断用户名是否重复，如果重复则出错，可以细化错误类型
    try:
        User.query.filter_by(id=g.user_id).update({"name":new_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="设置用户名出错")

    # 因为session中保存的有name值，所以也要更新一下
    session["name"]=new_name

    # 更新后最好返回新的信息
    return jsonify(errno=RET.OK,errmsg="OK",data={"name":new_name})


# 实名认证实现
@api.route("/users/auth")
@login_required
def get_user_auth():
    """
    查询实名认证信息
    :return:
    """
    try:
        user=User.query.get(g.user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    return jsonify(errno=RET.OK,errmsg="OK",data=user.auth_to_dict())


# 返回实名认证数据
@api.route("/users/auth",methods=["POST"])
@login_required
def set_user_auth():
    """
    设置实名认证信息
    :return:
    """
    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 保存用户的姓名与身份证号
    try:
        User.query.filter_by(id=g.user_id, real_name=None, id_card=None) \
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

    return jsonify(errno=RET.OK, errmsg="OK")