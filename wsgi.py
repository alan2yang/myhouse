# 与web服务器连接
import os

from ihome import create_app
from dotenv import load_dotenv


dotenv_path=os.path.join(os.path.dirname(__file__),'.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


app=create_app('development')
