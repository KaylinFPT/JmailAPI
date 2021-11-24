# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._logger import get_logger
from ._mvdelimited import MvDelimited

_logger = get_logger(__name__)


class RecordSet(MvDelimited):

    def __init__(self, obj=None, session=None):
        super().__init__(obj, session, 0)

    def __repr__(self):
        self._build_list()
        format_string = "<{} object {} at 0x{:016X}>"
        details = self._list
        return format_string.format('.'.join([RecordSet.__module__, RecordSet.__qualname__]), details,
                                    id(self))
