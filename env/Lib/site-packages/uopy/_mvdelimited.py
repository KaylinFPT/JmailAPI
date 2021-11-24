# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._constants import MARKS_COUNT
from ._logger import get_logger
from ._uniobject import UniObject

_logger = get_logger(__name__)


class MvDelimited(UniObject):

    def __init__(self, obj=None, session=None, mark_idx=1):

        super().__init__(session)

        self._bytes = None
        self._list = None
        self._mark_idx = mark_idx

        if isinstance(obj, list):
            self._list = list(obj)
        elif isinstance(obj, MvDelimited):
            self._list = list(obj.list)
        elif obj is None:
            self._bytes = b''
            self._list = []
        elif isinstance(obj, bytes) or isinstance(obj, bytearray):
            self._bytes = bytes(obj)
        else:
            self._bytes = self._session.encode(str(obj))

    def __str__(self):
        return self._session.decode(self.__bytes__())

    def __repr__(self):
        self._build_list()
        format_string = "<{} object {} at 0x{:016X}>"
        details = self._list
        return format_string.format('.'.join([MvDelimited.__module__, MvDelimited.__qualname__]), details,
                                    id(self))

    @property
    def list(self):
        self._build_list()
        return self._list

    def _to_string(self, lst):
        for i, f in enumerate(lst):
            if isinstance(f, list):
                lst[i] = self._to_string(f)
            else:
                lst[i] = self._session.decode(lst[i])
        return lst

    def _build_list(self):
        if self._list:
            return

        if not self._bytes or len(self._bytes) == 0:
            self._list = []
            return

        self._list = self._to_string(self._build_list_by_mark(self._bytes, self._mark_idx))

    def _find_lower_marks(self, byte_data, mark_idx):
        while mark_idx + 1 < MARKS_COUNT - 1:
            if byte_data.find(self._session.marks[mark_idx + 1]) == -1:
                mark_idx += 1
            else:
                return True

        return False

    def _build_list_by_mark(self, byte_data, mark_idx):
        nested_list = byte_data.split(self._session.marks[mark_idx])
        for i, f in enumerate(nested_list):
            if not self._find_lower_marks(f, mark_idx):
                pass
            else:
                nested_list[i] = self._build_list_by_mark(f, mark_idx + 1)
        return nested_list

    def __getitem__(self, key):
        self._build_list()
        return self._list.__getitem__(key)
        # d = DynArray(self._list.__getitem__(key), self._session)
        # self._list.__setitem__(key, d)
        # return self._list.__getitem__(key)

    def __setitem__(self, key, value):
        self._build_list()
        self._list.__setitem__(key, value)

    def __delitem__(self, key):
        self._build_list()
        self._list.__delitem__(key)

    def __contains__(self, item):
        self._build_list()
        return self._list.__contains__(item)

    def __len__(self):
        self._build_list()
        return self._list.__len__()

    def __iter__(self):
        self._build_list()
        for i in self._list:
            yield i

    def __eq__(self, other):
        if isinstance(other, list) or isinstance(other, MvDelimited):
            self._build_list()
            return self._list == list(other)
        elif isinstance(other, bytes) or isinstance(other, bytearray):
            return self.__bytes__() == bytes(other)
        else:
            return self.__bytes__() == self._session.encode(str(other))

    def __bytes__(self):
        if self._list:
            b_array = bytearray()
            self._list_2_bytes(b_array, self._list, self._mark_idx)
            self._bytes = bytes(b_array)
        else:
            return self._bytes

        return self._bytes

    def append(self, obj):
        self._build_list()
        self._list.append(obj)

    def clear(self):
        self._build_list()
        self._list.clear()
        self._bytes=b''

    def copy(self):
        return self._list.copy()

    def count(self, value):
        self._build_list()
        return self._list.count(value)

    def extend(self, iterable):
        self._build_list()
        self._list.extend(iterable)

    def index(self, value, start=0, stop=9223372036854775807):
        self._build_list()
        return self._list.index(value, start, stop)

    def insert(self, index, obj):
        self._build_list()
        self._list.insert(index, obj)

    def pop(self, index=-1):
        self._build_list()
        item = self._list.pop(index)
        return item

    def remove(self, value):
        self._build_list()
        self._list.remove(value)

    def reverse(self):
        self._build_list()
        self._list.reverse()

    def sort(self, key=None, reverse=False):
        self._build_list()
        self._list.sort(key, reverse)

    def _list_2_bytes(self, b_array, nl, mark_idx):
        if not nl:
            return

        mark = self._session.marks[mark_idx]
        for i in nl[:-1]:
            self._list_item_2_bytes(b_array, i, mark_idx + 1)
            b_array.extend(mark)

        self._list_item_2_bytes(b_array, nl[-1], mark_idx + 1)

    def _list_item_2_bytes(self, b_array, i, mark_idx):
        if (isinstance(i, list) or isinstance(i, MvDelimited)) and mark_idx <= 4:
            self._list_2_bytes(b_array, i, mark_idx)
        else:
            b_array.extend(self._value_2_bytes(i))

    def _value_2_bytes(self, v):
        if v is None:
            return b''

        if isinstance(v, bytes) or isinstance(v, bytearray):
            return bytes(v)
        else:
            return self._session.encode(str(v))
