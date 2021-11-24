# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

import logging
import os
from logging.handlers import RotatingFileHandler

from ._config import _logging_config, LOG_LEVEL, LOG_FORMAT, LOG_FILE_MAXSIZE, LOG_BACKUP_COUNT, LOG_DIR, LOG_FILE_NAME, \
    LOG_DATA_MAXSIZE

# define two type output format

_standard_fmt = '%(asctime)s : %(process)d : %(threadName)s : %(module)s : %(funcName)s' \
                ' : %(lineno)d ：%(levelname)s : %(message)s'
_simple_fmt = '%(asctime)s - %(threadName)s - %(process)d  - %(name)s - %(funcName)s() - %(levelname)s - %(message)s'

_log_dir = _logging_config[LOG_DIR]
_log_file_name = _logging_config[LOG_FILE_NAME]
_log_file_maxsize = _logging_config[LOG_FILE_MAXSIZE]
_log_format = _logging_config[LOG_FORMAT]
_log_backupCount = _logging_config[LOG_BACKUP_COUNT]
_log_data_maxsize = str(_logging_config[LOG_DATA_MAXSIZE])

# if dir not exits create one
if not os.path.isdir(_log_dir):
    os.mkdir(_log_dir)

# AP absolute path
_logfile_path = os.path.join(_log_dir, _log_file_name)

# log config dict
# logging.basicConfig()
_handler = logging.handlers.RotatingFileHandler(filename=_logfile_path, maxBytes=_log_file_maxsize,
                                                backupCount=_log_backupCount, encoding="utf-8")
if _log_format == 'simple':
    _formatter = logging.Formatter(_simple_fmt)
elif _log_format == 'standard':
    _formatter = logging.Formatter(_standard_fmt)
_handler.setFormatter(_formatter)


def get_logger(name):
    global _formatter
    logging.setLoggerClass(UOLogger)
    logger = logging.getLogger(name)  # create a log object
    logger.setLevel(_logging_config[LOG_LEVEL])
    logger.propagate = False
    logger.addHandler(_handler)
    return logger


class UOLogger(logging.getLoggerClass()):

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            if len(args) > 0:
                format_str_list = ["%." + _log_data_maxsize + "s"] * len(args)
                format_str = " ".join(format_str_list)
                msg += " : " + format_str
            self._log(logging.DEBUG, msg, args, **kwargs)
