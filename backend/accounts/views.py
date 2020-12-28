from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth import get_user_model
from rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer, UserSerializerWithToken, UserProfileSerializer

User = get_user_model()


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


@api_view(['GET'])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserList(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = UserSerializerWithToken(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfile(APIView):
    """
    Check Current UserProfile
    """

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def get(self, request, username, format=None):

        user = self.get_user(username)

        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, username, format=None):

        req_user = request.user

        user = self.get_user(username)

        if user is None:

            return Response(status=status.HTTP_404_NOT_FOUND)

        elif user.username != req_user.username:

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
        serializer = UserSerializer(last_five, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):

    def post(self, request, user_id, format=None):
        user = request.user

        try:
            user_to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.following.add(user_to_follow)
        user_to_follow.followers.add(user)

        return Response(status=status.HTTP_200_OK)


class UnFollowUser(APIView):

    def post(self, request, user_id, format=None):

        user = request.user

        try:
            user_to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.following.remove(user_to_follow)
        user_to_follow.followers.remove(user)

        return Response(status=status.HTTP_200_OK)


class Search(APIView):

    def get(self, request, format=None):

        username = request.query_params.get('username', None)

        if username is not None:

            users = User.objects.filter(username__istartswith=username)

            serializer = UserSerializer(users, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        else:

            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserFollowers(APIView):

    def get(self, request, username, format=None):

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        followers = user.followers.all()

        serializer = UserSerializer(followers, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserFollowing(APIView):

    def get(self, request, username, format=None):

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        following = user.following.all()

        serializer = UserSerializer(following, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


# class MakeFriend(APIView):
#
#     def post(self, request, user_id, format=None):
#         user = request.user
#
#         try:
#             user_to_friends = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         user.friends.add(user_to_friends)
#         user_to_friends.friends.add(user)
#
#         return Response(status=status.HTTP_200_OK)
#
#
# class DeleteFriend(APIView):
#
#     def post(self, request, user_id, format=None):
#
#         user = request.user
#
#         try:
#             user_to_friends = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         user.friends.remove(user_to_friends)
#         user_to_friends.friends.remove(user)
#
#         return Response(status=status.HTTP_200_OK)
#
#
# class UserFriends(APIView):
#
#     def get(self, request, username, format=None):
#
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#
#         friends = user.friends.all()
#
#         serializer = UserSerializer(friends, many=True)
#
#         return Response(data=serializer.data, status=status.HTTP_200_OK)
