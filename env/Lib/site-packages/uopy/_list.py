# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._file import File
from ._dynarray import DynArray
from ._funccodes import FuncCodes
from ._logger import *
from ._session import Session
from ._uniobject import UniObject
from ._unirpc import *
from ._uoerror import *

_SELECT_LIST_EMPTY_STATE = 1

_logger = get_logger(__name__)


class List(UniObject):
    """List is used to control, access, and manipulate server side select lists.

    List is iterable - the iterator returns a DynArray object representing a record id.
    The iteration can be run only once until the select list is exhausted - subsequent iteration yields nothing.

    Examples:
        >>> cmd = Command("SELECT VOC WITH F1 = 'V'")
        >>> cmd.run()
        >>> select_list = List() # default is select list 0
        >>> ids = select_list.read_list()
        >>> print(ids[:5])
        ['LOAD.LANG', 'BEGIN.WORK', 'CLEARSELECT', 'RELEASE.ITEMS', 'SET.WIDEZERO']

    """

    def __init__(self, list_no: int = 0, session: Session = None):
        """Initializes a new List object.

        Args:
            list_no (int, optional): select list number (default is 0).
            session (Session, optional): the Session object that the List object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        if list_no < 0 or list_no > 10:
            raise UOError(code=ErrorCodes.UOE_EINVAL)

        super().__init__(session)

        self._list_no = list_no
        self._is_all_fetched = False

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        details = {'list no': self._list_no}
        return format_string.format('.'.join([List.__module__, List.__qualname__]), details, id(self))

    def __iter__(self):
        return self

    def __next__(self):
        next_id = self.next()
        if self._is_all_fetched:
            raise StopIteration()
        return next_id

    def select(self, file_obj: File):
        """ Create a new select list by selecting the File object and generating a select list of
        all the record ids from that file. It will overwrite the previous select list and the select
        list pointer will be reset to the first record id in the list.

        Args:
            file_obj: File or Dictionary object to be selected.

        Returns:

        Raises:
            UOError

        """
        _logger.debug("Enter", self._list_no, file_obj)

        if not file_obj.is_opened:
            raise UOError(code=ErrorCodes.UOE_FILE_NOT_OPEN)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SELECT)
            out_packet.write(1, file_obj.handle)
            out_packet.write(2, self._list_no)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            self._is_all_fetched = False

        _logger.debug("Exit")
        return self

    def clear(self):
        """Clear the selected list, emptying the contents and preparing for a new select list to be generated.

        Args:

        Returns:

        Raises:
            UOError

        """
        _logger.debug("Enter", self._list_no)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_CLEARSELECT)
            out_packet.write(1, self._list_no)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            self._is_all_fetched = True

        _logger.debug("Exit")

    def next(self):
        """Return the next record ID in the select list.

        Args:

        Returns:
            DynArray: The next record id in the select list, or None if exhausted.

        Raises:
            UOError

        """
        _logger.debug("Enter", self._list_no)

        if self._is_all_fetched:
            next_id = None
        else:
            with self._lock:
                in_packet = UniRPCPacket()
                out_packet = UniRPCPacket()

                out_packet.write(0, FuncCodes.EIC_READNEXT)
                out_packet.write(1, self._list_no)

                resp_code = self._call_server(in_packet, out_packet)

                if not resp_code:
                    self._is_all_fetched = False
                    next_id = DynArray(in_packet.read(1), session=self._session)
                elif resp_code == ErrorCodes.UOE_LRR:
                    self._is_all_fetched = True
                    next_id = None
                else:
                    raise UOError(code=resp_code)

        _logger.debug("Exit", next_id)
        return next_id

    def read_list(self):
        """ Read the entire select list back.

        Args:

        Returns: 
            DynArray: contains all the record ids in the select list.

        Raises: 
            UOError

        """
        _logger.debug("Enter", self._list_no)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_READLIST)
            out_packet.write(1, self._list_no)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:

                self._is_all_fetched = True
                if in_packet.read(1) > 0:
                    ids = DynArray(in_packet.read(2), self._session)
                else:
                    ids = DynArray(b'', self._session)
            elif resp_code == ErrorCodes.UOE_LRR:
                self._is_all_fetched = True
                ids = DynArray(b'', self._session)
            else:
                raise UOError(code=resp_code)

        _logger.debug("Exit", ids)
        return ids

    def form_list(self, ids):
        """Create a new select list from the supplied list of record ids.

        The current select list number will be used as the new list number.

        Args:
            ids (DynArray or list): A list of record ids.

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug('Enter', self._list_no, ids)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_FORMLIST)
            out_packet.write(1, self._list_no)
            out_packet.write(2, self._session.encode(ids))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            if resp_code == 0:
                self._is_all_fetched = False

        _logger.debug("Exit")

    def select_alternate_key(self, file_obj: File, index_name):
        """Generate a select list from the given File based on the specified secondary index.

        Args:
            file_obj (File): a File or a Dictionary object.
            index_name (str): index name to select on.

        Returns:
            None

        Raises:
            UOError

        """
        return self._do_ak_select(file_obj, index_name, -1, b'')

    def select_matching_ak(self, file_obj: File, index_name, index_value):
        """Generate a select list from the given File based on the specified secondary index
        whose value matches that of the named value.

        Args:
            file_obj (File): a File or a Dictionary object.
            index_name (str): index name to select on.
            index_value (any): value within the index to select - can be str, bytes, DynArray.

        Returns:
            None

        Raises:
            UOError

        """
        index_value_bytes = self._session.encode(index_value)
        return self._do_ak_select(file_obj, index_name, len(index_value_bytes), index_value_bytes)

    def _do_ak_select(self, file_obj, index_name, index_len, index_value):
        _logger.debug("Enter", self._list_no, file_obj, index_name, index_len, index_value)

        if not isinstance(file_obj, File):
            raise UOError(code=ErrorCodes.UOE_ENFILE)

        if not file_obj.is_opened:
            raise UOError(code=ErrorCodes.UOE_FILE_NOT_OPEN)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SELECTINDEX)
            out_packet.write(1, file_obj.handle)
            out_packet.write(2, self._list_no)
            out_packet.write(3, self._session.encode(index_name))
            out_packet.write(4, index_len)
            out_packet.write_char_array(5, index_value)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            status = in_packet.read(1)
            if status == _SELECT_LIST_EMPTY_STATE:
                self._is_all_fetched = True
            else:
                self._is_all_fetched = False

        _logger.debug("Exit")
        return self
