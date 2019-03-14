from flask import request

from ihome.api_1_0 import api
from ihome.libs.utils.response_code import RET
from ihome.libs.utils.utils import login_required
from alipay import AliPay
from flask import g,current_app,jsonify

from ihome.models.models import Order
from ihome.registers import db


@api.route("/orders/<int:order_id>/payment",methods=["POST"])
@login_required
def order_pay(order_id):
    """
    发起支付宝支付
    :param order_id:
    :return:
    """

    user_id=g.user_id
    try:
        order=Order.query.filter(Order.id==order_id,Order.user_id==user_id,Order.status=='WAIT_PAYMENT').first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg="订单数据有误")

    with open("ihome/api_1_0/key/app_private_key.pem") as f:
        app_private_key_string=f.read()
    with open("ihome/api_1_0/key/alipay_public_key.pem") as f:
        alipay_public_key_string =f.read()

    # 请求定义
    alipay = AliPay(
        appid="2016092500596325",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA2
        debug = True  # 默认False
    )

    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string进行支付
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order_id,  # 订单号
        total_amount=str(order.amount/100),  # 金额
        subject="租房款项{}".format(order_id),  # 标题
        return_url="http://127.0.0.1:5000/paycomplete.html",  # 支付完成后用户跳转的页面:添加一个过渡页面
        notify_url=None  # 可选, 不填则使用默认notify url
    )

    pay_url=current_app.config["ALIPAY_URL_PREFIX"] + order_string

    return jsonify(errno=RET.OK,errmsg="OK",data={'pay_url':pay_url})

# return_url:
# http://127.0.0.1:5000/paycomplete.html?
# charset=utf-8
# &out_trade_no=4
# &method=alipay.trade.wap.pay.return
# &total_amount=384.00
# &sign=uMeBJaXmK8jfcOYw1TeDqbal7OQxJkJWqgFK6eeyxXKMOXOnySpXNUTSChI37GHUNFPG8FNW6dDEIkq%2FkbyV2NkzLfOZ%2BZOUS5%2BqEPZO8wjoiOEstekacP8UiBwlrsOKo9kXaudwaCTsQCir79mc52ADz287GRdwtHPfrZi0bH1IqTsxb9VjcTLUS9k9ZQWVl2YyD43AhqcGaQiwfcWPw%2BaTxXdLhzZQlckKaMjT8ioUpHUrJYcXXM06BbSNxiTwv8Wkny%2Bu1cWgsoPl1iTgR%2FtozIpj7QalbvSO3vHNNxMG4sND5Mb3VeOVKPsX22yeystyHWOQokxlSSQ8Ji1nfQ%3D%3D
# &trade_no=2019031422001414130500728495
# &auth_app_id=2016092500596325
# &version=1.0
# &app_id=2016092500596325
# &sign_type=RSA2
# &seller_id=2088102177267672
# &timestamp=2019-03-14+21%3A19%3A31


@api.route("/order/payment",methods=["PUT"])
@login_required
def update_order():
    """
    更新订单信息
    :return:
    """
    data=request.form.to_dict()  # 将表单数据转换为字典
    signature=data.pop("sign")  # 获取签名

    # 数据验证
    with open("ihome/api_1_0/key/app_private_key.pem") as f:
        app_private_key_string=f.read()
    with open("ihome/api_1_0/key/alipay_public_key.pem") as f:
        alipay_public_key_string =f.read()

    alipay = AliPay(
        appid="2016092500596325",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA2
        debug=True  # 默认False
    )

    # 对支付宝发送过来的数据进行验证
    result=alipay.verify(data,signature)

    if result:
        order_id=data.get("out_trade_no")   # 获取我们的订单号
        trade_no=data.get("trade_no")  # 支付宝的交易订单号
        try:
            Order.query.filter_by(id=order_id).update({"status":"WAIT_COMMENT","trade_no":trade_no})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")

