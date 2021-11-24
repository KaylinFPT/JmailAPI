# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._uoerror import UOError
from ._constants import MARKS_COUNT
from ._funccodes import FuncCodes
from ._uniobject import UniObject
from ._unirpc import *


class NLSMap(UniObject):
    def __init__(self, session=None):
        super().__init__(session)
        self._map_name = ""

    def get_server_map_name(self):
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_GETMAP)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._map_name = self._session.decode(in_packet.read(1))
                return self._map_name
            else:
                raise UOError(code=resp_code)

    def set_server_map_name(self, map_name):

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SETMAP)
            out_packet.write(1, self._session.encode(map_name))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._map_name = map_name
                marks = []
                for idx in range(MARKS_COUNT):
                    mark = in_packet.read(2 + idx)
                    marks.insert(0, mark)

                # hack, to workaround a server problem
                if marks[0] == 255 and marks[1] == 255:
                    for idx in range(MARKS_COUNT):
                        marks[idx] = 255 - idx
                    marks[idx - 1] = 0x80

                self._session.sync_marks(marks)

            else:
                raise UOError(code=resp_code)
