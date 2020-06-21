#!/usr/bin/python
"""The primary router for the data service for API"""
from re import findall

import requests
from flask import Flask, request, Response
from flask_cors import CORS
from werkzeug.datastructures import Headers


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
FILE_SERVER_LOCATION = '../deps/'
# Setup Flask app.
app = Flask(__name__, static_folder=FILE_SERVER_LOCATION)
app.debug = True
CORS(app, supports_credentials=True)


@app.route("/jbrowse_query/<path:path>", methods=['GET', 'POST'])
def streamed_proxy(path):
    """
    :param shock_id:
    :return:
    This method is used to support visualization of Variation data
    in Jbrowse. Jbrowse sends request to this method and this service
    returns required amount of bytes.
    :param shock_id:
    :return: bytes of data from shock id requested by Jbrowse
    # token should be sent as part of cookie with kbase_session
    # header={'Cookie': 'kbase_session=XXXXXXXXXXXXXXXXXX'}
    # where XXXXXXXXXXXXXX is the token
    """

    # TODO: This should come from the jbrowse itself.
    # TODO: So instead of putting it as /shock/shock_id
    # TODO: put server/shock/shock_id the whole path of the node

    node_url = get_node_url(path)

    # print request.headers
    token_resp = get_token(request.headers)
    # print ("token_resp is" + token_resp)
    if token_resp.startswith("Error"):
        return token_resp
    else:
        token = token_resp

    # Get total size of shock node
    auth_headers = {'Authorization': ('OAuth ' + token) if token else None}
    resp = requests.get(node_url, headers=auth_headers, allow_redirects=True)
    rb = resp.json()
    if rb["error"] is not None:
        if rb["error"][0].startswith("Invalid authorization header"):
            message = "Error: Unauthorized token"
            print(message)
            return message
        else:
            message = "Error: uncaught error" + "\n".join(rb["error"])
            print(message)
            return message
    size = rb['data']['file']['size']
    print(size)

    headers = Headers()
    status = None
    # Handle byte range request properly
    if "Range" in request.headers:
        status = 206
        ranges = findall(r"\d+", request.headers["Range"])

        begin = int(ranges[0])
        if len(ranges) > 1:
            end = int(ranges[1])

            # Request from shock with required bytes for input shock node
            effective_node_url = node_url + '?download&seek=' + str(begin) + '&length=' + str(end - begin + 1)
            print(effective_node_url)
            r = requests.get(effective_node_url, headers=auth_headers, stream=True)
            # TODO: Handle cases where this byte request goes above a certain limit
            # TODO: Looks like jbrowse handles it based properly on chunk size but still need to be sure
            #  Figuring this requires some  digging of Jbrowse code
            # data = r.content
            # Add headers
            if end >= size:
                end = size - 1
            content_length = end - begin + 1
            content_range = "bytes " + str(begin) + "-" + str(end) + "/" + str(size)
            headers.add('Content-Length', str(content_length))
            headers.add('Content-Range', str(content_range))
            headers.add('Accept-Ranges', 'bytes')
            headers.add('Connection', 'keep-alive')
            headers.add('Cache-Control', 'public, max-age=43200')
            # Send response with headers
            response = Response(r.iter_content(chunk_size=10 * 1024), status=status, headers=headers)
            return response
    # Handle non-byte range request
    # Needed to support smaller fasta index
    else:
        # server is the shock node url for downloading the whole file
        effective_node_url = node_url + "?download_raw"
        print(effective_node_url)
        # Make request
        r = requests.get(effective_node_url, headers=auth_headers, stream=True)
        # Add headers and status
        # print ("Status is" + r.status.code)
        headers.add('Content-Length', r.headers['Content-Length'])
        headers.add('Accept-Ranges', 'bytes')
        # Create streamed response
        response = Response(r.iter_content(chunk_size=10 * 1024), status=status, headers=headers)
        return response


@app.route('/dataset/<path:path>')
def static_proxy(path):
    """
    This is used to support Jbrowse sessions.
    Each jbrowse session is a new directory that serves
    static javascript files
    :param path: path to the file on the system
    :return: content of the file
    """
    # print (path)
    # send_static_file will guess the correct MIME type
    print (request.headers)
    return app.send_static_file(path)


if __name__ == '__main__':
    app.run()
