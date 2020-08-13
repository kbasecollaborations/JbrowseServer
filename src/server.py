#!/usr/bin/python
"""The primary router for the data service for API"""
from re import findall

import requests
from flask import Flask, request, Response
from flask_cors import CORS
from werkzeug.datastructures import Headers
#from kbase_workspace_client import WorkspaceClient



import os
from src.Utils.shock import Client as ShockClient
from src.Utils.WorkspaceClient import Workspace


import zipfile

def get_node_url(path):
    return "https://" + path


def get_token(request_header):
    # for debugging headers coming from the request

    # print (request_header)
    try:
        cookie_rawdata = request_header['Cookie'].split(";")
        # print (cookie_rawdata)
    except Exception:
        message = "Error:Missing Cookie in header {'Cookie': 'kbase_session=XXXXXXXXXX'}"
        print(message)
        return message

    cookie_dict = {}
    for c in cookie_rawdata:
        key, value = c.strip().split("=")
        cookie_dict[key] = value
    if 'kbase_session' in cookie_dict:
        token = cookie_dict['kbase_session']
        if len(token.strip()) == 0:
            message = "Error: empty token"
            print(message)
            return message
        else:
            return cookie_dict['kbase_session']
    else:
        message = "Error: Missing kbase_session in Cookie {'Cookie': 'kbase_session=XXXXXXXXXX'}"
        print(message)
        return message


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
    print (path)
    # send_static_file will guess the correct MIME type

    print ("Authenticating")
    token = None
    # 1) Make sure request is authenticated and has kbase_session in cookie
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
    print (ref)

    print ("Getting workspace data")
    # Need to make sure the first time a user is accessing this
    # we get the workspace object so that shock nodes are properly shared 

    #TODO: We are assuming the first call will always index.html which may or may not be the case
    #TODO: So put fix for the case where first call may be something like index.html
    #TODO: test for the presence of the directory as well.
    if (p[3]=="index.html"):
        kbase_endpoint = os.environ.get('KBASE_ENDPOINT', 'https://ci.kbase.us/services')
        ws_url = kbase_endpoint + "/ws"
        ws = Workspace(ws_url, token)
        try:
            genomic_indexes = ws.get_objects2( {'objects':[{"ref": ref,'included': ['/genomic_indexes']}]})['data'][0]['data']
        except:
            raise ValueError ("Can not access object")
            return '{"Error": "Cannot access object"}'

    dir = FILE_SERVER_LOCATION + "/" + ref
    tracklist_path = dir + "/data/trackList.json"
    if os.path.exists(tracklist_path):
        print ("Serving cached track information")
        return app.send_static_file(path)


    print ("Getting jbrowse.zip")
    # 3) Get shock node for the jbrowse instance
    shock_node = None
    for g in genomic_indexes:
        f = g.get('file_name')
        if f=='jbrowse.zip':
            shock_node = g.get('id')
    if shock_node is None:
        return '{"Error": "cannot find Jbrowse data node"}'

    shock_url = kbase_endpoint + "/shock-api"
    shock = ShockClient(shock_url, token)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    filename = os.path.join(dir, "jbrowse.zip")
    pathx = os.path.join("/kb/module/work", filename)
    data_zip_file = shock.download_to_path(shock_node, pathx)

    with zipfile.ZipFile(data_zip_file, 'r') as zip_ref:
        zip_ref.extractall(dir)

    print ("Final list of files")
    print (os.listdir(dir))
    return app.send_static_file(path)


if __name__ == '__main__':
    app.run()
