import json

import requests

from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import status, permissions
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django.utils.translation import ugettext_lazy as _

from accounts.models import User
from accounts.serializers import UserSerializerWithToken
from backend import settings


# ----- FACEBOOK ----- #

@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
def fblogin(request):
    """
    Redirect to Facebook account linking
    """
    app_id = settings.FACEBOOK_APP_ID
    redirect_uri = reverse('accounts:facebook_login_redirect')

    url = f'https://www.facebook.com/v7.0/dialog/oauth?' \
          f'client_id={app_id}' \
          f'&redirect_uri=http://localhost:9080{redirect_uri}' \
          f'&scope=email,public_profile'
    return redirect(url)


@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
@renderer_classes((JSONRenderer,))
def fblogin_redirect(request):
    app_id = settings.FACEBOOK_APP_ID
    app_secret = settings.FACEBOOK_APP_SECRET
    redirect_uri = reverse('accounts:facebook_login_redirect')

    # get access token from redirected url.
    code = request.GET['code']
    url = 'https://graph.facebook.com/v4.0/oauth/access_token'
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'redirect_uri': f'http://localhost:9080{redirect_uri}',
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

    """
    Possible output of user_info:
    
    ('id', 'test_id')
    ('first_name', 'Jun Hyeok')
    ('last_name', 'Lee')
    ('picture', {
        'data': {
            'height': 50, 
            'is_silhouette': False, 
            'url': 'https://scontent.xx.fbcdn.net/v/t1.0-1/...', 
            'width': 50
            }
        }
    )
    ('email', 'bnbong@naver.com')
    
    etc..
    """

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

        # for security, make account based with social account that user provides us
        # with random password and hashes it so outsider cannot open corresponding account's info.
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


# ----- GOOGLE ----- #

@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
def gglogin(request):
    """
    Redirect to Facebook account linking
    """
    app_id = settings.GOOGLE_APP_ID
    redirect_uri = reverse('accounts:google_login_redirect')

    url = f'https://accounts.google.com/o/oauth2/auth/oauthchooseaccount?' \
          f'client_id={app_id}' \
          f'&redirect_uri=http://localhost:9080{redirect_uri}' \
          f'&scope=https://www.googleapis.com/auth/userinfo.email' \
          f' https://www.googleapis.com/auth/userinfo.profile' \
          f' openid' \
          f'&response_type=code'
    return redirect(url)


@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
@renderer_classes((JSONRenderer,))
def gglogin_redirect(request):
    app_id = settings.GOOGLE_APP_ID
    app_secret = settings.GOOGLE_APP_SECRET
    redirect_uri = reverse('accounts:google_login_redirect')

    # get access token from redirected url.
    code = request.GET['code']
    verify_oauth2_token_url = f'https://accounts.google.com/o/oauth2/token?code={code}' \
                              f'&redirect_uri=http://localhost:9080{redirect_uri}' \
                              f'&client_id={app_id}' \
                              f'&client_secret={app_secret}' \
                              f'&grant_type=authorization_code'
    token_response = requests.post(verify_oauth2_token_url)

    id_token = token_response.json()['id_token']
    user_info_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
    user_info = requests.get(user_info_url)
    user_info = user_info.json()

    """
    Possible output of user_info:
    
    {
    // These six fields are included in all Google ID Tokens.
    "iss": "https://accounts.google.com",
    "sub": "110169484474386276334",
    "azp": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
    "aud": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
    "iat": "1433978353",
    "exp": "1433981953",

    // These seven fields are only included when the user has granted the "profile" and
    // "email" OAuth scopes to the application.
    "email": "testuser@gmail.com",
    "email_verified": "true",
    "name" : "Test User",
    "picture": "https://lh4.googleusercontent.com/-kYgzyAWpZzJ/ABCDEFGHI/AAAJKLMNOP/tIXL9Ir44LE/s99-c/photo.jpg",
    "given_name": "Test",
    "family_name": "User",
    "locale": "en"
    
    etc..
    }
    """

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
        try:
            email = user_info['email']
        except KeyError:
            return Response(data={"detail": _("The email for that social account could not be found. "
                                              "Please make your email public so that we can check your email.")},
                            status=status.HTTP_403_FORBIDDEN)

        user_id = email.split('@')[0]
        # if user have not granted "profile" and cannot see user's name
        try:
            username = user_info['name']

        except KeyError:
            username = ''

        # for security, make account based with social account that user provides us
        # with random password and hashes it so outsider cannot open corresponding account's info.
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
