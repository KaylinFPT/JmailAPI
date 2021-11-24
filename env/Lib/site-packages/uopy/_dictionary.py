# Copyright 2020 - 2020 Rocket Software, Inc. or its affiliates. All Rights Reserved.
#

from ._file import File

_DICT_TYPE_INDEX = 1
_DICT_LOC_INDEX = 2
_DICT_CONV_INDEX = 3
_DICT_NAME_INDEX = 4
_DICT_FORMAT_INDEX = 5
_DICT_SM_INDEX = 6
_DICT_ASSOC_INDEX = 7
_DICT_SQLTYPE_INDEX = 8


class Dictionary(File):
    """ Dictionary provides convenient access to MV dictionary files."""

    def __init__(self, name, session=None):
        """Initialize a Dictionary object.

        Args:
            name (str): the name of the MV file to be opened.
            session (Session, optional): the Session object that the Dictionary object is bound to.
                If omitted, the last opened Session in the current thread will be used.

        Raises:
            UOError

        """
        super().__init__(name, 1, session)  # 1 is for dictionary

    def get_assoc(self, record_id):
        """Return the ASSOC field of the dictionary record.
        
        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the ASSOC field.

        Raises:
            UOError.

        """
        return self.read_field(record_id, _DICT_ASSOC_INDEX)

    def set_assoc(self, record_id, assoc):
        """Set the ASSOC field of the dictionary record.
        
        Args:
            record_id (str or DynArray): the record id of the dictionary file.
            assoc (str or DynArray): the value of the ASSOC field.

        Returns:
            None

        Raises:
            UOError

        """
        self.write_field(record_id, _DICT_ASSOC_INDEX, assoc)

    def get_conv(self, record_id):
        """Return the CONV field of the dictionary record.
        
        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the CONV field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_CONV_INDEX)

    def set_conv(self, record_id, conv_code):
        """Set the CONV field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             conv_code (str or DynArray): the value of the CONV field.

        Returns:
             None

        Raises:
            UOError

        """
        self.write_field(record_id, _DICT_CONV_INDEX, conv_code)

    def get_format(self, record_id):
        """Return the FORMAT field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the FORMAT field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_FORMAT_INDEX)

    def set_format(self, record_id, format_code):
        """Set the FORMAT field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             format_code (str or DynArray): the value of the FORMAT field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_FORMAT_INDEX, format_code)

    def get_loc(self, record_id):
        """Return the LOC field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the LOC field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_LOC_INDEX)

    def set_loc(self, record_id, loc):
        """Set the LOC field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             loc (str or DynArray): the value of the LOC field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_LOC_INDEX, loc)

    def get_name(self, record_id):
        """Return the NAME field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the NAME field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_NAME_INDEX)

    def set_name(self, record_id, name):
        """Set the NAME field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             name (str or DynArray): the value of the NAME field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_NAME_INDEX, name)

    def get_sm(self, record_id):
        """Return the SM field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the SM field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_SM_INDEX)

    def set_sm(self, record_id, sm):
        """Set the SM field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             sm (str or DynArray): the value of the SM field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_SM_INDEX, sm)

    def get_sql_type(self, record_id):
        """Return the SQLType field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the SQLType field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_SQLTYPE_INDEX)

    def set_sql_type(self, record_id, sql_type):
        """Set the SQLType field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             sql_type (str or DynArray): the value of the SQLType field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_SQLTYPE_INDEX, sql_type)

    def get_type(self, record_id):
        """Return the TYPE field of the dictionary record.

        Args:
            record_id (str or DynArray): the record id of the dictionary file.

        Returns:
            DynArray: the value of the TYPE field.

        Raises:
            UOError

        """
        return self.read_field(record_id, _DICT_TYPE_INDEX)

    def set_type(self, record_id, field_type):
        """Set the TYPE field of the dictionary record.

        Args:
             record_id (str or DynArray): the record id of the dictionary file.
             field_type (str or DynArray): the value of the TYPE field.

        Returns:
             None

        Raises:
             UOError

        """
        self.write_field(record_id, _DICT_TYPE_INDEX, field_type)
