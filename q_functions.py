__Author__ = "Vincent Lamy"
__version__ = "2021.1015"

import json
import logging
from qumulo.rest_client import RestClient
import sys, getopt


def convert_quota_size(quota_size, logging):
    unit = quota_size[-1]
    quota_in_bytes = ''
    if unit == 'M':
        quota = int(quota_size[:-1])
        quota_in_bytes = quota * 1024 * 1024
    elif unit == 'G':
        quota = int(quota_size[:-1])
        quota_in_bytes = quota * 1024 * 1024 * 1024
    elif unit == 'T':
        quota = int(quota_size[:-1])
        quota_in_bytes = quota * 1024 * 1024 * 1024 * 1024
    elif unit == "P":
        quota = int(quota_size[:-1])
        quota_in_bytes = quota * 1024 * 1024 * 1024 * 1024
    logging.info('convert_quota_size,Quota {} has been converted to {} bytes'.format(quota_size,quota_in_bytes))
    print('Quota {} has been converted to {} bytes'.format(quota_size,quota_in_bytes))
    return quota_in_bytes


def gen_json_acl(username,homedir_owner):
    json_template = {
        "control": [
            "PRESENT"
        ],
        "posix_special_permissions": [],
        "aces": [
            {
                "type": "ALLOWED",
                "flags": [
                    "OBJECT_INHERIT",
                    "CONTAINER_INHERIT"
                ],
                "trustee": {
                    "domain": "ACTIVE_DIRECTORY",
                    "auth_id": "",
                    "uid": "",
                    "gid": "",
                    "sid": "",
                    "name": ""
                },
                "rights": [
                "READ",
                "READ_EA",
                "READ_ATTR",
                "READ_ACL",
                "WRITE_EA",
                "WRITE_ATTR",
                "WRITE_GROUP",
                "DELETE",
                "EXECUTE",
                "MODIFY",
                "EXTEND",
                "ADD_FILE",
                "ADD_SUBDIR",
                "DELETE_CHILD",
                "SYNCHRONIZE"
                ]
            },
            {
                "type": "ALLOWED",
                "flags": [
                    "OBJECT_INHERIT",
                    "CONTAINER_INHERIT",
                    "INHERITED"
                ],
                "trustee": {
                    "domain": "ACTIVE_DIRECTORY",
                    "auth_id": "",
                    "uid": "",
                    "gid": "",
                    "sid": "",
                    "name": "q-admins"
                },
                "rights": [
                    "ACCESS_RIGHTS_ALL"
                ]
            }
        ]
    }
    json_dump = json.dumps(json_template)
    json_acl = json.loads(json_dump)
    json_acl['aces'][0]['trustee']['name'] = username
    json_acl['aces'][1]['trustee']['name'] = homedir_owner
    return json_acl

