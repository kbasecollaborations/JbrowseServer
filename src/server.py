#!/usr/bin/python
"""The primary router for the data service for API"""

import json
import os
import re

import requests
import zipfile
from flask import Flask, request
from flask_cors import CORS

from src.Utils.WorkspaceClient import Workspace
from src.Utils.shock import Client as ShockClient


def get_node_url(path):
    return "https://" + path


def get_variation_file_service_url():
    '''
    get the most recent VariationFileServ url from the service wizard.
    sw_url: service wizard url
    '''
    # TODO Fix the following dev thing to beta or release or future
    json_obj = {
        "method": "ServiceWizard.get_service_status",
        "id": "",
        "params": [{"module_name": "VariationFileServ", "version": "dev"}]
    }
    kbase_endpoint = os.environ.get('KBASE_ENDPOINT')
    sw_url = kbase_endpoint + "/service_wizard"
    sw_resp = requests.post(url=sw_url, data=json.dumps(json_obj))
    vfs_resp = sw_resp.json()
    vfs_service_url = vfs_resp['result'][0]['url'].replace(":443", "")
    return vfs_service_url


def fix_tracklist(path):
    '''
    fix tracklist with upto date variation file service url
    '''

    with open(path) as f:
        data = json.load(f)
    # TODO: update vfs_url
    vfs_url = get_variation_file_service_url()
    print (vfs_url)
    for index, track in enumerate(data["tracks"]):
        for key in track:
            if "VariationFileServ" in track[key]:
                newUrl = re.sub(".*VariationFileServ/", "", track[key])
                data["tracks"][index][key] = vfs_url + "/" + newUrl

    with open(path, 'w') as f:
        json.dump(data, f)

    return (path)


def get_token(request_header):
    # for debugging headers coming from the request

    # print (request_header)
    try:
        cookie_rawdata = request_header['Cookie'].split(";")
        # print (cookie_rawdata)
    except Exception:
        message = "Error:Missing Cookie in header {'Cookie': 'kbase_session_backup=XXXXXXXXXX'}"
        print(message)
        return message

    cookie_dict = {}
    for c in cookie_rawdata:
        key, value = c.strip().split("=")
        cookie_dict[key] = value
    if 'kbase_session_backup' in cookie_dict:
        token = cookie_dict['kbase_session_backup']
        if len(token.strip()) == 0:
            message = "Error: empty token"
            print(message)
            return message
        else:
            return cookie_dict['kbase_session_backup']
    else:
        message = "Error: Missing kbase_session_backup in Cookie {'Cookie': 'kbase_session_backup=XXXXXXXXXX'}"
        print(message)
        return message


def get_jbrowse_from_obj(ref, token, KBASE_ENDPOINT):
    ws_url = KBASE_ENDPOINT + "/ws"
    ws = Workspace(url=ws_url, token=token)
    try:
        genomic_indexes = \
            ws.get_objects2({'objects': [{"ref": ref, 'included': ['/genomic_indexes']}]})['data'][0]['data'][
                'genomic_indexes']
    except:
        raise ValueError("Can not access object")
        return '{"Error": "Cannot access object"}'
    return genomic_indexes


# Set up server root path.
# TODO: COnfirm that the file server location matches with
# TODO: space that has enough space to host files
FILE_SERVER_LOCATION = '/kb/module/work'
# Setup Flask app.
app = Flask(__name__, static_folder=FILE_SERVER_LOCATION)
app.debug = True
CORS(app, supports_credentials=True)


@app.route('/jbrowse/<path:path>')
def static_proxy(path):
    """
    This is used to support Jbrowse sessions.
    Each jbrowse session is a new directory that serves
    static javascript files
    :param path: path to the file on the system
    :return: content of the file
    """
    print(path)
    # send_static_file will guess the correct MIME type

    KBASE_ENDPOINT = os.environ.get('KBASE_ENDPOINT')
    print("Authenticating")
    token = None
    # 1) Make sure request is authenticated and has kbase_session_backup in cookie
    token_resp = get_token(request.headers)
    if token_resp.startswith("Error"):
        return token_resp
    else:
        token = token_resp

    if token is None:
        return '{"error":"Unauthorized access"}'

    # TODO: Sanitize path properly
    # TODO: Add more checks
    # 2) Get workspace object ref check if things are cached

    p = path.split("/")
    ref = p[0] + "/" + p[1] + "/" + p[2]
    print("object reference is :" + ref)

    print("Getting workspace data")
    # Need to make sure the first time a user is accessing this
    # we get the workspace object so that shock nodes are properly shared

    # TODO: We are assuming the first call will always index.html which may or may not be the case
    # TODO: So put fix for the case where first call may be something like index.html
    # TODO: test for the presence of the directory as well.
    genomic_indexes = None
    if (p[3] == "index.html"):
        genomic_indexes = get_jbrowse_from_obj(ref, token, KBASE_ENDPOINT)

    dir = FILE_SERVER_LOCATION + "/" + ref
    tracklist_path = dir + "/data/trackList.json"
    if os.path.exists(tracklist_path):
        print("Serving cached track information")
        return app.send_static_file(path)
    else:
        print("Building Jbrowse path")
        genomic_indexes = get_jbrowse_from_obj(ref, token, KBASE_ENDPOINT)
        if genomic_indexes is None:
            return '{"error":"Missing genomic indexex"}'

    print("Getting jbrowse.zip")
    # 3) Get shock node for the jbrowse instance
    shock_node = None

    for g in genomic_indexes:
        print(g)
        f = g.get('file_name')
        if f == 'jbrowse.zip':
            shock_node = g.get('id')
    if shock_node is None:
        return '{"Error": "cannot find Jbrowse data node"}'

    shock_url = KBASE_ENDPOINT + "/shock-api"
    shock = ShockClient(shock_url, token)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    filename = os.path.join(dir, "jbrowse.zip")
    pathx = os.path.join("/kb/module/work", filename)
    data_zip_file = shock.download_to_path(shock_node, pathx)

    with zipfile.ZipFile(data_zip_file, 'r') as zip_ref:
        zip_ref.extractall(dir)

    updated_tracklist = fix_tracklist(tracklist_path)
    print("Tracklist path is :" + updated_tracklist)

    print("Final list of files")
    print(os.listdir(dir))
    return app.send_static_file(path)


if __name__ == '__main__':
    app.run()
