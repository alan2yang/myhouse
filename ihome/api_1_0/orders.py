from flask import current_app
from flask import g, jsonify
from flask import request

from ihome.extensions import db
from ihome.models import Order, House
from ihome.utils.response_code import RET
from . import api
from ihome.utils.utils import login_required
from datetime import datetime
from ihome import REDIS_STORE


@api.route("/orders",methods=["POST"])
@login_required
def make_order():
    """
    下订单
    :return:
    """
    user_id = g.user_id

    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")

    if not all((house_id, start_date_str, end_date_str)):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 日期格式检查
    try:
        # 将请求的时间参数字符串转换为datetime类型
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date
        # 计算预订的天数
        days = (end_date - start_date).days  # 日期格式：datetime.timedelta
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 预订的房屋不能是用户自己的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="不能预订自己的房屋")

    # 确保用户预订的时间内，房屋没有被别人下单
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="检查出错，请稍候重试")
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已被预订")

    amount = days * house.price

    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


@api.route("/user/orders")
@login_required
def get_order():
    """
    获取用户的订单，两种情况：获取当前用户下的单；获取当前用户租出去的单
    :return:
    """
    user_id=g.user_id

    # 获取用户角色：买家？卖家？
    role=request.args.get("role","")
    print('*'*50,role,'*'*50)

    try:
        if role=="landlord":  # 卖家
            houses=House.query.filter_by(user_id=user_id).all()
            houses_li=[house.id for house in houses]

            orders=Order.query.filter(Order.house_id.in_(houses_li)).order_by(Order.create_time.desc()).all()
        else:
            orders=Order.query.filter_by(user_id=user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")

    orders_dict_list = list()
    for order in orders:
        orders_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK,errmsg="OK",data={"orders":orders_dict_list})


@api.route("/orders/<int:order_id>/status",methods=["PUT"])  # 更新订单使用PUT方法
@login_required
def accept_reject_order(order_id):
    """
    接单／拒单
    :return:
    """
    # 接单要修改订单状态
    # 拒单要写拒单原因
    user_id = g.user_id

    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # action参数表明客户端请求的是接单还是拒单的行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 确保该订单的房东是当前用户
    try:
        order=Order.query.filter(Order.id==order_id,Order.status=="WAIT_ACCEPT").first()
        house=order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    if not order or user_id != house.user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    # 接受订单
    if action=="accept":
        order.status="WAIT_PAYMENT"
    elif action=="reject":
        reject_reson=req_data.get("reason")
        if not reject_reson:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status="REJECTED"
        order.comment=reject_reson

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment",methods=["POST"])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息
    :return:
    """
    user_id = g.user_id
    req_data = request.get_json()
    comment = req_data.get("comment")  # 评价信息

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态才可以
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1
        house.order_count += 1

        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
    try:
        REDIS_STORE.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")
