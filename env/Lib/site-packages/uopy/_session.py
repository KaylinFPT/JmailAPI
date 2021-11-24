# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

import copy
import threading
import time

from ._constants import MARKS_NAMED_TUPLE, DEFAULT_MARKS
from ._command import Command
from ._config import config, USER, PASSWORD, ACCOUNT, ENCODING, SSL_MODE, POOLING_ON
from ._constants import EXEC_REPLY, \
    EXEC_MORE_OUTPUT, AtVar
from ._dynarray import DynArray
from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._mvdelimited import MvDelimited
from ._transaction import Transaction
from ._uniobject import thread_data
from ._unirpc import UniRPCConnection, UniRPCPacket
from ._uoerror import UOError
from ._utils import mangle, get_host_info, is_cp_supported

_logger = get_logger(__name__)

_RESERVED = 0
_COMMS_VERSION = 4
_CS_VERSION = 6
_RPC_NO_ENCRYPTION = 0
_RPC_ERRORS = {
    ErrorCodes.UOE_RPC_BAD_CONNECTION,
    ErrorCodes.UOE_RPC_NO_CONNECTION,
    ErrorCodes.UOE_RPC_INVALID_ARG_TYPE,
    ErrorCodes.UOE_RPC_WRONG_VERSION,
    ErrorCodes.UOE_RPC_BAD_PARAMETER,
    ErrorCodes.UOE_RPC_FAILED,
    ErrorCodes.UOE_RPC_ARG_COUNT,
    ErrorCodes.UOE_RPC_UNKNOWN_HOST,
    ErrorCodes.UOE_RPC_CANT_FIND_SERVICE,
    ErrorCodes.UOE_RPC_TIMEOUT,
    ErrorCodes.UOE_RPC_REFUSED,
    ErrorCodes.UOE_RPC_CONNECTION,
    ErrorCodes.UOE_SR_SLAVE_READ_FAIL
}


class Session:
    """A Session represents a MV database connection. It is the foundation for and embedded in other UOPY objects.

    Session objects can be used in Python with statement so that whatever happens in the with statement block, they
    are guaranteed to be closed upon exit.

    Applications can also perform transactions on a Session, and get supported @var values from the server.

    Note:
        Applications should call uopy.connect() to get a Session object instead of directly instantiating a Session.

    Examples:

        >>> with uopy.connect(user='test', password='test'):
        >>>     cmd = uopy.Command("LIST VOC")
        >>>     cmd.run()
        >>>     print(cmd.response)


        >>> with uopy.connect(user="test", password="test") as session:
        >>>     session.tx_start()
        >>>     print(session.tx_is_active())
        ...
        >>>     session.tx_commit()

    """

    def __init__(self, connect_config):
        _logger.debug("Enter", {k: connect_config[k] for k in connect_config if k != "password"})

        self._config = connect_config

        self._lock = threading.RLock()

        self._rpc_connection = None
        self._is_rpc_failed = False;

        self._is_nls_enabled = False
        self._is_nls_locale_enabled = False
        self._is_ud = False
        self._is_d3 = False

        self.__pool = None
        self._idle_start_time = 0

        self._mac_address = "JAVA"
        self._license_token = ""

        self._host_type = None
        self._command = None
        self._transaction = None

        self.is_active = False
        self.marks = DEFAULT_MARKS

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        details = self._config
        return format_string.format('.'.join([Session.__module__, Session.__qualname__]), details, id(self))

    def __enter__(self):
        if not self.is_active:
            self.connect()
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self.close()

    def bind_pool(self, pool):
        self.__pool = pool

    @property
    def config(self):
        """A copy of all the configuration parameters for this session."""
        return copy.deepcopy(self._config)

    @property
    def idle_start_time(self):
        return self._idle_start_time;

    def start_idle(self):
        self._idle_start_time = time.time()

    @property
    def db_type(self):
        """str: either "UD' for UniData,'UV' for UniVerse, or "D3" for D3."""

        if self._is_ud:
            return "UD"
        elif self._is_d3:
            return "D3"
        else:
            return "UV"

    @property
    def is_nls_enabled(self):
        """boolean: whether NLS is enabled on the server."""
        return self._is_nls_enabled

    @property
    def encoding(self):
        """The name of the character encoding used for conversion between Python unicode strings and MV data.

        By default it is set to the local system's preferred encoding when server NLS is off, and to UTF-8 when
        server NLS is on. However it can be overridden by the application to what reflects the actual encoding of
        the server data.

        """
        return self._config[ENCODING]

    @encoding.setter
    def encoding(self, encoding):
        try:
            "".encode(encoding.strip())
            self._config[ENCODING] = encoding.strip()
        except LookupError as e:
            _logger.warning("Unsupported encoding setting, encoding is not changed:" + str(e))

    def sync_marks(self, mark_list):
        self.marks = MARKS_NAMED_TUPLE(*mark_list)

    def encode(self, obj):
        if isinstance(obj, str):
            return obj.encode(self._config[ENCODING], errors='replace')
        elif isinstance(obj, bytes) or isinstance(obj, bytearray):
            return obj
        elif isinstance(obj, MvDelimited):
            return bytes(obj)
        elif isinstance(obj, list):
            return bytes(MvDelimited(obj=obj, session=self))
        elif obj is None:
            return b''
        else:
            return str(obj).encode(self._config[ENCODING], errors='replace')

    def decode(self, obj):
        if isinstance(obj, bytes) or isinstance(obj, bytearray):
            return obj.decode(self._config[ENCODING], errors='replace')
        else:
            return str(obj)

    def _check_callable(self, in_exec=False):
        if self._rpc_connection is None or not self._rpc_connection.is_connected:
            raise UOError(code=ErrorCodes.UOE_SESSION_NOT_OPEN)

        if not in_exec:
            if self._command is not None:
                if self._command.status in {EXEC_MORE_OUTPUT, EXEC_REPLY}:
                    raise UOError(code=ErrorCodes.UOE_EXECUTEISACTIVE)

    def rpc_call(self, in_packet, out_packet, in_exec=False):
        with self._lock:
            self._check_callable(in_exec)
            self._rpc_connection.call(in_packet, out_packet)

    def read_packet4cmd(self, packet):
        with self._lock:
            self._rpc_connection.read_packet(packet)

    def connect(self):
        with self._lock:
            if self.is_active:
                _logger.warning("Session._connect: already connected.")
                return

            self._rpc_connection = UniRPCConnection(self._config)
            self._rpc_connection.connect()
            self._login()

            # TODO initialize the transaction object
            # self._transaction = self.Transaction()

            thread_data.session = self

    def _login(self):
        in_packet = UniRPCPacket()
        out_packet = UniRPCPacket()

        out_packet.write(0, _COMMS_VERSION)
        out_packet.write(1, _CS_VERSION)
        out_packet.write(2, self.encode(self._config[USER]))
        out_packet.write(3, mangle(self.encode(self._config[PASSWORD]),
                                   _COMMS_VERSION))
        out_packet.write(4, self.encode(self._config[ACCOUNT]))
        out_packet.write(5, self.encode(self._license_token))
        out_packet.write(6, _RESERVED)

        ip_int, hostname = get_host_info()

        out_packet.write(7, ip_int)
        out_packet.write(8, self.encode(self._mac_address))
        out_packet.write(9, self.encode(hostname))
        out_packet.write(10, b'')

        if config.pooling[POOLING_ON]:
            if is_cp_supported(self._rpc_connection.server_id):
                out_packet.write(11, 1)
            else:
                raise UOError(code=ErrorCodes.UOE_CP_NOTSUPPORTED, message="Database Server upgrade is needed.")

        self._config[PASSWORD] = ""
        self.rpc_call(in_packet, out_packet)

        resp_code = in_packet.read(0)
        if resp_code == 0:
            self._nls_init()
            self._get_host_info()
            self.is_active = True
            self._transaction = Transaction(session=self)
        else:
            if in_packet.argument_count > 1:
                last_error = self.decode(in_packet.read(1))
                raise UOError(message=last_error)
            else:
                raise UOError(code=resp_code)

    def _nls_init(self):
        from ._nlsmap import NLSMap

        in_packet = UniRPCPacket()
        out_packet = UniRPCPacket()
        out_packet.write(0, FuncCodes.EIC_GETSERVERINFO)
        self.rpc_call(in_packet, out_packet)

        resp_code = in_packet.read(0)
        if resp_code != 0:
            raise UOError(code=resp_code)

        nls_mode = in_packet.read(1)
        nls_lc_mode = in_packet.read(2)

        if nls_mode == 1:
            self._is_nls_enabled = True
            if nls_lc_mode == 1:
                self._is_nls_locale_enabled = True
        elif nls_mode == 2:
            self._is_ud = True
        elif nls_mode == 3:
            self._is_d3 = True

        if self._is_nls_enabled or self._is_ud:
            NLSMap(self).set_server_map_name("NONE")
            if self._is_nls_enabled:
                self.encoding = "UTF-8"

            # if self.is_nls_locale_enabled:
            #     _NLSLocale(self).set_server_locale_names("DEFAULT")

    def _get_host_info(self):
        in_packet = UniRPCPacket()
        out_packet = UniRPCPacket()
        out_packet.write(0, FuncCodes.EIC_SESSIONINFO)

        self.rpc_call(in_packet, out_packet)

        resp_code = in_packet.read(0)
        if resp_code == 0:
            self._host_type = in_packet.read(2)
        else:
            raise UOError(code=resp_code)

    def check_rpc_error(self, e):
        if e.code in _RPC_ERRORS:
            self._is_rpc_failed = True

    def health_check(self):
        with self._lock:
            if self._is_rpc_failed:
                _logger.debug("RPC failed")
                return False

        return self._rpc_connection.health_check()

    def hard_close(self):
        try:
            self._rpc_connection.close()
        except Exception as e:
            _logger.warning(str(e))
        finally:
            self.is_active = False
            self._rpc_connection = None
            thread_data.session = None

        _logger.debug("Exit", id(self), "is hard-closed ")

    def get_atvar(self, atvar):
        """Get a @var value from the server.

        Args:
            atvar: uopy.AtVar enum.

        Returns:
            DynArray: the value of the @var

        Raises:
            UOError

        Examples:
            >>> import uopy
            >>> for atvar in uopy.AtVar:
                    print(atvar.name, atvar.value)

            LOG_NAME 1
            PATH 2
            USER_NO 3
            WHO 4
            TRANSACTION 5
            DATA_PENDING 6
            USER_RETURN_CODE 7
            SYSTEM_RETURN_CODE 8
            NULL_STR 9
            SCHEMA 10
            TRANSACTION_LEVEL 11

            >>>
            >>> with uopy.connect(user='test_user', password='test_password') as session:
                    log_name = session.get_atvar(uopy.AtVar.LOG_NAME)
                    account_path = session.get_atvar(uopy.AtVar.PATH)
                    print(log_name)
                    print(account_path)

            test_user
            C:\\U2\\ud82\\XDEMO

        """
        _logger.debug("Enter", atvar)

        self._check_callable()

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()
            out_packet.write(0, FuncCodes.EIC_GETVALUE)
            out_packet.write(1, atvar.value)

            self._rpc_connection.call(in_packet, out_packet)

            resp_code = in_packet.read(0)
            if resp_code == 0:
                _logger.debug("Exit")
                return DynArray(in_packet.read(1), self)
            else:
                raise UOError(code=resp_code)

    def reset(self):
        _logger.debug("Enter", id(self))

        if self._is_rpc_failed:
            return False

        if self._command:
            tmp_command = self._command
            self._command = None

            if tmp_command.status in {EXEC_MORE_OUTPUT, EXEC_REPLY}:
                _logger.warning("Session is in the middle of a command execution.")
                return False

        if self.tx_is_active():
            _logger.warning("Session is in the middle of a transaction, will try to roll back.")
            try:
                self._transaction.rollback()
            except Exception as e:
                _logger.warning("Error occurred during transaction roll back." + str(e))
                return False

        _logger.debug("Exit")
        return True

    def close(self):
        """Close the session or return it to the connection pool.

        Raises:
            UOError

        """
        _logger.debug("Enter",id(self))
        if not self.is_active:
            _logger.warning("Session::disconnect: session is inactive.")
            return

        with self._lock:
            if self.__pool:
                self.__pool.free(self)
            else:
                # self.reset()
                self.hard_close()

        _logger.debug("Exit")

    def bind_command(self, command_obj):
        if self._command:
            _logger.warning("A session can only have one bound Command object, will replace the old one")
        self._command = command_obj

    def tx_start(self):
        """Start a transaction on the server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        self._transaction.begin()

    def tx_commit(self):
        """Commit the current transaction on the server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        self._transaction.commit()

    def tx_rollback(self):
        """Roll back the current transaction on the server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """

        self._transaction.rollback()

    def tx_level(self):
        """Return the current transaction level on the server

        Args:

        Returns:
            int: the current transaction level

        Raises:
             UOError

        """
        return int(str(self.get_atvar(AtVar.TRANSACTION_LEVEL)))

    def tx_is_active(self):
        """Check if a transaction is active on the server.

        Args:

        Returns:
            True/False: in transaction or not

        Raises:
            UOError

        """
        resp = self.get_atvar(AtVar.TRANSACTION)
        if resp == "" or resp == "0":
            return False
        else:
            return True

    def _server_transaction(self, tx_key):
        _logger.debug("Enter", tx_key)

        with self.lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            out_packet.write(0, FuncCodes.EIC_TRANSACTION)
            out_packet.write(1, tx_key)

            try:
                self._rpc_connection.call(in_packet, out_packet, self.encryption_type)
                ret_code = in_packet.read(0)
            except Exception as e:
                raise UOError(message=str(e))

            if ret_code == 0:
                pass
            else:
                self._session.check_rpc_is_failed(ret_code)
                self.status = in_packet.read(1)
                raise UOError(code=ret_code)

        _logger.info("Exit")
