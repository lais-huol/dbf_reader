#!/usr/bin/env python
import logging
import codecs
from typing import Union, Dict
from decimal import Decimal
from datetime import date
from io import IOBase


class DbfReader:

    def __init__(self, file_object: IOBase, encoding: str = 'iso-8859-1', table_definition=None) -> None:
        # Necessário para evitar referência circular
        from .definitions import TableDefinition
        if file_object.mode != 'rb':
            raise IOError("File object need to be in binary readble mode ('rb')")
        codecs.lookup(encoding)

        logging.debug(f"open {file_object}")
        self.file_object = file_object
        self.encoding = encoding
        self.actual_record = 0
        self.file_size = None
        self.records = None
        self.last_update = None
        if table_definition is None:
            self.definition = TableDefinition(self, self.encoding)
        # else:
        #     self.definition = table_definition
        #     self.file_object.read(self.definition.headerlen)

    def read(self, num_bytes: int) -> Union[str, bytes]:
        return self.file_object.read(num_bytes)

    def __iter__(self) -> Dict[str, Union[str, int, Decimal, date, bool]]:
        while self.actual_record < self.records:
            self.actual_record += 1
            deleted = self.read(1)
            if deleted != b' ':
                self.read(self.definition.record_size-1)
                continue
            result = {}
            for field in self.definition.fields:
                result[field.name] = field.value
            yield result
