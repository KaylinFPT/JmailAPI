# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from collections import namedtuple
from enum import Enum

#
# UOPY Global definitions
#

# File type flag
DATA_FILE = 0
DICT_FILE = 1

# Lock Behaviors
LOCK_WAIT = 1
LOCK_RETAIN = 2
LOCK_EXCLUSIVE = 4
LOCK_SHARED = 8

# Predefined Service Names for UO servers
UV_SERVICE = "uvcs"
UD_SERVICE = "udcs"
D3_SERVICE = "d3cs"
DEFAULT_SERVICE = "defcs"


# @variable Definitions
class AtVar(Enum):
    LOG_NAME = 1
    PATH = 2
    USER_NO = 3
    WHO = 4
    TRANSACTION = 5
    DATA_PENDING = 6
    USER_RETURN_CODE = 7
    SYSTEM_RETURN_CODE = 8
    NULL_STR = 9
    SCHEMA = 10
    TRANSACTION_LEVEL = 11


# Command Statuses
EXEC_COMPLETE = 0
EXEC_REPLY = 1
EXEC_MORE_OUTPUT = 2


# Locale Categories
class UOLocale(Enum):
    LC_TIME = 1
    LC_NUMERIC = 2
    LC_MONETARY = 3
    LC_CTYPE = 4
    LC_COLLATE = 5


MARKS_NAMED_TUPLE = namedtuple('MARKS', ['IM', 'FM', 'VM', 'SM', 'TM', 'SQLNULL'])
DEFAULT_MARKS = MARKS_NAMED_TUPLE(*[b'\xff', b'\xfe', b'\xfd', b'\xfc', b'\xfb', b'\x80'])
MARKS_COUNT = len(DEFAULT_MARKS)
