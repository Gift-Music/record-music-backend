import jwt

from rest_framework import serializers
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer, jwt_decode_handler
from rest_framework_jwt.settings import api_settings
from django.utils.translation import ugettext as _
from .models import User

jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class UserSerializerWithToken(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)

        return token

    class Meta:
        model = User
        fields = ('token', 'userid', 'username', 'email', 'password', 'profile_image')


class UserProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'profile_image',
            'userid',
            'username',
            'followers_count',
            'following_count',
        )


class CustomVerifyJSONWebTokenSerializer(VerifyJSONWebTokenSerializer):
    """
    Check the veracity of an access token.
    """

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

    def _check_user_id(self, payload):
        userid = payload.get('userid')

        if not userid:
            msg = _('Invalid payload.')
            raise serializers.ValidationError(msg)

        try:
            user = User.objects.get_by_natural_key(userid)
        except User.DoesNotExist:
            msg = _("User doesn't exist.")
            raise serializers.ValidationError(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise serializers.ValidationError(msg)

        return user

    def validate(self, attrs):
        token = attrs['token']

        payload = self._check_payload_user(self, token=token)
        user = self._check_user_id(self, payload=payload)

        # userprofile = UserSerializerWithToken(user)

        return token, user
