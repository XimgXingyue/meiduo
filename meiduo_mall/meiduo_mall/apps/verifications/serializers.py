from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers
import logging

logger = logging.getLogger('django')


class ImageCodeCheckSerializer(serializers.Serializer):
    '''
    image code validate
    '''
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # query real image code in redis
        redis_conn = get_redis_connection('verify_codes')
        real_image_code_text= redis_conn.get('img_%s' % image_code_id)
        if not real_image_code_text:
            raise serializers.ValidationError('Image verification code is invalid')

        # delete image code if it exists
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # compare image code
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != text.lower():
            raise serializers.ValidationError('image code error')

        # judge if it is in 60s
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('Requests are too frequent')

        return attrs