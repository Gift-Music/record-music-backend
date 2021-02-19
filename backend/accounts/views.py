from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.views import View

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from music.serializers import MusicSerializer
from . import authentication
from .serializers import *

User = get_user_model()


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


def send_verification_email(request, email):
    """
    Send verification email to user.

    Usage : Register new account, Checking Author of the logged account is owner.
    """

    def message(domain, code):
        return f"아래 계정 확인 코드를 입력하면 회원 인증이 완료됩니다.\n\n" \
               f"계정 확인 코드 : {code}\n\n감사합니다."

    subject = '[RecordMusic] 계정 인증'
    current_site = get_current_site(request)
    current_time = datetime.now()
    domain = current_site.domain
    code = get_random_string(length=5)
    message = message(domain, code)
    mail = EmailMessage(subject, message, to=[email])
    mail.send()

    return code, current_time


class UserProfile(APIView):
    """
    Check Current UserProfile
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get_user(self, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            return user
        except User.DoesNotExist:
            return None

    def get(self, request, user_id, format=None):

        user = self.get_user(user_id)

        if user is None:
            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.is_active is False:
            return Response({"detail": _("Cannot get disabled account.")}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializer(user)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id, format=None):

        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        elif user.is_active is False and user.is_deleted is not None:
            return Response({"detail": _("Cannot modify disabled account.")}, status=status.HTTP_403_FORBIDDEN)

        else:

            cpserializer = UserChangeProfileSerializer(user, data=request.data, partial=True)

            if cpserializer.is_valid():
                if cpserializer.validated_data.get('password') and user.is_social is True:
                    return Response({"detail": _("Social account cannot change password.")},
                                    status=status.HTTP_403_FORBIDDEN)
                user = cpserializer.update(validated_data=cpserializer.validated_data, instance=user)

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

            else:

                return Response(data=cpserializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id, format=None):
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        else:
            user = User.objects.get(user_id=user_id)
            user.is_active = False
            user.is_deleted = timezone.now()
            user.save()

            return Response({"detail": _("User decativated.")}, status=status.HTTP_200_OK)


class UserProfileImage(APIView):
    """
    View for uploaded profile images.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)
    serializer_class = ProfileImageSerializer

    def get_user(self, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            return user
        except User.DoesNotExist:
            return None

    def get(self, request, user_id):
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        profile_images = user.profileimage_set.all()
        serializer = ProfileImageSerializer(profile_images, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects.get(user_id=user_id)
        serializer = ProfileImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.create_profile_image(user, serializer.validated_data)

            return Response(data={"isSuccess": True}, status=status.HTTP_200_OK)

        else:
            return Response(data={"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, user_id):
        """
        request:
            pk of the ProfileImage.
        """
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        if request.data.get('id'):
            user.profile_image = ProfileImage.objects.get(id=request.data.get('id')).file
            user.save()

            return Response(data={"isSuccess": True}, status=status.HTTP_200_OK)

        else:
            return Response(data={"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        """
        request:
            pk of the ProfileImage.
        """
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

        if request.data.get('id'):
            instance = ProfileImage.objects.get(id=request.data.get('id'))
            if instance.file == user.profile_image:
                user.profile_image = None
                user.save()
            ProfileImage.delete(instance)

            return Response(data={"isSuccess": True}, status=status.HTTP_200_OK)

        else:
            return Response(data={"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)


class ExploreUsers(APIView):
    """
    Explore 5 new users to display profile photos, user nicknames, Korean names, and follow/followers.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, format=None):
        last_five = User.objects.all().order_by('-date_joined')[:5]
        serializer = UserProfileSerializer(last_five, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class FollowUser(APIView):
    """
    Follow user whose nickname is <user_id>.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def post(self, request, user_id, format=None):

        user = request.user

        try:
            user_to_follow = User.objects.get(user_id=user_id)

            # cannot follow myself.
            if user == user_to_follow:
                return Response({"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

            # cannot follow withdrawn user or deactivated user.
            if user_to_follow.is_deleted or user_to_follow.is_active is False:
                return Response({"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"isSuccess": False}, status=status.HTTP_404_NOT_FOUND)

        user.follows.add(user_to_follow)

        return Response({"isSuccess": True}, status=status.HTTP_200_OK)


class UnFollowUser(APIView):
    """
    Unfollow user whose nickname is <userid>.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def put(self, request, user_id, format=None):

        user = request.user

        try:
            user_to_follow = User.objects.get(user_id=user_id)

            # cannot unfollow myself.
            if user == user_to_follow:
                return Response({"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

            # cannot unfollow withdrawn user or deactivated user.
            if user_to_follow.is_deleted or user_to_follow.is_active is False:
                return Response({"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"isSuccess": False}, status=status.HTTP_404_NOT_FOUND)

        user.follows.remove(user_to_follow)

        return Response({"isSuccess": True}, status=status.HTTP_200_OK)


class Search(APIView):
    """
    Explore users with that nickname and kor name.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, request, user_id, format=None):

        username = request.data.get('username')

        if user_id is not None:

            if username is not None:
                users = User.objects.filter(user_id__istartswith=user_id, username__istartswith=username)
            else:
                users = User.objects.filter(user_id__istartswith=user_id) | User.objects.filter(
                    username__istartswith=user_id)

            serializer = UserProfileSerializer(users, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        else:

            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserFollowers(APIView):
    """
    Explore users that follow the user.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, request, user_id, format=None):

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        followers = []
        for i in user.followers.values():
            followers.append(User.objects.get(user_pk=i.get('from_user_id')))

        serializer = UserProfileSerializer(followers, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserFollowing(APIView):
    """
    Explore the users that the user follows.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, request, user_id, format=None):

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        following = user.follows.all()

        serializer = UserProfileSerializer(following, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserTokenVerify(APIView):
    """
    Login with JWT token
    request:
        "token" : string
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def post(self, request):

        try:
            logged_user = request.user
            serializer_class = CustomVerifyJSONWebTokenSerializer
            token, user = serializer_class.validate(serializer_class, request.data)

            if user != logged_user:
                return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = UserProfileSerializer(user)
            data = {'token': token,
                    'user': {
                        "profile_image": serializer.data.get('profile_image'),
                        "user_id": serializer.data.get('user_id'),
                        "email": serializer.data.get('email')
                        }
                    }
            return Response(data=data, status=status.HTTP_200_OK)

        except (AssertionError, TypeError):
            return Response({"detail": _("No user found, cannot verify token.")}, status=status.HTTP_404_NOT_FOUND)


class UserTokenRefresh(APIView):
    """
    Refresh token and keep login status
    request:
        "token" : string
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def post(self, request):
        try:
            logged_user = request.user
            serialzier_class = CustomRefreshJSONWebTokenSerializer
            token, user = serialzier_class.validate(serialzier_class, request.data)

            if user != logged_user:
                return Response({"detail": _("User mismatch.")}, status=status.HTTP_401_UNAUTHORIZED)

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
        except (AssertionError, TypeError):
            return Response({"detail": _("No user found, cannot refresh token.")}, status=status.HTTP_404_NOT_FOUND)


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
            if user.is_social is True:
                return Response(data={"detail": _("This account is social account. "
                                                  "Please proceed login with 'Continue with Social Account'")}
                                , status=status.HTTP_403_FORBIDDEN)
            if not user.check_password(password):
                return Response(data={"detail": _("Wrong user id or password.")}
                                , status=status.HTTP_401_UNAUTHORIZED)
            if user.is_deleted:
                return Response(data={"detail": _("This account is a withdrawn account.")}
                                , status=status.HTTP_401_UNAUTHORIZED)
            if user and user.is_active is False:
                if email is not None:
                    code, send_time = send_verification_email(request, email)
                    user.verify_code = f'{code},{send_time}'
                    user.save()

                    return Response(data={"detail": _("Please verify this account. Verification Email Sent.")}
                                    , status=status.HTTP_403_FORBIDDEN)

                else:
                    return Response(data={"detail": _("Email is not found.")}, status=status.HTTP_404_NOT_FOUND)

        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

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
        try:
            user = self.perform_create(serializer)
            user.is_active = False
            user.save()

            email = user.get_user_email()

            if user.is_active is False and email is not None:
                code, send_time = send_verification_email(request, email)
                user.verify_code = f'{code},{send_time}'
                user.save()

                return Response(data={"detail": _("Verification Email Sent.")}, status=status.HTTP_200_OK)

            else:
                return Response(data={"detail": _("Email is not found.")}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            user = User.objects.get(user_id=request.data.get('user_id'))
            if user and user.is_active is False:
                if user.email is not None:
                    code, send_time = send_verification_email(request, user.email)
                    user.verify_code = f'{code},{send_time}'
                    user.save()

                    return Response(data={"detail": _("You have not verify this account. Verification Email Sent.")}
                                    , status=status.HTTP_403_FORBIDDEN)

                else:
                    return Response(data={"detail": _("Email is not found.")}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(data={"detail": _("User exist.")}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        user = serializer.save(self.request)

        return user


class UserActivate(APIView):
    """
    response:
        msg (string)
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def post(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')

        user = User.objects.get(user_id=user_id)
        user_code = user.verify_code.split(',')[0]
        send_time = user.verify_code.split(',')[1]
        send_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M:%S.%f")

        if user is not None and user_code is not None:
            if user_code == code and (datetime.now() - send_time).days < 1:
                user.is_active = True
                user.save()

                msg = "인증 되었습니다."
                return HttpResponse(msg, status=status.HTTP_200_OK)

            else:
                msg = "코드 번호가 다릅니다."
                return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        elif (datetime.now() - send_time).days >= 1:
            email = user.get_user_email()
            code, send_time = send_verification_email(request, email)
            user.verify_code = f'{code},{send_time}'
            user.save()

            msg = "인증 메일이 만료되었습니다. 새로운 인증 메일을 확인해 주세요."
            return HttpResponse(msg, status=status.HTTP_403_FORBIDDEN)

        else:
            msg = "인증에 실패하였습니다."
            return HttpResponse(msg, status=status.HTTP_404_NOT_FOUND)


class PlaylistView(APIView):
    """
    'playlist_num' is not a id of it (playlist_num != playlist_id).
    It indicates which order the playlist is in. Starts with 0.

    playlist_id = real id of playlist (autofield of model, saved in DB)
    playlist_num = order of user's individual playlists.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)

            return Response(user.playlist.values(), status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            playlist_name = request.data.get('playlist_name')
            if playlist_name == '':
                playlist_name = 'Unnamed Playlist'

            playlist = Playlist.objects.create(user=user, playlist_name=playlist_name)
            playlist.save()
            user.playlist.add(playlist)
            user.save()

            serializer = PlaylistSerializer(playlist)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)

            playlist_name = request.data.get('playlist_name')
            playlist_num = request.data.get('playlist_num')
            try:
                playlist = user.playlist.all()[int(playlist_num)]
            except IndexError:
                return Response(data='Index Error', status=status.HTTP_400_BAD_REQUEST)

            playlist.playlist_name = playlist_name
            playlist.save()

            serializer = PlaylistSerializer(playlist)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)

            playlist_num = request.data.get('playlist_num')
            try:
                playlist = user.playlist.all()[int(playlist_num)]
            except IndexError:
                return Response(data='Index Error', status=status.HTTP_400_BAD_REQUEST)
            user.playlist.remove(playlist)
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PlaylistDetailView(APIView):
    """
    'playlist_num' is not a id of it (playlist_num != playlist_id).
    It indicates which order the playlist is in. Starts with 0.

    playlist_id = real id of playlist (autofield of model, saved in DB).
    playlist_num = order of user's individual playlists.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get(self, request, user_id, playlist_num):
        try:
            user = User.objects.get(user_id=user_id)
            try:
                playlist = user.playlist.all()[int(playlist_num)]
            except IndexError:
                return Response(data='Index Error', status=status.HTTP_400_BAD_REQUEST)
            serializer = MusicSerializer(playlist.musics, many=True)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, user_id, playlist_num):
        try:
            user = User.objects.get(user_id=user_id)
            try:
                playlist = user.playlist.all()[int(playlist_num)]
            except IndexError:
                return Response(data='Index Error', status=status.HTTP_400_BAD_REQUEST)
            music = request.data.get('music_id')
            playlist.musics.add(music)
            user.save()

            serializer = MusicSerializer(playlist.musics, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id, playlist_num):
        try:
            user = User.objects.get(user_id=user_id)
            try:
                playlist = user.playlist.all()[int(playlist_num)]
            except IndexError:
                return Response(data='Index Error', status=status.HTTP_400_BAD_REQUEST)
            music = request.data.get('music_id')
            playlist.musics.remove(music)
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
