from datetime import datetime, timedelta
from calendar import timegm

import jwt
import uuid

from rest_framework import serializers
from rest_framework_jwt.compat import get_username_field as get_userid_field
from rest_framework_jwt.serializers import jwt_decode_handler
from rest_framework_jwt.settings import api_settings
from django.utils.translation import ugettext as _

from .models import User

jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def get_userid(user):
    """
    Return the user's nickname.
    """
    try:
        user_id = user.get_userid()
    except AttributeError:
        user_id = user.user_id

    return user_id


def custom_jwt_payload_handler(user):
    """
    The role of passing over the user's pk number, nickname, expiration time, e-mail, orig_eat information stored
    in the db to be encoded as jwt token.
    """
    userid_field = get_userid_field()
    user_id = get_userid(user)
    user_pk = user.user_pk

    payload = { # user_id is a pk of user. Not userid field in User(accounts.User)
        'user_pk': user_pk,
        'user_id': user_id,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }
    if hasattr(user, 'email'):
        payload['email'] = user.email
    if isinstance(user_pk, uuid.UUID):
        payload['user_pk'] = str(user_pk)

    payload[userid_field] = user_id

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


class UserSerializerWithToken(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):

        payload = custom_jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)

        return token

    class Meta:
        model = User
        fields = ('token', 'user_id', 'username', 'email', 'password', 'profile_image')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Returns the profile of that user.
    """
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'profile_image',
            'user_id',
            'username',
            'email',
            'followers_count',
            'following_count',
        )


class CustomRegisterSerializer(serializers.ModelSerializer):
    """
    The serializer that creates a new user.
    It Hashes the password and save it.
    """
    user_id = serializers.CharField(
        max_length=150,
        min_length=1,
    )
    username = serializers.CharField(
        max_length=100,
        min_length=1,
    )
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def save(self, request):
        user = User(
            email=request.data.get('email'),
            user_id=request.data.get('user_id'),
            username=request.data.get('username'),
        )
        user.set_password(request.data.get('password'))
        user.is_active = False
        user.save()
        return user

    class Meta:
        model = User
        fields = (
            'user_id',
            'username',
            'email',
            'password',
            'is_active'
        )


def jwt_get_userid_from_payload(payload):
    return payload.get('user_id')


class BaseVerifyUserSerializer(serializers.ModelSerializer):
    """
    serializer that determines the user's information and token values.
    It acts as the BaseSerializer for CustomVerifyJSONWebTokenSerializer and CustomRefreshJSONWebTokenSerializer
    """
    token = serializers.CharField()

    def _check_user_id(self, payload):
        user_id = jwt_get_userid_from_payload(payload)

        if not user_id:
            msg = _('Invalid payload')
            raise serializers.ValidationError(msg)

        # Make sure user exists
        try:
            user = User.objects.get_by_natural_key(user_id)
        except User.DoesNotExist:
            msg = _("User Does not exist.")
            raise serializers.ValidationError(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise serializers.ValidationError(msg)

        return user

    def _check_payload_user(self, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        try:
            payload = jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise serializers.ValidationError(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise serializers.ValidationError(msg)

        return payload


class CustomVerifyJSONWebTokenSerializer(BaseVerifyUserSerializer):
    """
    Check the veracity of an access token.
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload_user(self, token=token)
        user = self._check_user_id(self, payload=payload)

        # userprofile = UserSerializerWithToken(user)

        return token, user


class CustomRefreshJSONWebTokenSerializer(BaseVerifyUserSerializer):
    """
    Refresh user access token
    """

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload_user(self, token=token)
        user = self._check_user_id(self, payload=payload)
        # Get and check 'orig_iat'
        orig_iat = payload.get('orig_iat')

        if orig_iat:
            # Verify expiration
            refresh_limit = api_settings.JWT_REFRESH_EXPIRATION_DELTA

            if isinstance(refresh_limit, timedelta):
                refresh_limit = (refresh_limit.days * 24 * 3600 +
                                 refresh_limit.seconds)

            expiration_timestamp = orig_iat + int(refresh_limit)
            now_timestamp = timegm(datetime.utcnow().utctimetuple())

            if now_timestamp > expiration_timestamp:
                msg = _('Refresh has expired.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('orig_iat field is required.')
            raise serializers.ValidationError(msg)

        new_payload = custom_jwt_payload_handler(user)
        new_payload['orig_iat'] = orig_iat

        return jwt_encode_handler(new_payload), user  # return new token and user data
