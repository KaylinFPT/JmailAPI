# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._constants import EXEC_COMPLETE, EXEC_REPLY, EXEC_MORE_OUTPUT
from ._errorcodes import ErrorCodes
from ._funccodes import FuncCodes
from ._logger import get_logger
from ._uniobject import UniObject
from ._unirpc import UniRPCPacket
from ._uoerror import UOError

_EXEC_END = 1
_EXEC_BTS = 22002  # Buffer size too small.
_EXEC_AT_INPUT = 39119  # The server is waiting for input to a command_text
_EXEC_DEFAULT_BUFFER_SIZE = 8192

_logger = get_logger(__name__)


class Command(UniObject):
    """Command allows applications to run MV ECL/TCL commands or stored procedures on the remote server.

    After a command is executed, it can have one of these three status:
        EXEC_COMPLETE: the command execution has completed.

        EXEC_REPLY: the command awaits user input - the reply() method can be called to provide an input.

        EXEC_MORE_OUTPUT: the command output buffer isn't big enough to hold all the results. In this case,
            the next_response() method can be called to get the next block of the response.

    When the status is either EXEC_REPLY or EXEC_MORE_OUTPUT, the cancel() method can be called to terminate
    the command execution.

    Attributes:
        command_text (str): the command text.
        at_system_return_code (int) : the value of the system variable @SYSTEM.RETURN.CODE on the server.
        at_selected (int): The value of the system variable @SELECTED on the server.

    Examples:

        >>> with uopy.connect(user='test', password='test'):
        >>>     cmd = uopy.Command("LIST VOC")
        >>>     cmd.run()
        >>>     print(cmd.response)

        >>> with uopy.connect(user='test', password='test'):
        >>>     cmd = uopy.Command("RUN BP SAYHELLOTO")
        >>>     if cmd.status == uopy.EXEC_REPLY:
        >>>         cmd.reply("MV loyal user")
        >>>     print(cmd.response)

    """

    def __init__(self, command_text=None, session=None):
        """Initialize a Command object

        Args:
            command_text (str, optional): the TCL/ECL command to be executed on the remote server.
            session (Session, optional): the Session object that the Command object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        super().__init__(session)

        self._buffer_size = _EXEC_DEFAULT_BUFFER_SIZE
        self._status = EXEC_COMPLETE
        self._response = ""
        self._next_block = ""
        self.command_text = "" if command_text is None else command_text
        self.at_system_return_code = 0
        self.at_selected = 0
        self._is_fetch_all = True
        self._session.bind_command(self)

    def __repr__(self):
        format_string = "<{} object {} at 0x{:016X}>"
        details = {'command_text': self.command_text}
        return format_string.format('.'.join([Command.__module__, Command.__qualname__]), details, id(self))

    @property
    def status(self):
        """int: The current status of the Command object."""
        return self._status

    @property
    def response(self):
        """str: The current response of the Command object from the server."""
        return self._response

    @property
    def buffer_size(self):
        """int: The size of the output buffer for the Command object.

        If left unset, all the output of the command execution will be brought back at once.
        If set explicitly, only the output of the specified size will be returned.

        """
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, value):
        if not isinstance(value, int):
            raise UOError(message='output buffer size must be an integer!')
        if value <= 0:
            raise UOError(message='output buffer size must between greater than 0!')
        self._buffer_size = value
        self._is_fetch_all = False

    def _exec(self, server_command, input_reply):

        in_packet = UniRPCPacket()
        out_packet = UniRPCPacket()

        out_packet.write(0, server_command)

        if server_command == FuncCodes.EIC_EXECUTE:
            out_packet.write(1, self._buffer_size)
            out_packet.write(2, self._session.encode(self.command_text))
        elif server_command == FuncCodes.EIC_EXECUTECONTINUE:
            out_packet.write(1, self._buffer_size)
        elif server_command == FuncCodes.EIC_INPUTREPLY:
            reply_str = input_reply + "\n"
            out_packet.write(1, self._session.encode(reply_str))
            out_packet.write(2, self._buffer_size)
        else:
            raise UOError(code=ErrorCodes.UOE_EINVAL)

        resp_code = self._call_server(in_packet, out_packet, in_exec=True)

        if resp_code == _EXEC_END:
            tmp_resp = self._session.decode(in_packet.read(1))
            self._session.read_packet4cmd(in_packet)
            self.at_system_return_code = in_packet.read(1)
            self.at_selected = in_packet.read(2)
            resp_code = EXEC_COMPLETE
        elif resp_code == _EXEC_BTS:
            tmp_resp = self._session.decode(in_packet.read(1))
            resp_code = EXEC_MORE_OUTPUT
        elif resp_code == _EXEC_AT_INPUT:
            tmp_resp = self._session.decode(in_packet.read(1))
            resp_code = EXEC_REPLY
        else:
            e = UOError(code=resp_code)
            _logger.debug(e)
            raise e

        if server_command == FuncCodes.EIC_EXECUTECONTINUE:
            self._next_block = tmp_resp
        else:
            self._response = tmp_resp

        _logger.debug("Response", tmp_resp, resp_code)
        return resp_code

    def _fetch_all(self, resp_code):
        while resp_code == EXEC_MORE_OUTPUT:
            resp_code = self._exec(FuncCodes.EIC_EXECUTECONTINUE, "")
            if resp_code in [EXEC_MORE_OUTPUT, EXEC_COMPLETE]:
                self._response += self._next_block
        return resp_code

    def run(self):
        """Execute the command on the remote server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", self.command_text)

        with self._lock:
            if self._status in {EXEC_MORE_OUTPUT, EXEC_REPLY}:
                raise UOError(code=ErrorCodes.UOE_EXECUTEISACTIVE)

            if self.command_text is None or self.command_text == "":
                raise UOError(ErrorCodes.UOE_USAGE_ERROR, message="invalid command_text")

            self.at_system_return_code = 0
            self.at_selected = 0
            self._response = ""

            resp_code = self._exec(FuncCodes.EIC_EXECUTE, "")
            self._status = resp_code

            if self._is_fetch_all and resp_code == EXEC_MORE_OUTPUT:
                self._status = self._fetch_all(resp_code)

        _logger.debug("Exit", self._status, self._response)

    def cancel(self):
        """Cancel the execution of the command.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter")

        with self._lock:
            in_packet = UniRPCPacket()
            out_packet = UniRPCPacket()

            if self._status in {EXEC_REPLY, EXEC_MORE_OUTPUT}:
                self._status = EXEC_COMPLETE

                out_packet.write(0, FuncCodes.EIC_CANCEL)

                resp_code = self._call_server(in_packet, out_packet)

                resp_code = in_packet.read(0)
                if resp_code != 0:
                    e = UOError(code=resp_code)
                    _logger.debug(e)
                    raise e
            else:
                _logger.warning("execution already finished")

        _logger.debug("Exit")

    def reply(self, reply_data):
        """Send a reply to the server to continue the command execution.

        Args:
            reply_data: the input for the command.

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter", reply_data)

        with self._lock:
            if self._status != EXEC_REPLY:
                raise UOError(code=ErrorCodes.UOE_NOTATINPUT)

            # reply_data += "\n"
            resp_code = self._exec(FuncCodes.EIC_INPUTREPLY, reply_data)

            self._status = resp_code
            if self._is_fetch_all and resp_code == EXEC_MORE_OUTPUT:
                self._status = self._fetch_all(resp_code)

        _logger.debug("Exit", self._status)

    def next_response(self):
        """Get the next block of output from the server.

        Args:

        Returns:
            None

        Raises:
            UOError

        """
        _logger.debug("Enter")

        with self._lock:
            if self._status != EXEC_MORE_OUTPUT:
                raise UOError(code=ErrorCodes.UOE_NOMORE)

            self._response = None
            resp_code = self._exec(FuncCodes.EIC_EXECUTECONTINUE, "")

            self._response = self._next_block

            self._status = resp_code
            if self._is_fetch_all and resp_code == EXEC_MORE_OUTPUT:
                self._status = self._fetch_all(resp_code)

        _logger.debug("Exit", self._status, self._response)
