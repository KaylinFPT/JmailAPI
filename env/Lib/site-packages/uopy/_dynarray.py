# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._mvdelimited import MvDelimited
from ._unirpc import UniRPCPacket
from ._uoerror import UOError

_logger = get_logger(__name__)


class DynArray(MvDelimited):
    """DynArray represents MV delimited data as nested lists and supports most common Python list methods.

    Specifically, a DynArray works with MV delimiters automatically and transparently. It can be used just like a Python
    list and should only be used in that manner. It is a best practice that applications do not use MV delimiters
    directly for internationalization reasons. Please remember that a DynArray can be passed directly to any UOPY method
    where MV delimited data is expected, such as file.write(), the application doesn't need to convert it first.

    Two convenience methods: make_list and make_nested_list are provided to convert a field itself into a list or nested
    list. They are useful if the original field is multivalued or multi-sub-valued, but may contain scalar values.
    Calling them first on a field will ensure that you can safely treat the field as a list or nested list.

    In addition, DynArray also supports two unique MV conversion functions: iconv and oconv. The details of these
    conversion functions are documented under each method. Because they call the remote server to do the conversion,
    it is strongly recommended that applications use File.read_named_fields() and File.write_named_fields() instead
    when reading data from or writing data to the server. They automatically perform the iconv and oconv on the
    specified fields on the server, and thus save a rpc call across the network.

    """

    def __init__(self, obj=None, session=None):
        """Initialize a DynArray object.

        Args:
            obj (any, optional): can be a Python list, a string, a byte object, or another DynArray.
            session (Session, optional): the Session object that the DynArray object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        super().__init__(obj, session)

    def __repr__(self):
        self._build_list()
        format_string = "<{} object {} at 0x{:016X}>"
        details = self._list
        return format_string.format('.'.join([DynArray.__module__, DynArray.__qualname__]), details, id(self))

    def __add__(self, other):
        if isinstance(other, DynArray):
            return DynArray(self._list + other._list)
        else:
            raise TypeError("can only concatenate DynArray to DynArray")

    def __iadd__(self, other):
        if isinstance(other, DynArray):
            self._list += other._list
            return self
        else:
            raise TypeError("can only concatenate DynArray to DynArray")

    def make_list(self, index):
        """Check if the list item is a list itself - if not, make it as such.

        Args:
            index (int): the index of the list item.

        Returns:
            None

        Examples:
            >>> d = uopy.DynArray([1, 2])
            >>> d.make_list(1)
            >>> d[1].append(3)
            >>> print(d.list)
            [1, [2, 3]]

        """
        self._build_list()
        if not isinstance(self._list[index], list):
            self._list[index] = [self._list[index]]

    def make_nested_list(self, index):
        """Check if the list item is a nested list itself - if not, make it as such.

        Args:
            index (int): the index of the list item.

        Returns:
            None

        Examples:
            >>> d = uopy.DynArray([1, 2])
            >>> d.make_nested_list(1)
            >>> d[1][0].append(3)
            >>> print(d.list)
            [1, [[2, 3]]]

        """
        self._build_list()
        if not isinstance(self._list[index], list):
            self._list[index] = [[self._list[index]]]
            return

        for i, v in enumerate(self._list[index]):
            if not isinstance(v, list):
                self._list[index][i] = [v]

    def iconv(self, conversion_code):
        """Return the internal storage value of the DynArray based on the conversion code.

        Args:
            conversion_code (str):  the MV conversion code.

        Returns:
            DynArray: the internal storage value.

        Raises:
            UOError

        """
        return self._server_conv(conversion_code, FuncCodes.EIC_ICONV)

    def oconv(self, conversion_code):
        """Return the output format of the DynArray based on the conversion code.

        Args:
            conversion_code (str): the MV conversion code.

        Returns:
            DynArray: the output format.

        Raises:
            UOError

        """
        return self._server_conv(conversion_code, FuncCodes.EIC_OCONV)

    def format(self, format_code):
        """Return the formatted value of the DynArray based on the format code.

        Args:
            format_code (str): the format code.

        Returns:
            DynArray: the formatted value.

        Raises:
            UOError

        """
        return self._server_conv(format_code, FuncCodes.EIC_FMT)

    def _server_conv(self, conversion_code, func_code):
        _logger.debug("Enter", conversion_code, func_code, self.__bytes__())

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, func_code)
            if func_code == FuncCodes.EIC_FMT:
                out_packet.write(1, self._session.encode(conversion_code))
                out_packet.write(2, self.__bytes__())
            else:
                out_packet.write(1, self.__bytes__())
                out_packet.write(2, self._session.encode(conversion_code))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        status = in_packet.read(1)
        if not status:
            result = DynArray(in_packet.read(2), self._session)
            _logger.debug("Exit", result)
            return result
        else:
            raise UOError(code=ErrorCodes.UOE_BAD_CONVERSION_DATA)
