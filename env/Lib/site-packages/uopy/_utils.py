# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

import ctypes
import ipaddress
import locale
import socket
from ._config import config, HOST, USER, PASSWORD, ACCOUNT, ENCODING
from ._errorcodes import ErrorCodes
from ._logger import get_logger
from ._uoerror import UOError

_logger = get_logger(__name__)


def mangle(bytes_array, version):
    encrypted_bytes_array = map(lambda x: x ^ version, bytes_array)
    return bytes(encrypted_bytes_array)


def get_host_info():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    int_ip = int(ipaddress.IPv4Address(ip))
    return ctypes.c_int(int_ip).value, hostname


def is_cp_supported(server_id):
    if server_id is not None and \
            (server_id.startswith(b'udapi') or server_id.startswith(b'uvapi')):
        return True
    else:
        return False


def build_connect_config(args):
    if not (USER in args and PASSWORD in args):
        raise UOError(code=ErrorCodes.UOE_USAGE_ERROR, message="Missing user login information")

    tmp_config = config.connection
    tmp_config.update({k: v for k, v in args.items() if k in tmp_config})
    tmp_config[USER] = args[USER]
    tmp_config[PASSWORD] = args[PASSWORD]

    encoding = tmp_config[ENCODING].strip()
    try:
        "".encode(encoding)
    except LookupError as e:
        _logger.warning("Unsupported encoding setting, system default will be used:" + str(e))
        tmp_config[ENCODING] = locale.getpreferredencoding()

    return tmp_config


def build_pooling_config(args):
    tmp_config = config.pooling
    tmp_config.update({k: v for k, v in args.items() if k in tmp_config})
    return tmp_config


def make_pool_key(connect_config):
    return connect_config[HOST] + connect_config[USER] + connect_config[
        PASSWORD] + connect_config[ACCOUNT]

