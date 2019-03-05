from flask import current_app, jsonify,json,request,g

from ihome.api_1_0 import api
from ihome.extensions import db
from ihome.models import Area, House, Facility, HouseImage
from ihome.utils.response_code import RET
from ihome import REDIS_STORE
from ihome.utils.utils import login_required
from ihome.utils.image_storage import storage


@api.route("/areas")
def get_area_info():
    """获取城区信息"""

    # 尝试从redis中读取数据
    try:
        resp_json = REDIS_STORE.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis有缓存数据
            return resp_json, 200, {"Content-Type": "application/json"}

    # 如果redis中没有缓存数据，查询数据库，读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    area_dict_li = []
    # 将对象转换为字典
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据转换为json字符串，保存在redis中
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    try:
        REDIS_STORE.setex("area_info", current_app.config["AREA_INFO_REDIS_CACHE_EXPIRES"], resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info",methods=["POST"])
@login_required
def get_house_info():
    """
    获取房屋信息
    前端发送过来的json数据
    {
    "title":"",
    "price":"",
    "area_id":"1",
    "address":"",
    "room_count":"",
    "acreage":"",
    "unit":"",
    "capacity":"",
    "beds":"",
    "deposit":"",
    "min_days":"",
    "max_days":"",
    "facility":["7","8"]
    }
    :return:
    """

    house_data=request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断金额是否正确:涉及money很重要，数据保存到数据库以分作为单位
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if not area:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 添加数据
    house=House(
        user_id=g.user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 放到后面与房屋设施数据一起提交
    # try:
    #     db.session.add(house)
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify()

    # 处理房屋设施信息
    facility_ids=house_data.get("facility")

    # 如果有设施信息
    if facility_ids:
        try:
            facilities=Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilities:
            house.facilities=facilities

    # 没有设施信息也无妨
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 保存数据成功，返回保存的房屋id
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image",methods=["POST"])
@login_required
def save_house_image():
    """
    接收房屋图片
    :return:
    """

    image_file=request.files.get("house_image")
    house_id=request.form.get("house_id")

    if not all([image_file,house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        house=House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    image_data=image_file.read()

    try:
        file_name=storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify()

    house_image=HouseImage(house_id=house_id,url=file_name)
    db.session.add(house_image)

    # 房屋首页图片设置:如果没有设置，则设置第一张图片
    if not house.index_image_url:
        house.index_image_url=file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    image_url=current_app.config["QINIU_URL_DOMAIN"]+file_name

    return jsonify(errno=RET.OK,errmsg="OK",data={"image_url":image_url})