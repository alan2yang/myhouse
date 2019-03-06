from flask import Blueprint

api = Blueprint('api', __name__)

# 注意循环导入问题
from . import index,verify_code,houses,passport,profile,orders
