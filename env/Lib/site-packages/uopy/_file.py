# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from . import UOError
from ._constants import LOCK_WAIT, LOCK_SHARED, LOCK_RETAIN, LOCK_EXCLUSIVE
from ._recordset import RecordSet
from ._dynarray import DynArray
from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._uniobject import UniObject
from ._unirpc import UniRPCPacket

_logger = get_logger(__name__)

_IK_READL = 4
_IK_READU = 2
_IK_DELETEU = 3
_IK_WRITEU = 5
_IK_WAIT = 1


def _map_read_lock_flag(lock_flag):
    if lock_flag == 0:
        return lock_flag

    tmp_flag = 0
    if lock_flag & LOCK_WAIT:
        tmp_flag = _IK_WAIT

    if lock_flag & LOCK_EXCLUSIVE:
        tmp_flag += _IK_READU
    elif lock_flag & LOCK_SHARED:
        tmp_flag += _IK_READL

    return tmp_flag


def _map_write_lock_flag(lock_flag):
    if lock_flag == 0:
        return lock_flag

    tmp_flag = 0
    if lock_flag & LOCK_WAIT:
        tmp_flag = _IK_WAIT

    if lock_flag & LOCK_RETAIN:
        tmp_flag += _IK_WRITEU

    return tmp_flag


def _map_delete_lock_flag(lock_flag):
    if lock_flag == 0:
        return lock_flag

    tmp_flag = 0
    if lock_flag & LOCK_WAIT:
        tmp_flag = _IK_WAIT

    if lock_flag & LOCK_RETAIN:
        tmp_flag += _IK_DELETEU

    return tmp_flag


_EIO_MSG_DICT = {
    1: "A bad partitioning algorithm exists for this file",
    2: "No such part file",
    3: "Record ID contains unmappable NLS characters",
    4: "Record data contains unmappable NLS characters",
    5: "An IO Error has occured"
}


class File(UniObject):
    """File object represents a MV hashed file on the remote server. It is the main mechanism for applications to
    access MV data remotely.

    File objects can be used in Python with statement so that whatever occurs in the with statement block, they
    are guaranteed to be closed upon exit.

    Examples:

        >>> with uopy.File("VOC") as voc_file:
        >>>     rec = voc_file.read("LIST")
        >>>     print(rec.list)

    """

    def __init__(self, name, dict_flag=0, session=None):
        """Initializes a File object.
        Args:
            name (str): the name of the MV File to be opened.
            dict_flag (int, optional): when it is uopy.DICT_FILE, then the File object points to the dictionary file.
                Otherwise, the target is the data file.
            session (Session, optional): the Session object that the File object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        super().__init__(session)

        if name is None or len(name) == 0:
            raise UOError(ErrorCodes.UOE_INVALIDFILENAME)

        self._command = None
        self._dict_flag = 1 if dict_flag else 0
        self._status = 0
        self._handle = None
        self._type = 0
        self._name = name
        self._is_opened = False

        self.open()

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        details = {'name': self._name, 'type': "DICT" if self._dict_flag else "DATA"}
        return format_string.format('.'.join([File.__module__, File.__qualname__]), details, id(self))

    def __enter__(self):
        if not self._is_opened:
            self.open()
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.close()

    @property
    def handle(self):
        return self._handle

    @property
    def status(self):
        """The status code set by the remote server after a file operation."""
        return self._status

    @property
    def is_opened(self):
        """boolean: True if the File object is opened on the remote server, otherwise False."""
        return self._is_opened

    def _check_opened(self):
        if not self._is_opened:
            raise UOError(code=ErrorCodes.UOE_FILE_NOT_OPEN)

    def open(self):
        """Open the named file on the remote server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._name)

        if self._is_opened:
            return

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_OPEN)
            out_packet.write(1, self._dict_flag)
            out_packet.write(2, self._session.encode(self._name))
            self._status = 0

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code, obj=self._name)

            self._status = in_packet.read(1)
            self._handle = in_packet.read(2)
            self._type = self._status
            self._is_opened = True

        _logger.debug("Exit")

    def clear(self):
        """Clear the content of the file on the remote server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._name)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_CLEARFILE)
            out_packet.write(1, self._handle)

            self._status = 0
            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def close(self):
        """Close the opened file on the remote server - all file and record locks are released.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._name)

        if not self._is_opened:
            return

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_CLOSE)
            out_packet.write(1, self._handle)

            self._status = 0
            self._is_opened = False
            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def delete(self, record_id, lock_flag=0):
        """Delete a record in the file.

        Args:
            record_id (any ): the record id - can be str, bytes, or DynArray.
            lock_flag (int, optional): 0 (default), LOCK_RETAIN, LOCK_WAIT, or LOCK_RETAIN + LOCK_WAIT

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id)

        self._check_opened()

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_DELETE)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_delete_lock_flag(lock_flag))
            out_packet.write(3, self._session.encode(record_id))

            self._status = 0
            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                self._status = in_packet.read(1)
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def read(self, record_id, lock_flag=0):
        """Read a record in the file.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            lock_flag (int, optional): 0 (default, no lock), or [LOCK_EXCLUSIVE or LOCK_SHARED] [+ LOCK_WAIT]

        Returns:
            DynArray: the content of the record.

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id, lock_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_READ)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_read_lock_flag(lock_flag))
            out_packet.write(3, self._session.encode(record_id))

            resp_code = self._call_server(in_packet, out_packet)
            self._status = in_packet.read(1)
            if resp_code != 0:
                if resp_code == ErrorCodes.UOE_EIO:
                    tmp_status = self._status
                    if tmp_status not in _EIO_MSG_DICT:
                        tmp_status = 5
                    msg = self._EIO_MSG_DICT[tmp_status]
                    raise UOError(code=resp_code, message=msg)
                else:
                    raise UOError(code=resp_code)
            else:
                record = DynArray(in_packet.read(2), session=self._session)

        _logger.debug("Exit", record)
        return record

    def write(self, record_id, record, lock_flag=0):
        """Write a record into the file.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            record (any): the record to be written - can be DynArray, str, bytes.
            lock_flag (int, optional): 0 (default), LOCK_RETAIN, LOCK_WAIT, or LOCK_RETAIN + LOCK_WAIT

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id, record, lock_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_WRITE)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_write_lock_flag(lock_flag))
            out_packet.write(3, self._session.encode(record_id))
            out_packet.write(4, self._session.encode(record))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._status = in_packet.read(1)
            else:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def read_field(self, record_id, field_num, lock_flag=0):
        """Read a single field of a record in the file.

        Args:
            record_id (any ): the record id - can be str, bytes, or DynArray
            field_num (int): the field number
            lock_flag (int, optional): 0 (default), or [LOCK_EXCLUSIVE or LOCK_SHARED] [+ LOCK_WAIT]

        Returns:
            DynArray: the value of the field.

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id, field_num, lock_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_READV)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_read_lock_flag(lock_flag))
            out_packet.write(3, field_num)
            out_packet.write(4, self._session.encode(record_id))

            resp_code = self._call_server(in_packet, out_packet)
            self._status = in_packet.read(1)
            if resp_code != 0:
                if resp_code == ErrorCodes.UOE_EIO:
                    tmp_status = self._status
                    if tmp_status not in _EIO_MSG_DICT:
                        tmp_status = 5
                    msg = self._EIO_MSG_DICT[tmp_status]
                    raise UOError(code=resp_code, message=msg)
                else:
                    raise UOError(code=resp_code)
            else:
                field = DynArray(in_packet.read(2), session=self._session)

        _logger.debug("Exit", field)
        return field

    def write_field(self, record_id, field_num, field_value, lock_flag=0):
        """Write a single field of a record to the file.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            field_num (int): the field number.
            field_value (any): the field value to be written - can be DynArray, str, bytes.
            lock_flag (int, optional): 0 (default), LOCK_RETAIN, LOCK_WAIT, or LOCK_RETAIN + LOCK_WAIT

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id, field_num, field_value, lock_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_WRITEV)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_write_lock_flag(lock_flag))
            out_packet.write(3, field_num)
            out_packet.write(4, self._session.encode(record_id))
            out_packet.write(5, self._session.encode(field_value))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._status = in_packet.read(1)
            else:
                raise UOError(code=resp_code)

        _logger.debug("Exit", self._status)

    def lock_file(self):
        """Lock the entire file exclusively.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._name)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_FILELOCK)
            out_packet.write(1, self._handle)

            resp_code = self._call_server(in_packet, out_packet)
            self._status = in_packet.read(1)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def unlock_file(self):
        """Release the exclusive lock on the entire file.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._name)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_FILEUNLOCK)
            out_packet.write(1, self._handle)

            resp_code = self._call_server(in_packet, out_packet)
            self._status = in_packet.read(1)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def lock(self, record_id, lock_flag=LOCK_EXCLUSIVE):
        """Lock a record in the file.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            lock_flag (int, optional): LOCK_EXCLUSIVE (default) or LOCK_SHARED

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id, lock_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_RECORDLOCK)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_read_lock_flag(lock_flag))
            out_packet.write(3, self._session.encode(record_id))

            resp_code = self._call_server(in_packet, out_packet)
            self._status = in_packet.read(1)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def unlock(self, record_id, clear_flag=False):
        """Release locks owned by the current session on a record of the file.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            clear_flag (boolean, optional): False (default), only release the lock on the specified record; otherwise,
                release all the locks owned by the current session.

        Returns:
            None

        Raises:
            UOError

        """

        _logger.debug("Enter", record_id, clear_flag)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_RELEASE)
            out_packet.write(1, self._handle)
            out_packet.write(2, 0 if not clear_flag else 1)
            out_packet.write(3, self._session.encode(record_id))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def is_locked(self, record_id):
        """Check if a record has a lock on it.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.

        Returns:
            boolean: True, a lock exists on the record by either the current session or other sessions.

        Raises:
            UOError

        """
        _logger.debug("Enter", record_id)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_RECORDLOCKED)
            out_packet.write(1, self._handle)
            out_packet.write(2, self._session.encode(record_id))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            lock_status = in_packet.read(1)
            self._status = in_packet.read(2)

        _logger.debug("Exit", lock_status, self._status)
        return False if lock_status == 0 else True

    def get_ak_info(self, index_name=""):
        """Obtain information about the secondary key indexes available on the file.

        Args:
            index_name (str, Optional). If this value is None or ignored, the list of available indices is returned.

        Returns:
            DynArray:
                The return value will vary depending on the type of index, as follows:
                1. For D-Type indexes: Field 1 contains D as the first character and
                    Field 2 contains the location number of the indexed field.
                2. For I-type indexes: Field 1 contains I as the first character,
                    Field 2 contains the I-type expression, and the compiled I-type resides in field 19 and onward.
                3. For both types:
                    2nd value of Field 1 indicates if the index needs to be rebuilt. It is an empty string otherwise.
                    3rd value of Field 1 is set if the index is null-suppressed. It is an empty string otherwise.
                    4th value of Field 1 is set if automatic updates are disabled. It is an empty string otherwise.
                    6th value of Field 1 contains an S for single valued indices or M for a multivalued index.

        Raises:
            UOError

        """
        _logger.debug("Enter", index_name)

        self._check_opened()
        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_INDICES)
            out_packet.write(1, self._handle)
            out_packet.write(2, len(index_name))
            out_packet.write(3, self._session.encode(index_name))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            ak_info = DynArray(in_packet.read(1), self._session)

        _logger.debug("Exit", ak_info)
        return ak_info

    def itype(self, record_id, i_type_id):
        """ Evaluates the specified I-descriptor and returns the evaluated string.

        Args:
            record_id (any): the record id - can be str, bytes, or DynArray.
            i_type_id (any): the I-descriptor record id in the dictionary - can be str, bytes, or DynArray.

        Returns:
            DynArray: the evaluated result.

        Raises:
          UOError

        """
        _logger.debug("Enter", record_id, i_type_id)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_ITYPE)
            out_packet.write(1, self._session.encode(self._name))
            out_packet.write(2, self._session.encode(record_id))
            out_packet.write(3, self._session.encode(i_type_id))

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

            result = DynArray(in_packet.read(1), session=self._session)

        _logger.debug("Exit", result)
        return result

    def read_named_fields(self, id_list, field_list, lock_flag=0):
        """Read a list of named fields on multiple records.

        Note:
            fields can be of D-type or I/V type.
            If field_list contains names that are not defined in the dictionary, these names are replaced by @ID.
            If a field has conv code on it, an oconv is automatically performed on its internal value to get the
            converted output value.

        Args:
            id_list: a list of record ids.
            field_list: a list of field names.
            lock_flag (int, optional): 0 (default, no lock), or [LOCK_EXCLUSIVE or LOCK_SHARED] [+ LOCK_WAIT]

        Returns:
            tuple: a tuple consisting of four lists: 1. response code list, 2. status code list, 3. record id list,
                    4. record list.

        Raises:
            UOError

        Examples:
            >>> with File("RENTAL_DETAILS") as test_file:
            >>>     field_list = ["FULL_NAME", "ACTUAL_RETURN_DATE", "BALANCE_DUE"]
            >>>     id_list = ['1084', '1307', '1976']
            >>>     read_rs = test_file.read_named_fields(id_list, field_list)
            >>>     for l in read_rs:
            >>>         print(l)
            ['0', '0', '0']
            ['0', '0', '0']
            ['1084', '1307', '1976']
            [['Karen McGlone', ['03/29/2010', '03/30/2010', '03/31/2010', '03/30/2010'], '3.50'],
            ['Jamie Klink', ['05/05/2010', '05/07/2010', '05/05/2010', '05/07/2010', '05/05/2010'], '4.82'],
            ['Mo Evans', ['08/23/2010', '08/20/2010', '08/26/2010', '08/22/2010', '08/25/2010', '08/22/2010'], '19.04']]

        """
        _logger.debug("Enter", id_list, field_list, lock_flag )

        self._check_opened()

        id_set = RecordSet(id_list, session=self._session)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_READNAMEDFIELDSET)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_read_lock_flag(lock_flag))
            out_packet.write(3, bytes(id_set))
            out_packet.write(4, b'')
            out_packet.write(5, self._session.encode(field_list))

            self._call_server(in_packet, out_packet)

            resp_code_set = RecordSet(in_packet.read(1), session=self._session)
            status_set = RecordSet(in_packet.read(2), session=self._session)
            return_data_set = RecordSet(in_packet.read(3), session=self._session)
            result_set = (resp_code_set.list, status_set.list, id_set.list, return_data_set.list)

        _logger.debug("Exit", result_set)
        return result_set

    def write_named_fields(self, id_list, field_list, field_data_list, lock_flag=0):
        """Write a list of named fields to multiple records.

        Note:
            If field_list contains names that are not defined in the dictionary, these names are ignored.
            If a field is of I/V type or the record id itself, it is ignored.
            If a field has CONV code on it, an iconv is automatically performed to use its internal value for the write.

        Args:
            id_list: a list of record ids.
            field_list: a list of field names.
            field_data_list: a list of DynArray consisting of all the field values.
            lock_flag (int, optional): 0 (default), LOCK_RETAIN, LOCK_WAIT, or LOCK_RETAIN + LOCK_WAIT

        Returns:
            tuple: a tuple consisting of 4 lists: 1. response code list, 2. status code list, 3. record id list,
                    4. field values list.

        Raises:
            UOError

        Examples:
            >>> with File("RENTAL_DETAILS") as test_file:
            >>>     field_list = ["FULL_NAME", "ACTUAL_RETURN_DATE", "BALANCE_DUE"]
            >>>     id_list = ['1084', '1307', '1976']
            >>>     field_value_list = [['Karen McGlone', ['03/29/2010', '03/30/2010', '03/31/2010', '03/30/2010'],
            '3.50'], ['Jamie Klink', ['05/05/2010', '05/07/2010', '05/05/2010', '05/07/2010', '05/05/2010'], '4.82'],
            ['Mo Evans', ['08/23/2010', '08/20/2010', '08/26/2010', '08/22/2010', '08/25/2010', '08/22/2010'],'19.04']]
            >>>     write_rs = test_file.write_named_fields(id_list, field_list, field_value_list)
            >>>     for l in write_rs:
            >>>         print(l)
            ['0', '0', '0']
            ['0', '0', '0']
            ['1084', '1307', '1976']
            [['Karen McGlone', ['03/29/2010', '03/30/2010', '03/31/2010', '03/30/2010'], '3.50'], ['Jamie Klink',
            ['05/05/2010', '05/07/2010', '05/05/2010', '05/07/2010', '05/05/2010'], '4.82'], ['Mo Evans',
            ['08/23/2010', '08/20/2010', '08/26/2010', '08/22/2010', '08/25/2010', '08/22/2010'], '19.04']]


        """
        _logger.debug("Enter", id_list, field_list, field_data_list, lock_flag)

        self._check_opened()

        id_set = RecordSet(id_list, session=self._session)
        field_data_set = RecordSet(field_data_list, session=self._session)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_WRITENAMEDFIELDSET)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_write_lock_flag(lock_flag))
            out_packet.write(3, bytes(id_set))
            out_packet.write(4, bytes(field_data_set))
            out_packet.write(5, self._session.encode(field_list))

            self._call_server(in_packet, out_packet)

            resp_code_set = RecordSet(in_packet.read(1), session=self._session)
            status_set = RecordSet(in_packet.read(2), session=self._session)
            result_set = (resp_code_set.list, status_set.list, id_set.list, field_data_set.list)

        _logger.debug("Exit", result_set)
        return result_set

    def read_records(self, id_list, lock_flag=0):
        """Read multiple records from the file.

        Args:
            id_list: a list of record ids.
            lock_flag (int, optional): 0 (default, no lock), or [LOCK_EXCLUSIVE or LOCK_SHARED] [+ LOCK_WAIT]

        Returns:
            tuple: a tuple consisting of four lists: 1. response code list, 2. status code list, 3. record id list,
                    4. record list.

        Raises:
            UOError

        """
        _logger.debug("Enter", id_list, lock_flag)

        self._check_opened()

        id_set = RecordSet(id_list, session=self._session)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_READSET)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_read_lock_flag(lock_flag))
            out_packet.write(3, bytes(id_set))
            out_packet.write(4, b'')
            out_packet.write(5, b'')

            self._call_server(in_packet, out_packet)

            resp_code_set = RecordSet(in_packet.read(1), session=self._session)
            status_set = RecordSet(in_packet.read(2), session=self._session)
            return_data_set = RecordSet(in_packet.read(3), session=self._session)
            result_set = (resp_code_set.list, status_set.list, id_set.list, return_data_set.list)

        _logger.debug("Exit", result_set)
        return result_set

    def write_records(self, id_list, record_list, lock_flag=0):
        """Write multiple records into the file.

        Args:
            id_list: a list of record ids.
            record_list: a list of records.
            lock_flag (int, optional): 0 (default), LOCK_RETAIN, LOCK_WAIT, or LOCK_RETAIN + LOCK_WAIT

        Returns:
            tuple: a tuple consisting of four lists: 1. response code list, 2. status code list, 3. record id list,
                    4. record list.

        Raises:
            UOError

        """
        _logger.debug("Enter", id_list, record_list, lock_flag)

        self._check_opened()

        id_set = RecordSet(id_list, session=self._session)
        record_set = RecordSet(record_list, session=self._session)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_WRITESET)
            out_packet.write(1, self._handle)
            out_packet.write(2, _map_write_lock_flag(lock_flag))
            out_packet.write(3, bytes(id_set))
            out_packet.write(4, bytes(record_set))
            out_packet.write(5, b'')

            self._call_server(in_packet, out_packet)

            resp_code_set = RecordSet(in_packet.read(1), session=self._session)
            status_set = RecordSet(in_packet.read(2), session=self._session)
            result_set = (resp_code_set.list, status_set.list, id_set.list, record_set.list)

        _logger.debug("Exit", result_set)
        return result_set
