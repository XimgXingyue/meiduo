from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from oauth.models import OAuthQQUser
from oauth.utils import OAuthQQ
from users.models import User


class OAuthQQUserSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    access_token = serializers.CharField(label='operation certification', write_only=True)
    mobile = serializers.RegexField(label='mobile', regex=r'^1[3-9]\d{9}$')
    sms_code = serializers.CharField(label='sms_code', write_only=True)
    class Meta:
        model = User
        fields = ('token', 'access_token', 'mobile', 'sms_code', 'password', 'id', 'username')
        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages':{
                    'min_length': 'the length of password must be from 8 to 20',
                    'max_length': 'the length of password must be from 8 to 20',
                }
            }
        }

    def validate(self, data):
        # judge access_token
        access_token = data['access_token']
        openid = OAuthQQ.check_bind_access_token(access_token)
        if not openid:
            raise serializers.ValidationError('invalid access_token')
        data['openid'] = openid

        # judge sms_code
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if real_sms_code is None:
            raise serializers.ValidationError('Invalid SMS verification code')

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('sms_code error')

        # judge password
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = data['password']
            if not user.check_password(password):
                raise serializers.ValidationError('password error!')
            data['user'] = user
        return data

    def create(self, validated_data):
        openid = validated_data['openid']
        user = validated_data.get('user')
        mobile = validated_data['mobile']
        password = validated_data['password']

        if not user:
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)

        OAuthQQUser.objects.create(user=user, openid=openid)

        # create jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        self.context['view'] = user  # 给视图添加上user属性， 以便在视图中调用（合并购物车时）

        return user
