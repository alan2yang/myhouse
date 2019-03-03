from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_session import Session

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()
csrf=CSRFProtect()
migrate=Migrate()
new_session=Session()



