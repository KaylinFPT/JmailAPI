# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._errorcodes import ErrorCodes

_ERROR_MESSAGES = {
    ErrorCodes.UOE_NOERROR: "No Error",
    ErrorCodes.UOE_ENOENT: "File: [{0}] No such file or directory",
    ErrorCodes.UOE_EACCESS: "Permission denied",
    ErrorCodes.UOE_EINVAL: "Invalid Argument",
    ErrorCodes.UOE_ENFILE: "Invalid File",
    ErrorCodes.UOE_EMFILE: "Too many open files",
    ErrorCodes.UOE_ENOSPC: "No space left on device",
    ErrorCodes.UOE_NETUNREACH: "Network is unreachable",
    ErrorCodes.UOE_USC: "Unsupported Server Operation.  This operation is not supported at this release of the server.",
    ErrorCodes.UOE_LRR: "The last record in the select list has been read",
    ErrorCodes.UOE_RNF: "This Record was not found",
    ErrorCodes.UOE_LCK: "This file or record is locked by another user",
    ErrorCodes.UOE_SELFAIL: "The select operation failed",
    ErrorCodes.UOE_LOCKINVALID: "The task _lock number specified is invalid",
    ErrorCodes.UOE_SEEKFAILED: "The fileSeek() operation failed",
    ErrorCodes.UOE_TX_ACTIVE: "Cannot perform this operation while a transaction is active",
    ErrorCodes.UOE_INVALIDATKEY: "The key used to set or retrieve an @variable is invalid",
    ErrorCodes.UOE_UNABLETOLOADSUB: "Unable to load the subroutine on the server",
    ErrorCodes.UOE_BADNUMARGS: "Wrong number of arguments supplied to the subroutine",
    ErrorCodes.UOE_SUBERROR: "The subroutine failed to complete successfully",
    ErrorCodes.UOE_ITYPEFTC: "The I-type operation failed to complete successfully",
    ErrorCodes.UOE_ITYPEFAILEDTOLOAD: "The I-type failed to load",
    ErrorCodes.UOE_ITYPENOTCOMPILED: "The I-type has not been compiled",
    ErrorCodes.UOE_BADITYPE: "This is not an I-Type or the I-type is corrupt",
    ErrorCodes.UOE_INVALIDFILENAME: "The specified filename is null",
    ErrorCodes.UOE_WEOFFAILED: "writeEOF() failed",
    ErrorCodes.UOE_EXECUTEISACTIVE: "An Execute is currently active on the server",
    ErrorCodes.UOE_EXECUTENOTACTIVE: "No Execute is currently active on the server",
    ErrorCodes.UOE_CANT_ACCESS_PF: "Cannot access part files",
    ErrorCodes.UOE_FAIL_TO_CANCEL: "Failed to cancel an execute",
    ErrorCodes.UOE_INVALID_INFO_KEY: "Bad key for the hostType method",
    ErrorCodes.UOE_CREATE_FAILED: "The creation of the sequential file failed",
    ErrorCodes.UOE_DUPHANDLE_FAILED: "Failed to duplicate a pipe handle",
    ErrorCodes.UOE_NVR: "No VOC record",
    ErrorCodes.UOE_NPN: "No pathname in VOC record",
    ErrorCodes.UOE_NODATA: "The server is not responding",
    ErrorCodes.UOE_SESSION_NOT_OPEN: "The session is not open",
    ErrorCodes.UOE_UVEXPIRED: "The UniVerse license has expired",
    ErrorCodes.UOE_BADDIR: "The directory does not exist, or is not a UniVerse account",
    ErrorCodes.UOE_BAD_UVHOME: "Cannot find the UV account directory",
    ErrorCodes.UOE_INVALIDPATH: "An invalid pathname was found in the UV.ACCOUNT file",
    ErrorCodes.UOE_INVALIDACCOUNT: "The account name supplied is not a valid account",
    ErrorCodes.UOE_BAD_UVACCOUNT_FILE: "The UV.ACCOUNT file could not be found or opened",
    ErrorCodes.UOE_FTA_NEW_ACCOUNT: "Failed to attach to the specified account",
    ErrorCodes.UOE_ULR: "The user limit has been reached on the server",
    ErrorCodes.UOE_IID: "Illegal record ID",
    ErrorCodes.UOE_BFN: "Bad Field Number",
    ErrorCodes.UOE_NO_NLS: "NLS is not available",
    ErrorCodes.UOE_MAP_NOT_FOUND: "NLS Map not found",
    ErrorCodes.UOE_NO_LOCALE: "NLS Locale support is not available",
    ErrorCodes.UOE_LOCALE_NOT_FOUND: "NLS Locale not found",
    ErrorCodes.UOE_CATEGORY_NOT_FOUND: "NLS Locale category not found",
    ErrorCodes.UOE_INVALIDFIELD: "Pointer error in a sequential file operation",
    ErrorCodes.UOE_SESSIONEXISTS: "The session is already open",
    ErrorCodes.UOE_BADPARAM: "Invalid parameter supplied to the subroutine",
    ErrorCodes.UOE_NOMORE: "nextBlock() was used, but no more blocks available",
    ErrorCodes.UOE_NOTATINPUT: "reply() method called without being at a EXEC_REPLY state",
    ErrorCodes.UOE_INVALID_DATAFIELD: "The dictionary entry does not have a valid TYPE field",
    ErrorCodes.UOE_BAD_DICTIONARY_ENTRY: "The dictionary entry is invalid",
    ErrorCodes.UOE_BAD_CONVERSION_DATA: "Unable to convert the data in the field",
    ErrorCodes.UOE_BAD_LOGINNAME: "The user name or password provided is incorrect",
    ErrorCodes.UOE_BAD_PASSWORD: "The password has expired",
    ErrorCodes.UOE_ACCOUNT_EXPIRED: "The account has expired",
    ErrorCodes.UOE_RUN_REMOTE_FAILED: "Unable to run as the given user",
    ErrorCodes.UOE_UPDATE_USER_FAILED: "Unable to update user details",
    ErrorCodes.UOE_FILE_NOT_OPEN: "File [{0}] was previously closed.  Must reopen to perform this operation",
    ErrorCodes.UOE_OPENSESSION_ERR: "Maximum number of UniJava sessions already open",
    ErrorCodes.UOE_NONNULL_RECORDID: "Cannot perform operation on a null recordID",
    ErrorCodes.UOE_SR_SLAVE_READ_FAIL: "Error occurred on server.  Possible client-side licensing failure.",
    ErrorCodes.UOE_SR_SLAVE_INPUT_REPLY: "Failed to write the reply to the slave (ic_inputreply)",
    ErrorCodes.UOE_BAD_SSL_MODE: "Bad SSL mode",
    ErrorCodes.UOE_QUERY_SYNTAX: "Query/sql syntax error or no result",
    ErrorCodes.UOE_UNISESSION_TIMEOUT: "The connection has timed out.",
    ErrorCodes.UOE_CP_NOTSUPPORTED: "Connection Pooling is OFF. Please verify UniVerse or UniData Version. This feature may not "
                                    "be supported in older UniVerse or UniData version.",
    ErrorCodes.UOE_XML_VERIFY_U2VERSION: "Please verify UniVerse or UniData Version. This feature may not be supported in older "
                                         "UniVerse or UniData version.",
    ErrorCodes.UOE_MINPOOL_MORETHAN_LICENSE: "MinPoolSize cannot exceed authorized number of Connection Pooling licenses.",
    ErrorCodes.UOE_ENCODING_NOTSUPPORTED: " Specified encoding is not supported by the current JRE",
    ErrorCodes.UOE_RPC_BAD_CONNECTION: "The connection is bad, and may be passing corrupt data",
    ErrorCodes.UOE_RPC_NO_CONNECTION: "No RPC Connection active.",
    ErrorCodes.UOE_RPC_FAILED: "The RPC failed",
    ErrorCodes.UOE_RPC_UNKNOWN_HOST: "The host name is not valid, or the host is not responding",
    ErrorCodes.UOE_RPC_CANT_FIND_SERVICE: "Cannot find the requested service in the unirpcservices file",
    ErrorCodes.UOE_RPC_TIMEOUT: "The connection has timed out",
    ErrorCodes.UOE_RPC_REFUSED: "The connection was refused as the RPC daemon is not running",
    ErrorCodes.UOE_RPC_CONNECTION: "These packets were created with a different connection.",
    ErrorCodes.UOE_RPC_INVALID_ARG_TYPE: "An argument was requested from the RPC that was of an invalid type." +
                                         "Check RpcServiceType' in connection string.",
    ErrorCodes.UOE_RPC_NO_MORE_CONNECTIONS: "No more connections available",
    ErrorCodes.UOE_RPC_WRONG_VERSION: "Wrong UniRPC version",
    ErrorCodes.UOE_RPC_BAD_PARAMETER: "The requested item does NOT exist.",
    ErrorCodes.UOE_RPC_ARG_COUNT: "Something is wrong with RPC package argument count",
    ErrorCodes.UOE_XMAP_UNABLE_OPEN_DICT: "unable open dict file",
    ErrorCodes.UOE_UNKNOWN_ERROR: "Unexpected Error",
    ErrorCodes.UOE_SUCCESS_WITH_INFO: "Success with Info",
    ErrorCodes.UOE_USAGE_ERROR: "Usage Error",
}


class UOError(Exception):
    """UOError represents error conditions detected in UOPY.

    It is recommended that Applications always use a try/catch block when calling any UOPY function and should rely on
    the code and message in UOError exception for proper error handling and reporting.

    Attributes:
        message (str): the error message.
        code (int): the error code; if the error is reported by the server, it is the server error code.

    """

    def __init__(self, code=ErrorCodes.UOE_UNKNOWN_ERROR, message=None, obj=None):
        super().__init__()
        self.code = code
        self.message = _ERROR_MESSAGES.get(code, "Unknown Error Code")
        if message:
            self.message += " : " + message
        if obj:
            try:
                self.message = self.message.format(obj)
            except:
                self.message += "on " + str(obj)

    def __str__(self):
        return "Error [{0}] : {1}".format(self.code, self.message)
