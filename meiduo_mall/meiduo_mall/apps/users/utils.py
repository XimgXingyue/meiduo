import re

from django.contrib.auth.backends import ModelBackend

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    '''return user_id and username except token'''

    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    '''Django always use username to authorization but we need user username or mobile
    so, we need to define a class to overwrite the authenticate function to solve it'''

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user




