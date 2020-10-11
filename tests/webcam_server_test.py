# Webcam Server tests
import auth
import os
import unittest


class TestServer(unittest.TestCase):
    secret: str = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print('=' * 80)
        print('Test case: ' + cls.__name__)
        print('Setup test case...')
        cls.secret = os.urandom(16).decode(errors="ignore")

    @classmethod
    def tearDownClass(cls):
        print('-' * 80)
        print('Cleanup test case...')
        print('=' * 80)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        print('-' * 80)

    def tearDown(self):
        super().tearDown()

    def test_encode_auth_token(self):
        token = auth.encode_auth_token(TestServer.secret, 'user1')
        self.assertTrue(isinstance(token, bytes))

    def test_decode_auth_token(self):
        token = auth.encode_auth_token(TestServer.secret, 'user1')
        self.assertTrue(isinstance(token, bytes), 'Wrong result')
        result:str = auth.decode_auth_token(TestServer.secret, token)
        self.assertEqual('user1', result, 'Wrong user')


if __name__ == '__main__':
    unittest.main()