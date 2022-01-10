#!/usr/bin/env python
import logging
from .definitions import TableDefinition


class DbfReader:

    def __init__(self, file_object, encoding='iso-8859-1') -> None:
        logging.debug(f"open {file_object}")
        self.file_object = file_object
        self.encoding = encoding
        self.definition = TableDefinition(self, encoding)
        self.actual_record = 0

    def read(self, num_bytes):
        return self.file_object.read(num_bytes)

    def __iter__(self):
        while self.actual_record < self.definition.records:
            self.actual_record += 1
            deleted = self.read(1)
            if deleted != b' ':
                continue
            result = {}
            for field in self.definition.fields:
                result[field.name] = field.value
            yield result
