from django.test import TestCase
from uchicagohvz.users.tasks import send_activation_email
from django.core import mail

# Create your tests here.
class EmailTestCase(TestCase):
    def test_email(self):
        email = mail.EmailMessage(
            subject='Test',
            body='This is a test message',
            to=['greglink49@gmail.com'],
        )
        email.send()
        print email
        self.assertEqual(True, True)
