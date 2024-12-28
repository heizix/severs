import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_register(self):
        response = self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 201)

    def test_upload_avatar(self):
        with open('tests/test_avatar.jpg', 'rb') as f:
            response = self.client.post('/upload_avatar', data={
                'username': 'testuser',
                'file': f
            })
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
