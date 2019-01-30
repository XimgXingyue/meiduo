from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework_jwt.settings import api_settings

from cart.utils import merge_cart_cookie_to_redis
from oauth.serializers import OAuthQQUserSerializer
from .exceptions import OAuthQQAPIError
from .models import OAuthQQUser
# Create your views here.

# url(r'^qq/authorization/$', views.QQAuthURLView.as_view())
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.utils import OAuthQQ


class QQAuthURLView(APIView):
    '''get QQ login URL'''

    def get(self, request):
        next = request.query_params.get('next')
        oauth = OAuthQQ(state=next)
        login_url = oauth.get_qq_login_url()
        return Response({'login_url': login_url})


class QQAuthUserView(CreateAPIView):
    '''QQ login user    ?code=xxxxxx'''

    serializer_class = OAuthQQUserSerializer

    def get(self,request):
        code = request.query_params.get('code')
        if not code:
            return Response({'message': 'lost code param'})

        oauth = OAuthQQ()
        try:
            # use code to request access_token from QQ
            access_token = oauth.get_access_token(code)

            # use access_token to ask for openid
            openid = oauth.get_openid(access_token)

        except OAuthQQAPIError:
            return Response({'message': 'get access_token or openid error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # use openid to query database
        try:
            QQuser = OAuthQQUser.objects.get(openid=openid)

        # create token if there is no such user
        except OAuthQQUser.DoesNotExist:
            # this is the first time user use QQ login
            token = oauth.generate_user_access_token(openid)
            return Response({'access_token': token})

        # if there is the user
        else:
            user = QQuser.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response = Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

            # 合并购物车
            response = merge_cart_cookie_to_redis(request, user, response)
            return response

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # 合并购物车
        user = self.user
        response = merge_cart_cookie_to_redis(request, user, response)
        return response






