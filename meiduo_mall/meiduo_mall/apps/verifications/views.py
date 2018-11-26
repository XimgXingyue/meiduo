import random

from django.http.response import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
import logging

# Create your views here.
from meiduo_mall.libs.captcha.captcha import captcha
from verifications import constants
from verifications import serializers
from meiduo_mall.utils.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms_code


logger = logging.getLogger('django')
class ImageCodeView(APIView):
    '''
    image code
    '''
    def get(self, request, code_id):
        # 生成验证码图片
        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="images/jpg")


# url('^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数：
        mobile, image_code_id, text
    """
    serializer_class = serializers.ImageCodeCheckSerializer

    def get(self, request, mobile):
        '''
        create sms code
        :param request:
        :param mobile:
        :return:
        '''
        # judge image code and whether in 60s
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # create sms code
        sms_code = "%06d" % random.randint(0, 999999)
        print(sms_code)

        # store send flag in redis
        redis_conn = get_redis_connection('verify_codes')

        # way 1:
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # way 2: use pipeline
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # send massage
        # try:
        #     ccp = CCP()
        #     result = ccp.send_template_sms(mobile, [sms_code, 5], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("send sms code error[mobile: %s, message: %s]" % (mobile, e))
        #     return Response({'message': 'failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # else:
        #     if result == 0:
        #         logger.info("send sms code successfully[mobile: %s]" % mobile)
        #         return Response({'message': 'OK'})
        #     else:
        #         logger.warning("send sms code failed[mobile: %s]" % mobile)
        #         return Response({'message': 'failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 使用celery发送sms—code
        send_sms_code.delay(mobile, sms_code, constants.SMS_CODE_TEMP_ID)
        return Response({'message': 'OK'})
