
from flask import abort
from flask import current_app
from flask import flash
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ihome.extensions import db

from . import api


@api.route('/')
def index():
    """
    首页
    :return:
    """

    return render_template('index/index.html')

