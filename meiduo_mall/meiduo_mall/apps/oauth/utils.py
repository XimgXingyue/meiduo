import json
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
import logging
from django.conf import settings
from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer

from oauth import constants
from .exceptions import OAuthQQAPIError

logger = logging.getLogger('django')
class OAuthQQ:
    ''' qq authorizate class'''

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id if client_id else settings.QQ_CLIENT_ID
        self.client_secret = client_secret if client_secret else settings.QQ_CLIENT_SECRET
        self.redirect_uri = redirect_uri if redirect_uri else settings.QQ_REDIRECT_URI
        # self.state = state if state else settings.QQ_STATE
        # It could be write as:
        self.state = state or settings.QQ_STATE

    def get_qq_login_url(self):
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
        }

        url += urlencode(params)
        return url

    def get_access_token(self, code):
        url = 'https://graph.qq.com/oauth2.0/token?'
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        url += urlencode(params)
        try:

            response = urlopen(url)
            response_data = response.read()  # the result is bytes
            response_data = response_data.decode()  # str

            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
            # get access_token value
            access_token = parse_qs(response_data).get('access_token')
            # print(access_token)
        except Exception as e:
            logger.error('get access_token error: %s' % e)
            raise OAuthQQAPIError
        else:
            return access_token[0]

    def get_openid(self, access_token):
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token

        try:
            response = urlopen(url)
            response_data = response.read().decode()

            # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            response_data = response_data[10:-4]
            openid = json.loads(response_data).get('openid')
            # print(openid)
        except Exception as e:
            logger.error('get openid error: %s' % e)
            raise OAuthQQAPIError
        else:
            return openid

    def generate_user_access_token(self, openid):
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.QQ_USER_TOKEN_EXPIRES)
        token = serializer.dumps({'openid': openid})  # bytes
        return token.decode()

    @staticmethod
    def check_bind_access_token(access_token):
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return None
        else:
            return data['openid']

