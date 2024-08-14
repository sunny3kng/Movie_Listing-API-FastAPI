
import unittest
from fastapi.testclient import TestClient
from main import app

class TestUsers(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_sign_up(self):
        response = self.client.post("/sign-up", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 201)

if __name__ == "__main__":
    unittest.main()
