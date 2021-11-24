# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

import threading

from ._errorcodes import ErrorCodes
from ._logger import get_logger
from ._uoerror import UOError

thread_data = threading.local()

_logger = get_logger(__name__)


class UniObject:
    def __init__(self, session):
        if not session:
            if getattr(thread_data, 'session', None) is None:
                raise UOError(code=ErrorCodes.UOE_USAGE_ERROR, message="No session is found.")
            self._session = thread_data.session
        else:
            self._session = session

        self._lock = threading.RLock()

    def _call_server(self, in_packet, out_packet, in_exec=False):
        with self._lock:
            try:
                self._session.rpc_call(in_packet, out_packet, in_exec)
                resp_code = in_packet.read(0)
            except UOError as e:
                self._session.check_rpc_error(e)
                raise
            except Exception as e:
                _logger.error(e)
                raise UOError(ErrorCodes.UOE_UNKNOWN_ERROR) from e

            return resp_code
