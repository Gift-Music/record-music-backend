from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from .views import *
from django.core import mail

User = get_user_model()


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.userdata = {
            'userid': 'test',
            'username': 'kimtest',
            'email': 'test@testmail.com',
            'password': 'junhyeok'
        }
        save_user = User(userid=cls.userdata.get('userid'), username=cls.userdata.get('username'),
                         email=cls.userdata.get('email'), password=cls.userdata.get('password'))
        save_user.save()

    def test_models(self):

        user = User.objects.get(userid='test')

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

    def test_upload_musicmaps(self):
        pass


class ViewTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.userdata = {
            'userid': 'test',
            'username': 'kimtest',
            'email': 'test@testmail.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(userid=cls.userdata.get('userid'), username=cls.userdata.get('username'),
                     email=cls.userdata.get('email'), password=cls.userdata.get('password'))

        cls.userdata2 = {
            'userid': 'test2',
            'username': 'leetest',
            'email': 'test2@testmail.com',
            'password': 'junhyeok'
        }
        User.objects.create_user(userid=cls.userdata2.get('userid'), username=cls.userdata2.get('username'),
                                 email=cls.userdata2.get('email'), password=cls.userdata2.get('password'))

    def test_isTestUserInDB(self):

        self.assertEqual('test', User.objects.get(userid='test').userid)

    def test_register_and_login(self):

        register_data = {
            'userid': 'test3',
            'username': 'leetest',
            'email': 'test3@testmail.com',
            'password': 'junhyeok'
        }
        register_response = self.client.post('/accounts/register/', register_data)

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_data = {
            'email': 'test3@testmail.com',
            'password': 'junhyeok'
        }
        login_response = self.client.post('/accounts/login/', login_data)

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_search(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(userid='test'))

        search_query = {
            'userid': 'test'
        }
        response = client.get('/accounts/search/test/', search_query)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('userid'), User.objects.get(userid='test').userid)

    def test_explore(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(userid='test'))
        response = client.get('/accounts/explore/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[1].get('userid'), User.objects.get(userid='test').userid)

    def test_profile(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(userid='test'))
        response = client.get('/accounts/test/profile/')

        self.assertEqual('test', response.data.get('userid'))
        self.assertEqual(None, response.data.get('profile_image'))
        self.assertEqual('kimtest', response.data.get('username'))
        self.assertEqual(0, response.data.get('followers_count'))
        self.assertEqual(0, response.data.get('following_count'))

    def test_follow_and_unfollow(self):
        client = APIClient()
        client.force_authenticate(user=User.objects.get(userid='test'))
        request = {
            'userid': 'test'
        }
        response = client.post('/accounts/test2/follow/', request)
        user = User.objects.get(userid='test')
        user2 = User.objects.get(userid='test2')

        self.assertEqual(True, response.data.get('isSuccess'))
        self.assertEqual(1, user.following_count)
        self.assertEqual(1, user2.followers_count)

        response = client.put('/accounts/test2/unfollow/', request)

        self.assertEqual(True, response.data.get('isSuccess'))
        self.assertEqual(0, user.following_count)
        self.assertEqual(0, user2.followers_count)

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
