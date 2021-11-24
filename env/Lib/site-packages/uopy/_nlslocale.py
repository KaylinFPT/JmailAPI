# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from . import UOLocale
from ._funccodes import FuncCodes
from ._uniobject import UniObject
from ._unirpc import *
from ._uoerror import *


class NLSLocale(UniObject):

    def __init__(self, session=None):
        super().__init__(session)

    def set_server_locale_name(self, lc_category, lc_value):
        if isinstance(lc_category, UOLocale):
            raise UOError(ErrorCodes.UOE_EINVAL)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SETLOCALE)
            out_packet.write(1, lc_category.value)
            out_packet.write(2, self._session.encode(lc_value))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code != 0:
                raise UOError(code=resp_code)

    def get_server_locale_name(self, lc_category):

        if isinstance(lc_category, UOLocale):
            raise UOError(ErrorCodes.UOE_EINVAL)

        with self._lock:

            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_GETLOCALE)
            out_packet.write(1, lc_category.value)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                return self._session.decode(in_packet.read(1))
            else:
                raise UOError(resp_code)
