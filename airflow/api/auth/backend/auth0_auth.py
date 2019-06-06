# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import jwt
import json
import boto3
import os

from airflow import configuration as conf
from six.moves.urllib.request import urlopen
from base64 import b64decode
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import DecodeError
from functools import wraps

from flask import Response
from flask import make_response
from flask import request
from airflow.utils.log.logging_mixin import LoggingMixin


SECRET = None
JWKS_URL = None

log = LoggingMixin().log
client_auth = None


def init_app(app):
    global KMS_ENCRYPTED_SECRET
    KMS_ENCRYPTED_SECRET = get_config_param('client_secret')
    global JWKS_URL
    JWKS_URL = "https://" + get_config_param('domain') + "/.well-known/jwks.json"


def get_config_param(param):
    return str(conf.get('auth0_rest_api', param))


def jwt_decode(jwt_token, key, options, algorithm):
    try:
        decoded = jwt.decode(jwt_token, key, options=options, algorithms=algorithm)
        return True
    except:
        log.warn("JWT token error")
        return False


def _unauthorized():
    """
    Indicate that authorization is required
    :return:
    """
    return Response("Unauthorized", 401, {"WWW-Authenticate": "Negotiate"})


def _forbidden():
    return Response("Forbidden", 403)


def requires_authentication(function):
    """Determines if the Access Token is valid
    """
    @wraps(function)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth:
            return _unauthorized()

        parts = auth.split()

        if parts[0].lower() != "bearer":
            return _unauthorized()
        elif len(parts) != 2:
            return _unauthorized()

        jwt_token = parts[1]
        unverified_header = None
        # Check that the JWT is well formed and extract the algorithm type from the header
        try:
            unverified_header = jwt.get_unverified_header(jwt_token)
        except DecodeError:
            raise Exception("JWT is NOT well formed.")

        # Get the type of algorithm used to encrypt the token
        algorithm = str(unverified_header["alg"])

        options = {
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_nbf': False,
                    'verify_aud': False,
                    'require_exp': True,
                    'require_iat': True,
                    'require_nbf': False
                    }

        if "HS" in algorithm:
            kms_client = boto3.client('kms', os.environ['AWS_DEFAULT_REGION'])
            secret = kms_client.decrypt(CiphertextBlob=b64decode(KMS_ENCRYPTED_SECRET))['Plaintext']
            jwt_decode(jwt_token, secret, options, algorithm)
        elif "RS" in algorithm:
            jsonurl = urlopen(JWKS_URL)
            jwks = json.loads(jsonurl.read())

            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    key_json = key
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key_json))

            if not jwt_decode(jwt_token, public_key, options, algorithm):
                return _unauthorized()
        else:
            log.warn("Unrecognised encryption algorithm used")
            return _unauthorized()

        response = function(*args, **kwargs)
        response = make_response(response)

        return response

    return decorated
