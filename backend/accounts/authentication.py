import jwt
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from accounts.serializers import jwt_get_userid_from_payload
from backend import settings


class CustomJWTAuthentication(BaseAuthentication):
    '''
        custom authentication class for DRF and JWT
    '''

    def authenticate(self, request):

        User = get_user_model()
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            # header = 'JWT xxxxxxxxxxxxxxxxxxxxxxxx'
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(
                access_token, settings.SECRET_KEY, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        user = User.objects.get_by_natural_key(user_id=jwt_get_userid_from_payload(payload))
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('user is inactive')

        return (user, None)
