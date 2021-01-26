from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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


def send_verification_email(request, user, email, link):
    """
    Send verification email to user.

    Usage : Register new account, Checking Author of the logged account is owner.
    """
    def message(domain, uidb64, token):
        activation_link = f"{link}/{uidb64}/{token}"
        return f"아래 링크를 클릭하면 회원 인증이 완료됩니다.\n\n" \
               f"회원 인증 완료 링크 : {activation_link}\n\n감사합니다."

    subject = '[RecordMusic] 계정 인증'
    current_site = get_current_site(request)
    domain = current_site.domain
    uidb64 = urlsafe_base64_encode(force_bytes(user.user_pk))
    token = default_token_generator.make_token(user=user)  # One-time token for account authentication
    message = message(domain, uidb64, token)
    mail = EmailMessage(subject, message, to=[email])
    mail.send()


class UserProfile(APIView):
    """
    Check Current UserProfile

    todo : changing profile image
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
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id, format=None):

        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response(status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response(status=status.HTTP_401_UNAUTHORIZED)

        else:

            cpserializer = UserChangeProfileSerializer(user, data=request.data, partial=True)

            if cpserializer.is_valid():
                cpserializer.update(validated_data=cpserializer.validated_data, instance=user)
                user = cpserializer.save()

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


class UserDelete(APIView):
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def get_user(self, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            return user
        except User.DoesNotExist:
            return None

    # User withdrawal
    def put(self, request, user_id):
        req_user = request.user

        user = self.get_user(user_id)

        if user is None:

            return Response({"isSuccess": False}, status=status.HTTP_404_NOT_FOUND)

        elif user.user_id != req_user.user_id:

            return Response({"isSuccess": False}, status=status.HTTP_401_UNAUTHORIZED)

        else:
            user = User.objects.get(user_id=user_id)
            user.is_active = False
            user.is_deleted = timezone.now()
            user.save()

            return Response({"isSuccess": True}, status=status.HTTP_200_OK)


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
    permission_classes = (permissions.AllowAny,)

    def post(self, request):

        try:
            serializer_class = CustomVerifyJSONWebTokenSerializer
            token, user = serializer_class.validate(serializer_class, request.data)

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
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serialzier_class = CustomRefreshJSONWebTokenSerializer
        token, user = serialzier_class.validate(serialzier_class, request.data)

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
                    send_verification_email(request, user, email,
                                            link='http://127.0.0.1:9080/accounts/activate')

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
                send_verification_email(request, user, email,
                                        link='http://127.0.0.1:9080/accounts/activate')

                return Response(data={"detail": _("Verification Email Sent.")}, status=status.HTTP_200_OK)

            else:
                return Response(data={"detail": _("Email is not found.")}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            user = User.objects.get(user_id=request.data.get('user_id'))
            if user and user.is_active is False:
                if user.email is not None:
                    send_verification_email(request, user, user.email,
                                            link='http://127.0.0.1:9080/accounts/activate')

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
        {"isSuccess": Boolean}
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def post(self, request, uidb64, token):
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(user_pk=uid)

        if user is not None and default_token_generator.check_token(user=user, token=token):
            user.is_active = True
            user.save()

            return Response(data={"isSuccess": True}, status=status.HTTP_200_OK)

        elif default_token_generator.check_token(user=user, token=token) is False:
            send_verification_email(request, user=user, email=user.email,
                                    link='http://127.0.0.1:9080/accounts/activate')

            return Response(data={"detail": _("Account authentication has expired. New Verification Email Sent.")},
                            status=status.HTTP_403_FORBIDDEN)

        else:
            return Response(data={"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)


class CheckUser(APIView):
    """
    Confirming that the user is himself by sending confirmation email.
    Can use it when user authorization is needed before change password.

    PW change suggestion : The process of changing password is recommended to be implemented
    as a process of identifying user themselves via email and initializing password into new password
    rather than the process of writing old password and writing new password.

    This is because accounts created with social accounts have random passwords,
    and even the owner of social accounts does not know the password of accounts stored in the DB.
    """
    authentication_classes = (authentication.CustomJWTAuthentication,)

    def post(self, request, user_id):
        user = User.objects.get(user_id=user_id)
        email = user.get_user_email()

        send_verification_email(request, user=user, email=email,
                                link='http://127.0.0.1:9080/accounts/checkuser/redirect')

        return Response(data={"detail": _("Verification Email Sent.")}, status=status.HTTP_200_OK)


class VerifyUser(APIView):
    """
    response:
        {"isSuccess": Boolean}
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, uidb64, token):
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(user_pk=uid)
        request.user = user
        if user is not None and default_token_generator.check_token(user=user, token=token):

            return Response(data={"isSuccess": True}, status=status.HTTP_200_OK)

        elif default_token_generator.check_token(user=user, token=token) is False:
            send_verification_email(request, user=user, email=user.email,
                                    link='http://127.0.0.1:9080/accounts/checkuser/redirect')

            return Response(data={"detail": _("Account authentication has expired. New Verification Email Sent.")},
                            status=status.HTTP_403_FORBIDDEN)

        else:
            return Response(data={"isSuccess": False}, status=status.HTTP_400_BAD_REQUEST)
