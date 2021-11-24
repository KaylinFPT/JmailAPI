# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

import copy
import queue
import threading
import time

from ._config import MIN_POOL_SIZE, MAX_POOL_SIZE, MAX_WAIT_TIME, IDLE_REMOVE_THRESHOLD
from ._errorcodes import ErrorCodes
from ._logger import *
from ._session import Session
from ._uniobject import thread_data
from ._uoerror import UOError

_logger = get_logger(__name__)
lock = threading.RLock()


class Pool:

    def __init__(self, connect_config, pooling_config):
        self.__conn_config = connect_config
        self._pooling_config = pooling_config
        self._connection_pool = {}
        self._lock = threading.RLock()
        self._available = queue.Queue()
        self._busy = []
        self._max_size = self._pooling_config[MAX_POOL_SIZE]
        self._min_size = self._pooling_config[MIN_POOL_SIZE]
        self._max_size = self._min_size if self._min_size > self._max_size else self._max_size
        self._available_count = 0

        self._available.put(self._make_a_connection(raise_error=True))

    def _make_a_connection(self, raise_error=False):
        _logger.debug("Enter")

        try:
            session = Session(copy.deepcopy(self.__conn_config))
            session.connect()
            session.bind_pool(self)
        except Exception as e:
            if not raise_error:
                _logger.warning(e)
                session.hard_close()
                session = None
            else:
                raise

        _logger.debug("Exit")
        return session

    def _test_and_add(self):
        with self._lock:
            total_size = self._available.qsize() + len(self._busy)
            _logger.debug('total size, max_pool_size', total_size, self._max_size)

            if total_size < self._max_size:
                return self._make_a_connection()
            return None

    def _retry_till_timeout(self):
        for retry_count in range(1, 11):
            _logger.debug("retry_count", retry_count)
            try:
                session = self._available.get(True, self._pooling_config[MAX_WAIT_TIME] / 10)
            except queue.Empty:
                session = self._test_and_add()

            if session:
                self._busy.append(session)
                return session

        return None

    def get(self):
        _logger.debug("Enter")

        try:
            session = self._available.get_nowait()
            self._busy.append(session)
        except queue.Empty:
            session = self._test_and_add()
            if session:
                self._busy.append(session)

        if not session:
            session = self._retry_till_timeout()
            if not session:
                _logger.debug("timed out")
                raise UOError(ErrorCodes.UOE_UNISESSION_TIMEOUT, message='Pooling get connection timeout')

        if not session.health_check():
            _logger.warning("Session didn't pass health check, to be hard-closed")
            self._busy.remove(session)
            session.hard_close()
            return self.get()

        _logger.debug("Got session", id(session))
        thread_data.session = session

        _logger.debug("Exit")
        return session

    def free(self, session):
        _logger.debug("Enter", id(session))

        # with self._lock:

        if not session.reset() or not session.health_check():
            self._busy.remove(session)
            session.hard_close()
            self._maintain_min_size()
            return

        session.start_idle()
        self._busy.remove(session)
        self._available.put(session)

        thread_data.session = None

        _logger.debug("Exit")

    def _maintain_min_size(self):
        _logger.debug("Enter")

        with self._lock:
            makeup_count = self._min_size - self._available.qsize() - len(self._busy)
            _logger.debug('available, in_use, min_pool_size', self._available.qsize(), len(self._busy),
                          self._min_size)
            _logger.debug("makeup_count", makeup_count)
            if makeup_count > 0:
                for _ in range(makeup_count):
                    session = self._make_a_connection()
                    if session:
                        self._available.put(session)

        _logger.debug("Exit")

    def remove_idle_connections(self):
        _logger.debug("Enter")

        thresh_hold = self._pooling_config[IDLE_REMOVE_THRESHOLD]
        current_time = time.time()

        while self._available.qsize() > 0 and self._available.qsize() + len(self._busy) > self._min_size:
            try:
                s = self._available.get_nowait()
            except queue.Empty:
                break

            if (current_time - s.idle_start_time) >= thresh_hold:
                s.hard_close()
            else:
                self._available.put(s)
                break

        _logger.debug("Exit")
