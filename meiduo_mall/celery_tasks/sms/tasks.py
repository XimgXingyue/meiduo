import logging
from celery_tasks.main import celery_app
from .utils.yuntongxun.sms import CCP

logger = logging.getLogger('django')


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code, temp_id):
    '''send sms code'''
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, 5], temp_id)
    except Exception as e:
        logger.error("send sms code error[mobile: %s, message: %s]" % (mobile, e))
    else:
        if result == 0:
            logger.info("send sms code successfully[mobile: %s]" % mobile)
        else:
            logger.warning("send sms code failed[mobile: %s]" % mobile)
