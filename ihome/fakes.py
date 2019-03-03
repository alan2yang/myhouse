# 虚拟数据生成功能
import random

from faker import Faker
from sqlalchemy.exc import IntegrityError

from ihome import db
from ihome.models import Admin

fake = Faker()


def fake_admin():
    admin = Admin(
        username='yf',
        blog_title="YF'sBlog",
        blog_sub_title="I'm the real thing.",
        name='Mima Kirigoe',
        about="Welcome to YF's Blog!"
    )
    admin.set_password('helloflask')
    db.session.add(admin)
    db.session.commit()




