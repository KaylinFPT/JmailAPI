# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._dynarray import DynArray
from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._uniobject import UniObject
from ._unirpc import UniRPCPacket
from ._uoerror import UOError

_logger = get_logger(__name__)


class Subroutine(UniObject):
    """Subroutine allows the application to call a cataloged BASIC subroutine on the server.

    Arguments are used to both pass in data to and get back data from the cataloged subroutine.

    Attributes:
        name (str): the name of the cataloged BASIC subroutine.
        num_args (int): the number of arguments defined on the cataloged subroutine.
        args (list): the argument list for the subroutine, an argument can be a str, a DynArray, a byte array.

    Examples:
        >>> sub = Subroutine("SAYHELLOTO", 1)
        >>> sub.args[0] = "David"
        >>> print(sub.args)
        ['David']
        >>> sub.call()
        >>> print(sub.args)
        ['Hello, David']

    """

    def __init__(self, name="", num_args=0, session=None):
        """Initialize a Subroutine object

        Args:
            name (str): the name of the cataloged BASIC subroutine.
            num_args (int) : the number of arguments defined on the cataloged subroutine.
            session (Session, optional): the Session object that the Subroutine object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        super().__init__(session)

        self.name = name
        self.num_args = int(num_args) if int(num_args) > 0 else 0
        self.args = ["" for i in range(num_args)]

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        cls_name = '.'.join([self.__module__, self.__class__.__qualname__])
        details = (self.name, self.num_args, self.args)
        return format_string.format('.'.join([Subroutine.__module__, Subroutine.__qualname__]), details, id(self))

    def call(self):
        """Run the catalogued subroutine using the args on the remote server."""

        _logger.debug("Enter", self.name, self.args)

        if self.name is None or len(str(self.name)) == 0:
            raise UOError(code=ErrorCodes.UOE_UNABLETOLOADSUB)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SUBCALL)
            out_packet.write(1, self.num_args)
            out_packet.write(2, self._session.encode(self.name))

            for i in range(3, self.num_args + 3):
                out_packet.write(i, self._session.encode(self.args[i - 3]))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            for i in range(1, self.num_args + 1):
                self.args[i - 1] = DynArray(in_packet.read(i), self._session)

        _logger.debug("Exit", self.name, self.args)
