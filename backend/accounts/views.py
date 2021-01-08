from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth import get_user_model
from rest_auth.models import TokenModel
from rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.views import LoginView

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework_jwt.views import JSONWebTokenAPIView, VerifyJSONWebToken

from .serializers import UserSerializerWithToken, UserProfileSerializer, CustomVerifyJSONWebTokenSerializer

User = get_user_model()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


@api_view(['GET'])
def current_user(request):
    serializer = UserSerializerWithToken(request.user)
    return Response(serializer.data)


# @api_view(['GET'])
# def validate_jwt_token(request):
#
#     try:
#         token = request.META['HTTP_AUTHORIZATION']
#         data = {'token': token.split()[1]}
#         valid_data = VerifyJSONWebTokenSerializer().validate(data)
#     except Exception as e:
#         return Response(e)
#
#     return Response(status=status.HTTP_200_OK)


# class UserList(APIView):
#
#     permission_classes = (permissions.AllowAny,)
#
#     def post(self, request, format=None):
#         serializer = UserSerializerWithToken(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    신규 가입 유저 5명을 탐색한다.
    """
    def get(self, request, format=None):
        last_five = User.objects.all().order_by('-date_joined')[:5]
        serializer = UserSerializerWithToken(last_five, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):

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


class Search(APIView): # 유저 한글 이름(현재 하단에 구현된 코드)과 유저 닉네임으로 검색하는 기능(추후 추가)

    def get(self, request, format=None):

        userid = request.query_params.get('userid', None)

        if userid is not None:

            users = User.objects.filter(userid__istartswith=userid)

            serializer = UserSerializerWithToken(users, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        else:

            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserFollowers(APIView):

    def get(self, request, userid, format=None):

        try:
            user = User.objects.get(userid=userid)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        followers = user.followers.all()

        serializer = UserSerializerWithToken(followers, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserFollowing(APIView):

    def get(self, request, userid, format=None):

        try:
            user = User.objects.get(userid=userid)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        following = user.following.all()

        serializer = UserSerializerWithToken(following, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserTokenVerify(APIView):
    """
    Login with JWT token
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


class UserLogout(APIView):
    pass


class UserRegister(APIView):
    """
    request:
        "user_id" : string
        "email" : string
        "password" : string
        "username" : string
    """
    pass
