from celery import Celery
from ihome.libs.ytx.sms import CCP

celery_app=Celery('ihome',broker='redis://127.0.0.1:6379/1')


@celery_app.task
def send_sms(to,datas,temp_id):
    ccp=CCP()
    ccp.send_template_sms(to,datas,temp_id)