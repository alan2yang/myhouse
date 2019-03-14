from datetime import datetime

from flask import current_app, jsonify,json,request,g
from flask import session
from ihome.libs.utils.image_storage import storage
from ihome.libs.utils.response_code import RET

from ihome import REDIS_STORE
from ihome.api_1_0 import api
from ihome.libs.utils.utils import login_required
from ihome.models.models import Area, House, Facility, HouseImage, User, Order
from ihome.registers import db


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
    接收房屋信息
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


@api.route("/user/houses")
@login_required
def get_publish_houses():
    """
    获取用户已经发布的房源信息
    :return:
    """
    try:
        houses=User.query.get(g.user_id).houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    houses_li=list()
    for house in houses:
        houses_li.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_li})


@api.route("/houses/index")
def get_houses_index():
    """
    获取主页的房屋信息
    :return:
    """

    # 使用缓存
    try:
        ret=REDIS_STORE.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret=None

    # 如果缓存中有，则直接返回
    if ret:
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}

    # 缓存中没有，则从数据库中取
    try:
        # 查询数据库，返回房屋订单数目最多的5条数据
        houses = House.query.order_by(House.order_count.desc()).limit(current_app.config['HOME_PAGE_MAX_HOUSES'])
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not houses:
        return jsonify(errno=RET.NODATA, errmsg="查询无数据")

    houses_list = []
    for house in houses:
        # 如果房屋未设置主图片，则跳过
        if not house.index_image_url:
            continue
        houses_list.append(house.to_basic_dict())

    # 将数据转换为json，并保存到redis缓存
    json_houses = json.dumps(houses_list)  # "[{},{},{}]"
    try:
        REDIS_STORE.setex("home_page_data", current_app.config["HOME_PAGE_DATA_REDIS_EXPIRES"], json_houses)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>")
def get_house_detail(house_id):
    """
    获取房屋详细信息
    前端要确认当前用户是否为房东
    :return:
    """
    # 获取当前用户id，如果没有登录则返回-1
    user_id=session.get("user_id","-1")

    # 异常情况
    if not user_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数确实")

    # 先从redis缓存中获取信息
    try:
        ret = REDIS_STORE.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典，在模型类中实现:因为to_full_dict方法涉及数据库操作
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    house_json=json.dumps(house_data)

    try:
        REDIS_STORE.setex("house_info_%s" % house_id,current_app.config["HOUSE_DETAIL_REDIS_EXPIRE_SECOND"],house_json)
    except Exception as e:
        current_app.logger.error(e)

    # 返回数据
    # print('{"errno":"0","errmsg":"OK","data":{"user_id":%s,"house":%s}}' % (user_id,house_json))
    return '{"errno":"0","errmsg":"OK","data":{"user_id":%s,"house":%s}}' % (user_id,house_json),200,{"Content-Type":"application/json"}


# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """
    房屋查询功能

    :return:
    """

    start_date=request.args.get("sd","")  # 开始时间
    end_date=request.args.get("ed","")  # 截止时间
    area_id=request.args.get("aid","")  # 区域id
    sort_key=request.args.get("sk","new")  # 排序方式
    page=request.args.get("p",1)  # 当前页

    # 校验时间
    try:
        if start_date:
            start_date=datetime.strptime(start_date,"%Y-%m-%d")
        if end_date:
            end_date=datetime.strptime(end_date,"%Y-%m-%d")
        if start_date and end_date:
            assert start_date<=end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 校验区域id
    if area_id:
        try:
            area=Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    # 检验page
    try:
        page=int(page)
    except Exception as e:
        current_app.logger.error(e)
        page=1

    # 从缓存中读取数据
    try:
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        resp_json=REDIS_STORE.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json,200,{"Content-Type":"application/json"}

    # 多个过滤条件用列表保存
    filter_li=list()

    conflict_orders=None
    # 获取不符合要求的订单
    try:
        if start_date and end_date:
            conflict_orders=Order.query.filter(Order.begin_date<end_date,Order.end_date>start_date).all()
        elif start_date:
            conflict_orders=Order.query.filter(Order.begin_date<start_date,Order.end_date>start_date).all()
        elif end_date:
            conflict_orders=Order.query.filter(Order.begin_date < end_date, Order.end_date > end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders:
        conflict_house_ids=[order.house_id for order in conflict_orders]
        # 如果冲突房屋id存在，则添加过滤条件
        if conflict_house_ids:
            filter_li.append(House.id.notin_(conflict_house_ids))

    # 区域过滤
    if area_id:
        filter_li.append(House.area_id==area_id)

    # 排序规则：这里只做过滤，还没执行查询功能
    if sort_key=="booking":
        house_query=House.query.filter(*filter_li).order_by(House.order_count.desc())
    elif sort_key=="price-inc":
        house_query =House.query.filter(*filter_li).order_by(House.price.asc())
    elif sort_key=="price-des":
        house_query =House.query.filter(*filter_li).order_by(House.price.desc())
    else:
        house_query =House.query.filter(*filter_li).order_by(House.create_time)

    # 分页,返回查询结果
    try:
        pagination=house_query.paginate(page=page,per_page=current_app.config["HOUSE_LIST_PAGE_CAPACITY"],error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    total_page=pagination.pages

    houses_li=list()
    for house in pagination.items:
        houses_li.append(house.to_basic_dict())

    # 除了状态码，还要返回总页数、当前页数、当前的数据
    # resp_dict={"errno":"0","errmsg":"OK","data":{"total_page":total_page,"current_page":page,"houses":houses_li}}
    resp_dict=dict(errno=RET.OK,errmsg="OK",data={"total_page":total_page,"current_page":page,"houses":houses_li})
    resp_json=json.dumps(resp_dict)

    # 尝试添加缓存

    # 缓存的保存格式
    # 根据过滤条件来保存　start_date,end_date,area_id,sort_key
    # 每组过滤条件下又有多个分页，所以可以考虑将每个分页分开保存
    # 考虑使用hash格式保存

    if page<=total_page:  # 如果当前页数超过了总页数，则该数据无意义，不缓存
        try:
            redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            # 问题：如果数据存入成功，但设置过期时间失败，怎么办？
            # REDIS_STORE.hset(redis_key,page,resp_json)
            # REDIS_STORE.expire(redis_key,current_app.config["HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES"])

            # 考虑使用管道
            # 创建redis管道对象，可以一次执行多个语句
            pipeline=REDIS_STORE.pipeline()
            # 开启
            pipeline.multi()
            REDIS_STORE.hset(redis_key,page,resp_json)
            REDIS_STORE.expire(redis_key,current_app.config["HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES"])

            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)

    return resp_json,200,{"Content-Type":"application/json"}


