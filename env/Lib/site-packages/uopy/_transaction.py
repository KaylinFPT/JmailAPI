# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._funccodes import FuncCodes
from ._logger import *
from ._uniobject import UniObject
from ._unirpc import *
from ._uoerror import UOError

_logger = get_logger(__name__)

_TRANS_START = 1
_TRANS_COMMIT = 2
_TRANS_ROLLBACK = 3


class Transaction(UniObject):
    def __init__(self, session=None):
        super().__init__(session)

    def begin(self):
        _logger.debug("Enter")
        self._server_transaction(_TRANS_START)
        _logger.debug("Exit")

    def commit(self):
        _logger.debug("Enter")
        self._server_transaction(_TRANS_COMMIT)
        _logger.debug("Exit")

    def rollback(self):
        _logger.debug("Enter")
        self._server_transaction(_TRANS_ROLLBACK)
        _logger.debug("Exit")

    def _server_transaction(self, tx_key):
        _logger.debug("Enter key = {}".format(tx_key))

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_TRANSACTION)
            out_packet.write(1, tx_key)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")
