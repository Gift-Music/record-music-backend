import json

import requests

from django.shortcuts import redirect
from rest_framework import status, permissions
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django.utils.translation import ugettext_lazy as _

from accounts.models import User
from accounts.serializers import UserSerializerWithToken
from backend import settings


@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
def fblogin(request):
    """
    Redirect to Facebook account linking
    """
    app_id = settings.FACEBOOK_APP_ID

    url = f'https://www.facebook.com/v7.0/dialog/oauth?' \
          f'client_id={app_id}' \
          f'&redirect_uri=http://localhost:9080/accounts/sociallogin/facebook/redirect/' \
          f'&scope=email,public_profile'
    return redirect(url)


@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
@renderer_classes((JSONRenderer,))
def fblogin_redirect(request):
    app_id = settings.FACEBOOK_APP_ID
    app_secret = settings.FACEBOOK_APP_SECRET

    # get access token from redirected url.
    code = request.GET['code']
    url = 'https://graph.facebook.com/v4.0/oauth/access_token'
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'redirect_uri': 'http://localhost:9080/accounts/sociallogin/facebook/redirect/',
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'code': code,
    }

    # debug access token is valid form.
    response = requests.get(url, params)
    url_debug_token = 'https://graph.facebook.com/debug_token'

    access_token = response.json()['access_token']

    params_debug_token = {
        "input_token": access_token,
        "access_token": f'{app_id}|{app_secret}'
    }

    debug_info = requests.get(url_debug_token, params=params_debug_token)

    if not debug_info.json()['data']:
        return Response(data={"detail": _("Invalid social account.")}, status=status.HTTP_403_FORBIDDEN)

    url_user_info = 'https://graph.facebook.com/me'
    user_info_fields = [
        'id',
        'first_name',
        'last_name',
        'picture',
        'email',
    ]
    params_user_info = {
        "fields": ','.join(user_info_fields),
        "access_token": access_token
    }

    user_info = requests.get(url_user_info, params=params_user_info)
    user_info = user_info.json()

    try:
        # login with social account if social account is in User
        email = json.dumps(user_info['email'])
        email = email.replace('"', '')
        user = User.objects.get(email=email)
        if user.is_social is False:
            return Response(data={"detail": _("User already exists and not registered with social account.")},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializerWithToken(user)

        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('user_id'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        # make new account with social account
        email = user_info['email']
        user_id = email.split('@')[0]
        username = user_info['last_name'] + user_info['first_name']
        password = User.objects.make_random_password()

        user = User(
            email=email,
            user_id=user_id,
            username=username,
            is_social=True,
        )
        user.set_password(password)
        user.save()

        serializer = UserSerializerWithToken(user)

        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('user_id'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_201_CREATED)
