import os
import unittest
import json

import requests
from dotenv import load_dotenv

load_dotenv('.env')

token = os.environ['token']
if token is None:
    raise RuntimeError("Copy .env.example to .env in root directory and fill token value token=XXXXXX ")

KBASE_ENDPOINT = os.environ['KBASE_ENDPOINT']
if KBASE_ENDPOINT is None:
    raise RuntimeError(
        "Copy .env.example to .env in root directory and fill KBASE_ENDPOINT=https://ci.kbase.us/services or as appropriate ")

print ("kbase end point is :" + KBASE_ENDPOINT)
base_url = 'http://web:5000'
cookie_info = "kbase_session=" + token


def make_request(url, headers):
    """Helper to make a JSON RPC request with the given workspace ref."""
    print(url)
    print(headers)
    resp = requests.get(url, headers=headers)
    return json.loads(resp.text)


class TestApi(unittest.TestCase):

    def test_complete_download(self):
        '''
        Test complete authenticated download of a small file
        '''

        # Make sure you populate .env file properly
        if (KBASE_ENDPOINT.startswith("https://appdev")):
            variation_obj_ref = "47506/18/1"
            url = base_url + "/jbrowse/" + variation_obj_ref + "/data/trackList.json"
            headers = {'Cookie': cookie_info}
            resp = make_request(url, headers)
            case1 =  "appdev.kbase.us" in resp['tracks'][0]['urlTemplate']
            self.assertTrue(case1)


        # Make sure you populate .env file properly
        if (KBASE_ENDPOINT.startswith("https://ci.")):
            variation_obj_ref = "51623/4/1"
            url = base_url + "/jbrowse/" + variation_obj_ref + "/data/trackList.json"
            headers = {'Cookie': cookie_info}
            resp = make_request(url, headers)
            case1 = "ci.kbase.us" in resp['tracks'][0]['urlTemplate']
            self.assertTrue(case1)
