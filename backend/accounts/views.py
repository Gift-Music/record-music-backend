from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from rest_auth.app_settings import create_token
from rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from backend import settings
from .serializers import UserSerializerWithToken, UserProfileSerializer, CustomRegisterSerializer, \
    CustomVerifyJSONWebTokenSerializer, custom_jwt_payload_handler, CustomRefreshJSONWebTokenSerializer

User = get_user_model()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


class UserProfile(APIView):
    """
    Check Current UserProfile
    """

    def get_user(self, userid):
        try:
            user = User.objects.get(userid=userid)
            return user
        except User.DoesNotExist:
            return None

    def get(self, request, userid, format=None):

        user = self.get_user(userid)

        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    # 자신의 프로필을 수정.
    def put(self, request, userid, format=None):

        req_user = request.user

        user = self.get_user(userid)

        if user is None:

            return Response(status=status.HTTP_404_NOT_FOUND)

        elif user.userid != req_user.userid:

            return Response(status=status.HTTP_401_UNAUTHORIZED)

        else:

            serializer = UserProfileSerializer(user, data=request.data, partial=True)

            if serializer.is_valid():

                serializer.save()

                return Response(data=serializer.data, status=status.HTTP_200_OK)

            else:

                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExploreUsers(APIView):
    """
    Explore 5 new users to display profile photos, user nicknames, Korean names, and follow/followers.
    """
    def get(self, request, format=None):
        last_five = User.objects.all().order_by('-date_joined')[:5]
        serializer = UserProfileSerializer(last_five, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):
    """
    Follow user whose nickname is <userid>.
    """

    def post(self, request, userid, format=None):
        user = request.user

        try:
            user_to_follow = User.objects.get(userid=userid)
            if user == user_to_follow: return Response(status=status.HTTP_400_BAD_REQUEST) # 자기 자신을 팔로우할 수 없다.
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.following.add(user_to_follow)
        user_to_follow.followers.add(user)

        return Response(status=status.HTTP_200_OK)


class UnFollowUser(APIView):
    """
    Unfollow user whose nickname is <userid>.
    """

    def put(self, request, userid, format=None):

        user = request.user

        try:
            user_to_follow = User.objects.get(userid=userid)
            if user == user_to_follow: return Response(status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.following.remove(user_to_follow)
        user_to_follow.followers.remove(user)

        return Response(status=status.HTTP_200_OK)


class Search(APIView): # 유저 한글 이름으로 검색하는 기능 추가할 예정.
    """
    Explore users with that nickname.
    """

    def get(self, request, format=None):

        userid = request.data.get('userid', None)

        if userid is not None:

            users = User.objects.filter(userid__istartswith=userid)

            serializer = UserProfileSerializer(users, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        else:

            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserFollowers(APIView):
    """
    Explore users that follow the user.
    """

    def get(self, request, userid, format=None):

        try:
            user = User.objects.get(userid=userid)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        followers = user.followers.all()

        serializer = UserProfileSerializer(followers, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserFollowing(APIView):
    """
    Explore the users that the user follows.
    """

    def get(self, request, userid, format=None):

        try:
            user = User.objects.get(userid=userid)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        following = user.following.all()

        serializer = UserProfileSerializer(following, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserTokenVerify(APIView):
    """
    Login with JWT token
    request:
        "token" : string
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer_class = CustomVerifyJSONWebTokenSerializer
        token, user = serializer_class.validate(serializer_class, request.data)

        serializer = UserSerializerWithToken(user)
        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('userid'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_200_OK)


class UserTokenRefresh(APIView):
    """
    Refresh token and keep login status
    request:
        "token" : string
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serialzier_class = CustomRefreshJSONWebTokenSerializer
        token, user = serialzier_class.validate(serialzier_class, request.data)

        serializer = UserSerializerWithToken(user)
        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('userid'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_200_OK)


class UserLogin(APIView):
    """
    request:
        "email" : string
        "password" : string
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):

        try:
            email = request.data.get('email')
            password = request.data.get('password')

            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializerWithToken(user)

        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('userid'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_200_OK)


def user_jwt_encode(user):
    """
    use custom_jwt_payload_handler to encode user information into jwt token
    """
    try:
        from rest_framework_jwt.settings import api_settings
    except ImportError:
        raise ImportError("djangorestframework_jwt needs to be installed")

    jwt_payload_handler = custom_jwt_payload_handler
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    return jwt_encode_handler(payload)


class UserRegister(APIView):
    """
    request:
        "user_id" : string
        "email" : string
        "password" : string
        "username" : string
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):

        serializer = CustomRegisterSerializer(data=request.data)
        user = self.perform_create(serializer)
        # userdata = self.get_response_user_data(user)

        serializer = UserSerializerWithToken(user)

        user_token = serializer.data.get('token')
        data = {'token': user_token,
                'user': {
                    "profile_image": serializer.data.get('profile_image'),
                    "user_id": serializer.data.get('userid'),
                    "email": serializer.data.get('email')
                    }
                }

        return Response(data=data, status=status.HTTP_201_CREATED)

    # def get_response_user_data(self, user):
    #     # if allauth_settings.EMAIL_VERIFICATION == \
    #     #         allauth_settings.EmailVerificationMethod.MANDATORY:
    #     #     return {"detail": _("Verification e-mail sent.")}
    #
    #     if getattr(settings, 'REST_USE_JWT', False):
    #         data = {
    #             'user': user,
    #             'token': self.token
    #         }
    #         return JWTSerializer(data).data
    #     else:
    #         return TokenSerializer(user.auth_token).data

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        if getattr(settings, 'REST_USE_JWT', False):
            self.token = user_jwt_encode(user)
        else:
            create_token(self.token, user, serializer)

        return user
