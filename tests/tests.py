import unittest

#
# Ensure the flask server is running before executing tests.
# You may need to manually remove leftover data from previous test runs using an external tool.
#

class SecurityTestCases(unittest.TestCase):

    def testSignupNoInput(self):
        import requests

        r = requests.post("http://127.0.0.1:5000/signup/", data={})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Account created", r.text)

    def testSignupEmptyInput(self):
        import requests

        data = {
            "email": "",
            "name": "",
            "password": "",
            "password_verification": "",
        }
        r = requests.post("http://127.0.0.1:5000/signup/", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Account created", r.text)

    def testSignupBadEmailInput(self):
        import requests

        data = {
            "email": "not_an_email_address",
            "name": "example",
            "password": "password",
            "password_verification": "password",
        }
        r = requests.post("http://127.0.0.1:5000/signup/", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Account created", r.text)


    def testSignupBadPasswordInput(self):
        import requests

        data = {
            "email": "testbadpassword@example.com",
            "name": "example",
            "password": "password",
            "password_verification": "different",
        }
        r = requests.post("http://127.0.0.1:5000/signup/", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Account created", r.text)


    def testSignupXSS(self):
        import requests

        data = {
            "email": "xss@evil.com",
            "name": "<span onload=\"alert(1)\">my_username</span>",
            "password": "password",
            "password_verification": "password",
        }
        r = requests.post("http://127.0.0.1:5000/signup/", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("<span onload=\"alert(1)\">", r.text)

