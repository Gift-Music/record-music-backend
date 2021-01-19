from django.test import TestCase
from django.core.mail import EmailMessage
from django.conf import settings


class MailTest(TestCase):

    def test_send_mail(self):
        email = EmailMessage('test', 'test message', to=['sdsdertyjsy@gmail.com'])
        complete = email.send()
        self.assertEquals(complete, 1)

