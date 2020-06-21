"""
Simple integration tests on the API itself.

We make actual ajax requests to the running docker container.
"""
import os
import unittest

import requests
from dotenv import load_dotenv

load_dotenv('.env')

token = os.environ['token']
if token is None:
    raise RuntimeError("Copy .env.example to .env in root directory and fill token value token=XXXXXX ")
# The URL of the running server from within the docker container
base_url = 'http://web:5000'
cookie_info_good = "kbase_session=" + token
cookie_info_bad = "abc=def"
cookie_wrong_token = "kbase_session=" + "wrong_token"
cookie_empty_token = "kbase_session=" + ""


def make_request(url, headers):
    """Helper to make a JSON RPC request with the given workspace ref."""
    print(url)
    print(headers)
    resp = requests.post(url, headers=headers)
    return resp.text


class TestApi(unittest.TestCase):

    # @unittest.skip('x')
    def test_complete_download(self):
        """Test complete authenticated download of a small file"""
        print("running test: test_complete_download ")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Cookie': cookie_info_good}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp.startswith("Chr1") and
                        resp.endswith("80\n"))

    # @unittest.skip('x')
    def test_partial_download(self):
        """Test partial download with headers in the range format"""
        print("running test: test_partial_download ")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Cookie': cookie_info_good, 'Range': 'bytes:6-10'}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp == "04276")

    # @unittest.skip('x')
    def test_missing_cookie(self):
        """Test missing cookie in headers"""
        print("running test: test_missing cookie ")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Range': 'bytes:6-10'}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp.startswith("Error:Missing Cookie in header"))

    # @unittest.skip('x')
    def test_missing_kbase_session(self):
        """Test missing kbase_session in cookie headers"""
        print("running test: test_missing_kbase_session")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Cookie': cookie_info_bad, 'Range': 'bytes:6-10'}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp.startswith("Error: Missing kbase_session in Cookie"))

    # @unittest.skip('x')
    def test_wrong_token(self):
        """Test wrong token"""
        print("running test: test_wrong_token")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Cookie': cookie_wrong_token, 'Range': 'bytes:6-10'}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp.startswith("Error: Unauthorized token"))

    # @unittest.skip('x')
    def test_empty_token(self):
        """Test empty token"""
        print("running test: test_empty_tokem")
        url = base_url + "/jbrowse_query/appdev.kbase.us/services/shock-api/node/ad4ebf34-49fa-41b0-ab4c-9358d46a352b"
        headers = {'Cookie': cookie_empty_token, 'Range': 'bytes:6-10'}
        resp = make_request(url, headers)
        # print (resp)
        self.assertTrue(resp.startswith("Error: empty token"))
