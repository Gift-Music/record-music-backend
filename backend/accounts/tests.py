from collections import OrderedDict
from datetime import date

from django.utils.http import base36_to_int
from rest_framework.test import APITestCase, APIClient

from .authentication import *
from .views import *
from django.core import mail
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator

from .models import *
from django.test import TestCase

User = get_user_model()


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@testmail.com',
            'password': 'junhyeok'
        }
        User.objects.create(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                            email=cls.userdata.get('email'), password=cls.userdata.get('password')).save()

        cls.userdata2 = {
            'user_id': 'test2',
            'username': 'leetest',
            'email': 'test2@testmail.com',
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

        user_with_email = User.objects.get(email='test@testmail.com')

        self.assertEqual('test', user_with_email.get_user_id())
        self.assertEqual(user, user_with_email)
        self.assertEqual('test@testmail.com', user.get_user_email())
        self.assertEqual(False, user.is_active is False)

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
            'email': 'test3@testmail.com',
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
                                     ('email', 'test@testmail.com'), ('followers_count', 1), ('following_count', 2)])

        self.assertEqual([expect_result], serializer.data)

    def test_upload_musicmaps(self):
        pass


class ViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'user_id': 'test',
            'username': 'kimtest',
            'email': 'test@testmail.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata.get('user_id'), username=cls.userdata.get('username'),
                                 email=cls.userdata.get('email'), password=cls.userdata.get('password'))

        cls.userdata2 = {
            'user_id': 'test2',
            'username': 'leetest',
            'email': 'test2@testmail.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(user_id=cls.userdata2.get('user_id'), username=cls.userdata2.get('username'),
                                 email=cls.userdata2.get('email'), password=cls.userdata2.get('password'))

    def test_isTestUserInDB(self):
        self.assertEqual('test', User.objects.get(user_id='test').user_id)

    def test_change_isActive(self):
        user = User.objects.get(user_id='test')
        user.is_active = False
        self.assertEqual(False, user.is_active)
        user.is_active = True
        self.assertEqual(True, user.is_active)

    def test_register_and_login(self):
        register_data = {
            'user_id': 'test3',
            'username': 'leetest',
            'email': 'test3@testmail.com',
            'password': 'junhyeok'
        }
        register_response = self.client.post('/accounts/register/', register_data)

        self.assertEqual({'detail': 'Verification Email Sent.'}, register_response.data)
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_data = {
            'email': 'test3@testmail.com',
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
                                 email='test3@testmail.com', password='junhyeok')

        client.post('/accounts/test2/follow/', None)
        client.post('/accounts/test3/follow/', None)

        response = client.get('/accounts/test/following/')
        user = User.objects.get(user_id='test')

        expect_result_1, expect_result_2 = \
            OrderedDict([('profile_image', None), ('user_id', 'test2'), ('username', 'leetest'),
                         ('email', 'test2@testmail.com'), ('followers_count', 1), ('following_count', 0)]), \
            OrderedDict([('profile_image', None), ('user_id', 'test3'), ('username', 'ParkTest'),
                         ('email', 'test3@testmail.com'), ('followers_count', 1), ('following_count', 0)])

        self.assertEqual([expect_result_1, expect_result_2], response.data)
        self.assertEqual(2, Follow.objects.all().count())
        self.assertEqual(2, user.following_count)

        client.put('/accounts/test3/unfollow/', None)

        response = client.get('/accounts/test/following/')
        expect_result = OrderedDict([('profile_image', None), ('user_id', 'test2'), ('username', 'leetest'),
                                     ('email', 'test2@testmail.com'), ('followers_count', 1), ('following_count', 0)])

        self.assertEqual([expect_result], response.data)
        self.assertEqual(1, Follow.objects.all().count())
        self.assertEqual(1, user.following_count)

    def test_send_email(self):
        mail.send_mail('Subject here',
                       'Here is the message.',
                       'from@example.com',
                       ['to@example.com'],
                       fail_silently=False)

        assert len(mail.outbox) == 1, "Inbox is not empty."
        assert mail.outbox[0].subject == 'Subject here'
        assert mail.outbox[0].body == 'Here is the message.'
        assert mail.outbox[0].from_email == 'from@example.com'
        assert mail.outbox[0].to == ['to@example.com']

    def test_should_make_uidb64_and_token(self):
        user = User.objects.get(user_id='test')
        uidb64 = urlsafe_base64_encode(force_bytes(user.user_pk))
        self.assertIsNotNone(uidb64)

        token = default_token_generator.make_token(user)
        self.assertIsNotNone(token)

    def test_check_current_domain(self):
        from django.test.client import RequestFactory
        rf = RequestFactory()
        rf.ALLOWED_HOSTS = ['127.0.0.1']
        rf.defaults['SERVER_NAME'] = '127.0.0.1'
        get_request = rf.get('/hello/')

        self.assertEqual('http://127.0.0.1', get_request._current_scheme_host)

    def test_send_verification_email(self):
        user = User.objects.get(user_id='test')
        request = {
            'user_id': 'test3',
            'username': 'leetest',
            'email': 'test3@testmail.com',
            'password': 'junhyeok'
        }
        uidb64 = urlsafe_base64_encode(force_bytes(user.user_pk))
        token = default_token_generator.make_token(user=user)  # One-time token for account authentication

        def message(domain, uidb64, token, link):
            activation_link = f"{link}/{uidb64}/{token}"
            return f"아래 링크를 클릭하면 회원 인증이 완료됩니다.\n\n" \
                   f"회원 인증 완료 링크 : {activation_link}\n\n감사합니다."

            # should change localhost domain to {domain} after register record-music domain
            # return f"아래 링크를 클릭하면 회원 인증이 완료됩니다.\n\n" \
            #                    f"회원 인증 완료 링크 : http://{domain}/accounts/register/activate/{uidb64}/{token}\n\n 감사합니다."

        self.assertEqual(f"아래 링크를 클릭하면 회원 인증이 완료됩니다."
                         f"\n\n회원 인증 완료 링크 : http://127.0.0.1:9080/accounts/register/activate/{uidb64}/{token}\n\n감사합니다."
                         , message(None, uidb64, token, 'http://127.0.0.1:9080/accounts/register/activate'))
        self.assertEqual(None, send_verification_email(request, user, user.email,
                                                       'http://127.0.0.1:9080/accounts/register/activate'))

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

        y, m, d = 2021, default_token_generator._today().month, default_token_generator._today().day + 3
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

    def test_should_update_user_profile(self):
        client = APIClient()
        user = User.objects.get(user_id='test')
        client.force_authenticate(user=user)

        data_email_change = {
            'email': 'junny@test.com'
        }
        response = client.put('/accounts/test/profile/', data_email_change)

        self.assertEqual('junny@test.com', response.data.get('user').get('email'))

        data_username_change = {
            'username': 'Lee Hyeok-Jun'
        }
        client.put('/accounts/test/profile/', data_username_change)
        response = client.get('/accounts/test/profile/')

        self.assertEqual('Lee Hyeok-Jun', response.data.get('username'))

        data_multiple_change = {
            'email': 'junny@test.com',
            'username': 'Lee Hyeok-Jun'
        }
        client.put('/accounts/test/profile/', data_multiple_change)
        response = client.get('/accounts/test/profile/')

        self.assertEqual('junny@test.com', response.data.get('email'))
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

    def test_check_user_and_token_over_exp_limit_day(self):
        user = User.objects.get(user_id='test')
        uidb64 = urlsafe_base64_encode(force_bytes(user.user_pk))
        token = default_token_generator.make_token(user=user)

        response = self.client.get(f'/accounts/checkuser/redirect/{uidb64}/{token}')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        class DefTokenGen(PasswordResetTokenGenerator):

            def _today(self):
                return date.today() + timedelta(days=10)

        token_generator = DefTokenGen()

        self.assertFalse(token_generator.check_token(user, token))
