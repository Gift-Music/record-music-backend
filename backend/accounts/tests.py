import os
from collections import OrderedDict
from datetime import date

from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.crypto import get_random_string
from django.utils.http import base36_to_int
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase, APIClient

from .authentication import *
from .views import *
from django.core import mail
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator

from .models import *
from django.test import TestCase

User = get_user_model()


class ModelTest(TestCase):
    """
    Testing User model.
    """

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@example.com',
            'password': 'junhyeok'
        }
        User.objects.create(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                            email=cls.userdata.get('email'), password=cls.userdata.get('password')).save()

        cls.userdata2 = {
            'user_id': 'test2',
            'username': 'leetest',
            'email': 'test2@example.com',
            'password': 'junhyeok'
        }
        User.objects.create(user_id=cls.userdata2.get('user_id'), username=cls.userdata2.get('username'),
                            email=cls.userdata2.get('email'), password=cls.userdata2.get('password')).save()

    def test_setUpData_check(self):
        user = User.objects.get(user_id='test')

        self.assertEqual('test', user.get_user_id())
        self.assertEqual('kimtest', user.get_name())
        self.assertEqual(0, user.followers_count)
        self.assertEqual(0, user.following_count)
        self.assertEqual(False, user.is_staff)
        self.assertEqual(False, user.is_superuser)
        self.assertEqual(True, user.is_active)

        user_with_email = User.objects.get(email='test@example.com')

        self.assertEqual('test', user_with_email.get_user_id())
        self.assertEqual(user, user_with_email)
        self.assertEqual('test@example.com', user.get_user_email())
        self.assertEqual(False, user.is_active is False)
        self.assertEqual(None, user.is_deleted)
        self.assertEqual(None, user.verify_code)

    def test_should_create_user_in_model(self):
        another_user = {
            'user_id': 'test3',
            'username': 'parktest',
            'email': 'test3@example.com',
            'password': 'junhyeok',
        }
        User.objects.create_user(user_id=another_user.get('user_id'), username=another_user.get('username'),
                                 email=another_user.get('email'), password=another_user.get('password'))

        self.assertIsNotNone(User.objects.get(user_id='test3'))
        self.assertEqual('test3', User.objects.get(user_id='test3').user_id)
        self.assertEqual('parktest', User.objects.get(user_id='test3').username)
        self.assertEqual('test3@example.com', User.objects.get(user_id='test3').email)
        self.assertEqual(True, User.objects.get(user_id='test3').is_active)
        self.assertIsNone(User.objects.get(user_id='test3').is_deleted)

    def test_change_user_model_isActive(self):
        user = User.objects.get(user_id='test')
        user.is_active = False
        self.assertEqual(False, user.is_active)
        user.is_active = True
        self.assertEqual(True, user.is_active)

    def test_follow_model_test(self):
        user1 = User.objects.get(user_id='test')
        user2 = User.objects.get(user_id='test2')

        Follow.objects.create(from_user=user1, to_user=user2)

        self.assertEqual(1, Follow.objects.all().count())
        self.assertEqual('test', Follow.objects.first().from_user.user_id)
        self.assertEqual('test2', Follow.objects.first().to_user.user_id)

    def test_follow_and_unfollow_models(self):
        another_user = {
            'user_id': 'test3',
            'username': 'parktest',
            'email': 'test3@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=another_user.get('user_id'), username=another_user.get('username'),
                                 email=another_user.get('email'), password=another_user.get('password'))

        user1 = User.objects.get(user_id='test')
        user2 = User.objects.get(user_id='test2')
        user3 = User.objects.get(user_id='test3')

        user1.follows.add(user2)
        user1.follows.add(user3)
        user3.follows.add(user1)

        expect_response = User.objects.get(user_id='test2'), User.objects.get(user_id='test3')
        expect_response = list(expect_response)

        self.assertEqual(list(user1.follows.all()), expect_response)
        self.assertEqual(1, user1.following.values()[0].get('from_user_id'))

        followers = []
        for i in user2.followers.values():
            followers.append(User.objects.get(user_pk=i.get('from_user_id')))

        serializer = UserProfileSerializer(followers, many=True)

        expect_result = OrderedDict([('profile_image', None), ('user_id', 'test'), ('username', 'kimtest'),
                                     ('email', 'test@example.com'), ('followers_count', 1), ('following_count', 2),
                                     ('is_private', False)])

        self.assertEqual([expect_result], serializer.data)

    def test_profile_image_model(self):
        """
        location of media directory: ...\record-music-backend\backend\backend\media
        """
        user = User.objects.get(user_id='test')
        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage.jpg", image)
        image_model.creator = User.objects.get(user_id='test')
        image_model.save()

        self.assertIsNotNone(ProfileImage.objects.all())
        self.assertEqual('test', image_model.creator.user_id)
        self.assertIsNotNone(user.profileimage_set.all())
        self.assertEqual(1, ProfileImage.objects.first().id)

    def test_upload_musicmaps(self):
        pass


class BaseUserAccountViewTest(APITestCase):
    """
    Testing the implemented User API.

    Check the response data of User API.
    """

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                                 email=cls.userdata.get('email'), password=cls.userdata.get('password'))

        cls.userdata2 = {
            'user_id': 'test2',
            'username': 'leetest',
            'email': 'test2@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata2.get('user_id'), username=cls.userdata2.get('username'),
                                 email=cls.userdata2.get('email'), password=cls.userdata2.get('password'))

    def test_isTestUserInDB(self):
        self.assertEqual('test', User.objects.get(user_id='test').user_id)

    def test_register_and_login(self):
        register_data = {
            'user_id': 'test3',
            'username': 'leetest',
            'email': 'test3@example.com',
            'password': 'junhyeok'
        }
        register_response = self.client.post('/accounts/register/', register_data)

        self.assertEqual({'detail': 'Verification Email Sent.'}, register_response.data)
        self.assertEqual(register_response.status_code, status.HTTP_200_OK)

        login_data = {
            'email': 'test3@example.com',
            'password': 'junhyeok'
        }
        login_response = self.client.post('/accounts/login/', login_data)

        # Because this account has not verified yet.
        self.assertEqual(login_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))

        search_query = {
            'user_id': 'test'
        }
        response = client.get('/accounts/search/test/', search_query)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('user_id'), User.objects.get(user_id='test').user_id)

    def test_explore(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))
        response = client.get('/accounts/explore/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[1].get('user_id'), User.objects.get(user_id='test').user_id)

    def test_profile(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))
        response = client.get('/accounts/test/profile/')

        self.assertEqual('test', response.data.get('user_id'))
        self.assertEqual(None, response.data.get('profile_image'))
        self.assertEqual('kimtest', response.data.get('username'))
        self.assertEqual(0, response.data.get('followers_count'))
        self.assertEqual(0, response.data.get('following_count'))

    def test_follow_and_unfollow(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))
        request = {
            'user_id': 'test'
        }
        response = client.post('/accounts/test2/follow/', request)
        user = User.objects.get(user_id='test')
        user2 = User.objects.get(user_id='test2')

        self.assertEqual(True, response.data.get('isSuccess'))
        self.assertEqual(1, user.following_count)
        self.assertEqual(1, user2.followers_count)

        response = client.put('/accounts/test2/unfollow/', request)

        self.assertEqual(True, response.data.get('isSuccess'))
        self.assertEqual(0, user.following_count)
        self.assertEqual(0, user2.followers_count)

    def test_follow_and_following_users_and_unfollow(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))

        User.objects.create_user(user_id='test3', username='ParkTest',
                                 email='test3@example.com', password='junhyeok')

        client.post('/accounts/test2/follow/', None)
        client.post('/accounts/test3/follow/', None)

        response = client.get('/accounts/test/following/')
        user = User.objects.get(user_id='test')

        expect_result_1, expect_result_2 = \
            OrderedDict([('profile_image', None), ('user_id', 'test2'), ('username', 'leetest'),
                         ('email', 'test2@example.com'), ('followers_count', 1), ('following_count', 0),
                         ('is_private', False)]), \
            OrderedDict([('profile_image', None), ('user_id', 'test3'), ('username', 'ParkTest'),
                         ('email', 'test3@example.com'), ('followers_count', 1), ('following_count', 0),
                         ('is_private', False)])

        self.assertEqual([expect_result_1, expect_result_2], response.data)
        self.assertEqual(2, Follow.objects.all().count())
        self.assertEqual(2, user.following_count)

        client.put('/accounts/test3/unfollow/', None)

        response = client.get('/accounts/test/following/')
        expect_result = OrderedDict([('profile_image', None), ('user_id', 'test2'), ('username', 'leetest'),
                                     ('email', 'test2@example.com'), ('followers_count', 1), ('following_count', 0),
                                     ('is_private', False)])

        self.assertEqual([expect_result], response.data)
        self.assertEqual(1, Follow.objects.all().count())
        self.assertEqual(1, user.following_count)

    def test_verify_user_token(self):
        user = User.objects.get(user_id='test')
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))

        encode_payload = custom_jwt_payload_handler(user)
        access_token = jwt_encode_handler(encode_payload)
        data = {
            'token': access_token
        }
        response = client.post('/accounts/verify/', data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('test', response.data.get('user').get('user_id'))

    def test_refresh_user_token(self):
        user = User.objects.get(user_id='test')
        client = APIClient()
        client.force_authenticate(user=User.objects.get(user_id='test'))

        encode_payload = custom_jwt_payload_handler(user)
        access_token = jwt_encode_handler(encode_payload)
        data = {
            'token': access_token
        }
        response = client.post('/accounts/refresh/', data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('test', response.data.get('user').get('user_id'))

    def test_should_update_user_profile(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        data_email_change = {
            'email': 'junny@example.com'
        }
        response = client.put('/accounts/test/profile/', data_email_change)

        self.assertEqual('junny@example.com', response.data.get('user').get('email'))

        data_username_change = {
            'username': 'Lee Hyeok-Jun'
        }
        client.put('/accounts/test/profile/', data_username_change)
        response = client.get('/accounts/test/profile/')

        self.assertEqual('Lee Hyeok-Jun', response.data.get('username'))

        data_multiple_change = {
            'email': 'junny@example.com',
            'username': 'Lee Hyeok-Jun'
        }
        client.put('/accounts/test/profile/', data_multiple_change)
        response = client.get('/accounts/test/profile/')

        self.assertEqual('junny@example.com', response.data.get('email'))
        self.assertEqual('Lee Hyeok-Jun', response.data.get('username'))

        data_userid_change_same = {
            'user_id': 'test2'
        }
        response = client.put('/accounts/test/profile/', data_userid_change_same)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data_password_change = {
            'password': 'jhlee0210'
        }
        client.put('/accounts/test/profile/', data_password_change)
        user = User.objects.get(user_id='test')

        self.assertEqual(True, user.check_password('jhlee0210'))

    def test_user_deactivate(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        response = client.delete('/accounts/test/profile/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        user = User.objects.get(user_id='test')
        self.assertEqual(False, user.is_active)
        self.assertIsNotNone(user.is_deleted)

        response = client.delete('/accounts/test2/profile/')
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

        response = client.delete('/accounts/bnbong/profile/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_profile_image(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        response = client.get('/accounts/test/profile/profileimage/')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([], response.data)

        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage1.jpg", image)
        image_model.creator = User.objects.get(user_id='test')
        image_model.save()

        response = client.get('/accounts/test/profile/profileimage/')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNot([], response.data)

        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage2.jpg", image)
        image_model.creator = User.objects.get(user_id='test')
        image_model.save()

        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage3.jpg", image)
        image_model.creator = User.objects.get(user_id='test')
        image_model.save()

        request = {
            'file': None
        }

        response = client.post('/accounts/test/profile/profileimage/', request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'isSuccess': True}, response.data)

        request = {
            'id': 1
        }

        response = client.put('/accounts/test/profile/profileimage/', request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'isSuccess': True}, response.data)
        self.assertIsNotNone(user.profile_image)

        request = {
            'id': 1
        }

        response = client.delete('/accounts/test/profile/profileimage/', request)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, ProfileImage.objects.first().id)
        self.assertEqual(None, client.get('/accounts/test/profile/').data.get('profile_image'))


class SubUserAccountViewTest(TestCase):
    """
    Testing the functions implemented in the User API that work in an auxiliary manner.

    Check every single sub functions result that do not appear as response in user API,
    such as how long a user account has been disabled, a body of email, etc...
    """

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                                 email=cls.userdata.get('email'), password=cls.userdata.get('password'))

    def test_check_current_domain(self):
        from django.test.client import RequestFactory
        rf = RequestFactory()
        rf.ALLOWED_HOSTS = ['127.0.0.1']
        rf.defaults['SERVER_NAME'] = '127.0.0.1'
        get_request = rf.get('/hello/')

        self.assertEqual('http://127.0.0.1', get_request._current_scheme_host)

    def test_email_send(self):
        mail.send_mail('Subject here',
                       'Here is the message.',
                       'from@example.com',
                       ['to@example.com'],
                       fail_silently=False)

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual('Subject here', mail.outbox[0].subject)
        self.assertEqual('Here is the message.', mail.outbox[0].body)
        self.assertEqual('from@example.com', mail.outbox[0].from_email)
        self.assertEqual(['to@example.com'], mail.outbox[0].to)

    def test_send_verification_email(self):
        user = User.objects.get(user_id='test')
        request = {
            'user_id': 'test3',
            'username': 'leetest',
            'email': 'test3@example.com',
            'password': 'junhyeok'
        }
        code = get_random_string(length=5)

        def message(domain, code):
            return f"아래 계정 확인 코드를 입력하면 회원 인증이 완료됩니다.\n\n" \
                   f"계정 확인 코드 : {code}\n\n감사합니다."

        self.assertEqual(f"아래 계정 확인 코드를 입력하면 회원 인증이 완료됩니다.\n\n계정 확인 코드 : {code}\n\n감사합니다."
                         , message(None, code))

        result1, result2 = send_verification_email(request, code)

        self.assertEqual(5, len(result1))
        self.assertEqual(datetime.today().day, result2.day)

    def test_jwt_encoding_and_authentication_check(self):
        user = User.objects.get(user_id='test')
        encode_payload = custom_jwt_payload_handler(user)
        access_token = jwt_encode_handler(encode_payload)
        decode_payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=['HS256'])

        self.assertEqual('test', decode_payload.get('user_id'))

    def test_email_conf_timeout(self):
        user = User.objects.get(user_id='test')
        token = default_token_generator.make_token(user=user)
        ts_b36, _ = token.split("-")
        ts = base36_to_int(ts_b36)

        y, m, d = 2021, 1, 23
        not_over_day = date(y, m, d)

        self.assertEqual(False,
                         (default_token_generator._num_days(not_over_day) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS)

        y, m, d = default_token_generator._today().year, default_token_generator._today().month, \
                  default_token_generator._today().day + 3

        over_day = date(y, m, d)

        self.assertEqual(True,
                         (default_token_generator._num_days(over_day) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS)

    def test_social_login_access_token_slice(self):
        user_info = {"id": "my_id_here",
                     "first_name": "\uc900\ud601",
                     "last_name": "\uc774",
                     "picture": {"data": {"height": 50, "is_silhouette": False,
                                          "url": "profile_url_here",
                                          "width": 50}},
                     "email": "bnbong\u0040naver.com"}
        self.assertEqual("bnbong@naver.com", user_info['email'])
        self.assertEqual("준혁", user_info['first_name'])
        self.assertEqual("이", user_info['last_name'])

    def test_make_reverse_url_with_format_string(self):
        redirect_uri = reverse('accounts:google_login_redirect')
        uri = f'http://localhost:9080{redirect_uri}'

        self.assertEqual('http://localhost:9080/accounts/sociallogin/google/redirect/', uri)

    def test_serializer_valid_data(self):
        user = User.objects.get(user_id='test')
        request = {
            'is_active': False,
            'is_deleted': timezone.now(),
            'password': 'test123'
        }
        serializer = UserChangeProfileSerializer(user, data=request, partial=True)

        if serializer.is_valid():
            serializer.update(validated_data=serializer.validated_data, instance=user)

        self.assertEqual(True, serializer.is_valid())
        self.assertIsNotNone(serializer.validated_data)
        self.assertEqual('test123', serializer.validated_data.get('password'))

    def test_change_profile_image_and_upload(self):
        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage", image)
        user = User.objects.get(user_id='test')
        user.profile_image = image_model.file
        user.save()

        self.assertIsNotNone(user.profile_image)

    def test_upload_image_into_model(self):
        """
        Calls Permission denied [Error no. 13], and I cannot find solution of this.
        Tried to find a solution for three days, but I failed :(
        """

        # image_model = ProfileImage()

        """
        Error occurs in next line.
        """
        # image_model.file = SimpleUploadedFile(name='test_image.jpg', content=open(os.path.join(settings.MEDIA_ROOT), 'rb').read(),
        #                                       content_type='image/jpeg')
        # image_model.creator = User.objects.get(user_id='test')
        # image_model.save()
        #
        # self.assertIsNotNone(ProfileImage.objects.all())
        # self.assertEqual('test', image_model.creator.user_id)
        pass

    def test_check_profile_image(self):
        """
        If this test case is run as a single one, it will pass normally.
        I couldn't find a reason for this.
        """
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        image_model = ProfileImage()
        image = ImageFile(open(
            r'C:\WorkStationFiles\record-music-backend-main\record-music-backend\backend\backend\media\TEST-IMAGE.jpg',
            'rb'))
        image_model.file.save("testimage1.jpg", image)
        image_model.creator = User.objects.get(user_id='test')
        image_model.save()

        user.profile_image = ProfileImage.objects.get(id=1).file
        user.save()

        self.assertIsNotNone(user.profile_image)

        instance = ProfileImage.objects.get(id=1)
        self.assertEqual(True, instance.file == user.profile_image)

    def test_random_string_generator(self):
        """
        This string will be used in email account verification at register
        """
        token = get_random_string(length=5)

        self.assertEqual(5, len(token))

        time = datetime.now()
        nexttime = datetime.now() + timedelta(days=1)

        self.assertEqual(True, (nexttime - time).days == settings.PASSWORD_RESET_TIMEOUT_DAYS)

    def test_should_save_verification_data(self):
        user = User.objects.get(user_id='test')
        code = get_random_string(length=5)
        today = datetime.now()
        user.verify_code = f'{code},{today}'
        user.save()

        self.assertEqual(code, user.verify_code.split(',')[0])
        self.assertEqual(str(today), user.verify_code.split(',')[1])


class UserAccountFailTest(TestCase):
    """
    Checking the fail response(status which starts with 4__) of implemented User API.

    The name of the test case will start with 'cannot ~'.
    """

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                                 email=cls.userdata.get('email'), password=cls.userdata.get('password'))

        cls.userdata2 = {
            'user_id': 'test2',
            'username': 'leetest',
            'email': 'test2@example.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata2.get('user_id'), username=cls.userdata2.get('username'),
                                 email=cls.userdata2.get('email'), password=cls.userdata2.get('password'))

    def test_cannot_verify_unknown_user_token(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        payload = {
            'user_pk': 2,
            'user_id': 'test2',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "test2@example.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }

        other_user_token = jwt_encode_handler(payload)
        data = {
            'token': other_user_token
        }
        response = client.post('/accounts/verify/', data)

        # Cannot verify other user's token
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({'detail': 'User mismatch.'}, response.data)

        payload = {
            'user_pk': 10,
            'user_id': 'admin',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "admin@admin.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }

        fake_token = jwt_encode_handler(payload)
        data = {
            'token': fake_token
        }
        response = client.post('/accounts/verify/', data)

        # Cannot verify unknown user's token
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual([ErrorDetail(string='User Does not exist.', code='invalid')], response.data)

        payload = {
            'user_pk': 1,
            'user_id': 'test',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "test@example.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }
        user_token = jwt_encode_handler(payload)
        response = client.post('/accounts/verify/', user_token)

        # Invalid request input occurs.
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual({'detail': 'No user found, cannot verify token.'}, response.data)

    def test_cannot_refresh_unknown_user_token(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        payload = {
            'user_pk': 2,
            'user_id': 'test2',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "test2@example.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }

        other_user_token = jwt_encode_handler(payload)
        data = {
            'token': other_user_token
        }
        response = client.post('/accounts/refresh/', data)

        # Cannot refresh other user's token
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({'detail': 'User mismatch.'}, response.data)

        payload = {
            'user_pk': 10,
            'user_id': 'admin',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "admin@admin.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }

        fake_token = jwt_encode_handler(payload)
        data = {
            'token': fake_token
        }
        response = client.post('/accounts/refresh/', data)

        # Cannot refresh unknown user's token
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual([ErrorDetail(string='User Does not exist.', code='invalid')], response.data)

        payload = {
            'user_pk': 1,
            'user_id': 'test',
            'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
            "email": "test@example.com",
            "orig_iat": timegm(datetime.utcnow().utctimetuple())
        }
        user_token = jwt_encode_handler(payload)
        response = client.post('/accounts/refresh/', user_token)

        # Invalid request input occurs.
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual({'detail': 'No user found, cannot refresh token.'}, response.data)

    def test_cannot_follow_and_unfollow_myself(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        response = client.post('/accounts/test/follow/', )

        # Cannot follow myself.
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'isSuccess': False}, response.data)

        response = client.put('/accounts/test/unfollow/', )

        # Cannot unfollow myself.
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'isSuccess': False}, response.data)

    def test_cannot_follow_and_unfollow_deactivated_user(self):
        user = User.objects.get(user_id='test2')
        user.is_active = False
        user.is_deleted = timezone.now()
        user.save()

        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        response = client.post('/accounts/test2/follow/')

        # Cannot follow disabled user.
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'isSuccess': False}, response.data)

        response = client.put('/accounts/test2/unfollow/')

        # Cannot unfollow disabled user.
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'isSuccess': False}, response.data)

    def test_cannot_login_deactivated_user(self):
        another_user = {
            'user_id': 'test3',
            'username': 'parktest',
            'email': 'test3@example.com',
            'password': 'junhyeok',
        }
        User.objects.create_user(user_id=another_user.get('user_id'), username=another_user.get('username'),
                                 email=another_user.get('email'), password=another_user.get('password'))
        user = User.objects.get(user_id='test3')
        user.is_active = False
        user.is_deleted = timezone.now()
        user.save()

        login_data = {
            'email': user.email,
            'password': 'junhyeok'
        }
        response = self.client.post('/accounts/login/', login_data)

        # Cannot login disabled user.
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({'detail': 'This account is a withdrawn account.'}, response.data)

    def test_cannot_get_and_put_disabled_account_profile(self):
        another_user = {
            'user_id': 'test3',
            'username': 'parktest',
            'email': 'test3@example.com',
            'password': 'junhyeok',
        }
        User.objects.create_user(user_id=another_user.get('user_id'), username=another_user.get('username'),
                                 email=another_user.get('email'), password=another_user.get('password'))
        user = User.objects.get(user_id='test3')
        user.is_active = False
        user.is_deleted = timezone.now()
        user.save()

        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        response = client.get('/accounts/test3/profile/')

        # Cannot get disabled user profile.
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({"detail": "Cannot get disabled account."}, response.data)

        data = {
            'username': 'KimDisabled',
        }
        response = client.put('/accounts/test3/profile/', data)

        # Cannot change other user profile.
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"detail": "User mismatch."}, response.data)

        user = User.objects.get(user_id='test3')
        client.force_authenticate(user=user)

        data = {
            'username': 'KimDisabled',
        }
        response = client.put('/accounts/test3/profile/', data)

        # Cannot change disabled user profile.
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({"detail": "Cannot modify disabled account."}, response.data)

    def test_cannot_change_password_social_account(self):
        user = User.objects.get(user_id='test')
        user.is_social = True
        user.save()

        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        data = {
            'password': 'test1234'
        }
        response = client.put('/accounts/test/profile/', data)

        # Cannot change password social account.
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'Social account cannot change password.'}, response.data)
