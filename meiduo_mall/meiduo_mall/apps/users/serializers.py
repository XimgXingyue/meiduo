import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from celery_tasks.email.tasks import send_verify_email

from .models import User, Address


class CreateUserSerializer(serializers.ModelSerializer):
    '''
    create user model class
    '''
    password2 = serializers.CharField(label='confirmed password', write_only=True)
    sms_code = serializers.CharField(label='sms_code', write_only=True)
    allow = serializers.CharField(label='agree_protocol', write_only=True)
    token = serializers.CharField(label='jwt_token', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
            }
        }

    def validate_mobile(self, value):
        '''validate mobile num'''
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('mobile format error')
        return value

    def validate_allow(self, value):
        '''validate whether the allow is true'''
        if value != 'true':
            raise serializers.ValidationError('please agree the protocol to register')
        return value

    def validate(self, data):
        '''confirm the psw and psw2'''
        if data['password'] != data['password2']:
            raise serializers.ValidationError('the passwords are not the same')

        '''judge the sms_code'''
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if real_sms_code is None:
            raise serializers.ValidationError('Invalid SMS verification code')

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('sms_code error')

        return data

    def create(self, validated_data):
        '''create a new user'''

        # 1 delete the fields that not be included in user model
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        print(validated_data)

        # use django to create
        # user = User.objects.create(**validated_data)

        # use the method in serializers.ModelSerializer class
        user = super().create(validated_data)

        # use django to decode the psw
        user.set_password(validated_data['password'])
        user.save()

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        email = validated_data['email']
        instance.email = email
        instance.save()

        # create verify url
        verify_url = instance.generate_verify_email_url()

        # send email
        send_verify_email.delay(email, verify_url)
        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    '''
    user address serializer
    '''
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='province_id', required=True)
    city_id = serializers.IntegerField(label='city_id', required=True)
    district_id = serializers.IntegerField(label='district_id', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')


    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('mobile format error')
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('title',)