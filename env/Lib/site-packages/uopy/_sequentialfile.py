# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._uniobject import UniObject
from ._unirpc import UniRPCPacket
from ._uoerror import UOError

_SEQ_FILE_START = 0
_SEQ_FILE_CURR = 1
_SEQ_FILE_END = 2
_DEFAULT_BLOCK_SIZE = 8192

_logger = get_logger(__name__)


class SequentialFile(UniObject):
    """SequentialFile is used to define and manage MV Sequential Files (which are OS files).

    SequentialFile can be used in the Python with statement so that whatever occurs in the with statement block,
    they are guaranteed to be closed upon exit.

    Examples:
          >>> with SequentialFile("BP", "TEST_SEQ", True) as seq_file:
          >>>   seq_file.write_line("This is test line 1")
          >>>   seq_file.write_line("This is test line 2")
          >>>   seq_file.seek(0) # go to the beginning of the file
          >>>   seq_file.write_line("This is test line 0") # overwrite the first line
          >>>   seq_file.seek(0)
          >>>   seq_file.read_line()
          This is test line 0
          >>>   seq_file.read_line()
          This is test line 2

    """

    def __init__(self, file_name, record_id, create_flag=False, session=None):
        """Initializes a SequentialFile object.

        Args:
            file_name (str): the directory file name.
            record_id (str): the sequential file name.
            create_flag (boolean, optional): when False (default), do not create the file if nonexistent;
                otherwise, create the file if nonexistent.
            session (Session, optional): the Session object that the SequentialFile object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Returns:
            None
            
        Raises:
            UOError
            
        """
        super().__init__(session)

        self._seq_file_name = str(file_name)
        self._seq_record_id = str(record_id)
        self._is_opened = False
        self._seq_timeout = 0
        self._seq_file_handle = 0
        self._status = 0
        self._block_size = _DEFAULT_BLOCK_SIZE
        self._is_read_all = True

        if create_flag:
            self._seq_create_flag = 1
        else:
            self._seq_create_flag = 0

        self.open()

    def __enter__(self):
        if not self._is_opened:
            self.open()
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.close()

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        details = {'dir': self._seq_file_name, 'name': self._seq_record_id}
        return format_string.format('.'.join([SequentialFile.__module__, SequentialFile.__qualname__]), details,
                                    id(self))

    @property
    def status(self):
        """int: The status code set by the remote server after a sequential file operation."""
        return self._status

    @property
    def block_size(self):
        """int: The block size for read_block(). The default value is 8192.

        If left unset, read_block() will read the whole file back.
        If set explicitly, it will be the maximum size of the data read_block() returns.

        """
        return self._block_size

    @block_size.setter
    def block_size(self, value):
        if not isinstance(value, int):
            raise UOError(message='read buffer size must be an integer!')
        if value <= 0:
            raise UOError(message='read buffer size must between greater than 0!')
        self._block_size = value
        self._is_read_all = False

    @property
    def timeout(self):
        """int: the timeout for sequential file operations."""
        return self._seq_timeout

    @timeout.setter
    def timeout(self, new_timeout):

        _logger.debug("Enter")

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_TIMEOUT)
            out_packet.write(1, self._seq_file_handle)
            out_packet.write(2, new_timeout)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code != 0:
                raise UOError(code=resp_code)

            self._seq_timeout = new_timeout

        _logger.debug("Exit")

    def open(self):
        """Open the server-side file, creating it if the create_flag is True and the file doesn't exist.

        Args:

        Returns:

        Raises:
            UOError

        """
        _logger.debug("Enter", self._seq_file_name, self._seq_record_id)

        if self._is_opened:
            return

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_OPENSEQ)
            out_packet.write(1, self._session.encode(self._seq_file_name))
            out_packet.write(2, self._session.encode(self._seq_record_id))
            out_packet.write(3, self._seq_create_flag)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code, obj=self._seq_file_name)

            self._is_opened = True
            self._seq_file_handle = in_packet.read(2)

        _logger.debug("Exit")

    def close(self):
        """Close an opened sequential file.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self._seq_file_name, self._seq_record_id)

        if not self._is_opened:
            return

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_CLOSESEQ)
            out_packet.write(1, self._seq_file_handle)

            resp_code = self._call_server(in_packet, out_packet)
            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def seek(self, offset, relative_pos=0):
        """Move the file pointer within the Sequential File by an offset position specified in bytes.

        Args:
            offset (int): specifies the number of bytes before or after relative_pos.
                    A negative value moves the pointer to a position before aRelPos.
            relative_pos (int): specifies the relative position within a file from which to seek. Default value is 0.
                    0 (default) start from the beginning of the file.
                    1 start from the current position.
                    2 start from the end of the file.

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", offset, relative_pos)

        if relative_pos not in {_SEQ_FILE_START, _SEQ_FILE_CURR, _SEQ_FILE_END}:
            raise UOError(code=ErrorCodes.UOE_EINVAL)

        with self._lock:

            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_SEEK)
            out_packet.write(1, self._seq_file_handle)
            out_packet.write(2, offset)
            out_packet.write(3, relative_pos)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def write_eof(self):
        """Write an EOF marker to the sequential file.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug('Enter')

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_WEOFSEQ)
            out_packet.write(1, self._seq_file_handle)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code != 0:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def write_block(self, blk_data):
        """Write the given block to the sequential file at the location currently set.

        Args:
            blk_data (any): The data to write - can be str, bytes or DynArray.

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug('Enter', blk_data)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_WRITEBLK)
            out_packet.write(1, self._seq_file_handle)
            out_packet.write(2, self._session.encode(blk_data))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._status = in_packet.read(1)
            else:
                raise UOError(code=resp_code)

        _logger.debug("Exit")

    def write_line(self, line_data):
        """Write the given line to the sequential file at the location currently set.

        Args:
            line_data (any): The data to write - can be str, bytes or DynArray.

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug('Enter', line_data)

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_WRITESEQ)
            out_packet.write(1, self._seq_file_handle)
            out_packet.write(2, self._session.encode(line_data))

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._status = in_packet.read(1)
            else:
                raise UOError(code=resp_code)

            _logger.debug("Exit")

    def read_line(self):
        """Reads a line of data from the sequential file.

        The lines must be delimited with a newline character.

        status property will return one of the following values:
        -1    The file is not open for reading.
        0        The read was successful.
        1        The end of file was reached.

        Args:

        Returns:
            str: the line of data read.

        Raises:
            UOError

        """

        _logger.debug('Enter')

        with self._lock:

            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_READSEQ)
            out_packet.write(1, self._seq_file_handle)

            resp_code = self._call_server(in_packet, out_packet)

            if resp_code == 0:
                self._status = in_packet.read(1)
                line_ = in_packet.read(2)
            else:
                raise UOError(code=resp_code)

        _logger.debug("Exit", line_)
        return self._session.decode(line_)

    def read_block(self):
        """ Reads a block of data from the sequential file.

        Upon completion, the status property will return one of the following values:
        -1    The file is not open for reading.
        0     The read was successful.
        1     The end of file was reached.

        Args:
 
        Returns:
            bytes: the data block read.

        Raises:
            UOError

        """

        _logger.debug("Enter")

        with self._lock:

            bytes_buf = b''

            while self._status == 0:
                in_packet = UniRPCPacket()
                out_packet = UniRPCPacket()

                out_packet.write(0, FuncCodes.EIC_READBLK)
                out_packet.write(1, self._seq_file_handle)
                out_packet.write(2, self._block_size)

                resp_code = self._call_server(in_packet, out_packet)

                self._status = in_packet.read(1)

                if resp_code == 0:
                    bytes_buf += in_packet.read(2)

                    if not self._is_read_all:
                        break
                else:
                    raise UOError(code=resp_code)

            _logger.debug("Exit", bytes_buf)
            return bytes_buf
