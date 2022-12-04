#!/usr/bin/env python
import struct
import datetime
import logging
from .reader import DbfReader


class TableDefinition:

    """ DBF definition
        self.dbf_format: int == (3=dBASE Level 5; 4=dBASE Level 7; Bit 3 and bit 7=dBASE IV or dBASE for Windows memo file;
                                 bits 4-6=dBASE IV SQL table; bit 7=.DBT memo file, either a dBASE III PLUS type or
                                 a dBASE IV or dBASE for Windows memo file).
        self.last_update: Union[datetime.date, None] == The file update date, None if month or day is 0
        self.numfields: int == fields count
        self.record_size: int == size of each DBF line
        self.fields:list[Field] == field list
        self.terminator: byte == HEADER terminator character

        An info log will be issued if:
            - The file update date is invalid.
            - The file has a polluted trailing, that is, different from 22 \x00
            - The terminator of the HEADER is different from \r or \x00
        A debug log will be issued with data from
          self.records, self.headerlen, self.numfields, self.record_size, self.fields & self.terminator.
    """

    def __init__(self, reader: DbfReader) -> None:
        self.reader = reader

        # lê um short, que é a versão do DBase
        #       Valid dBASE for Windows table file, bits 0-2 indicate version number: 3 for dBASE Level 5, 4 for dBASE Level 7.
        #       Bit 3 and bit 7 indicate presence of a dBASE IV or dBASE for Windows memo file; bits 4-6 indicate the presence of a dBASE IV SQL table;
        #       bit 7 indicates the presence of any .DBT memo file (either a dBASE III PLUS type or a dBASE IV or dBASE for Windows memo file).
        # lê um short, que é o ANO da última atualização, sendo 0 igual a 1900
        # lê um short, que é o MÊS da última atualização
        # lê um short, que é o DIA da última atualização
        # lê um long, que é a quantidade de registros
        # lê um short, que é o tamanho do header, incluíndo este dados que estão sendo lidos agora e a lista de definição de campos
        # lê os últimos 22 bytes, estes deveriam ser trailing o ser apenas e ter apenas \x00
        header_block_size = 32
        file_header = reader.read(header_block_size)
        self.dbf_format, y, m, d, self.records, self.headerlen, trailing = struct.unpack('<bbbbLH22s', file_header)
        if m == 0 or d == 0:
            logging.info("The file update date is invalid.")
            self.last_update = None
        else:
            self.last_update = datetime.date(y+1900, m, d)
        expected_trailing = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        if trailing != expected_trailing:
            logging.info(f"File has polluted trailing, expected {expected_trailing} but received {trailing}.")

        # a definição de cada campo tem 32 caracteres ignorando os bytes que já foram lidos (32)
        # e avançando para o caractere seguinte (32 + 1 = 33)
        # para saber a quantidade de campos é só dividir os bytes restantes no header
        # pelo tamanho da definição de um campo (32 bytes)
        self.numfields = int((self.headerlen - len(file_header) - 1) / header_block_size)

        # agora é só ler a definição de cada campo, começa em 1 pois o primeiro caractere do DBF indica se a linha foi ou apagada
        self.record_size = 1
        self.fields = []
        for fieldno in range(self.numfields):
            field = FieldDefinition(self, fieldno + 1, reader.read(header_block_size))
            self.record_size += field.size
            self.fields.append(field)

        # soma +1 pois considerando o HEADER terminator
        self.file_size = self.headerlen + (self.record_size * self.records) + 1

        # em algum momento o arquivo DBF passou a ser gerado com erro ao invés de ter uma quebra de linha usando \r,
        # passou a ter uma quebra de linha usando \x00 não foi necessariamente em todos os tipos de arquivos,
        # dado que não identifiquei em PFuuaamm, mas identifiquei em STuuaamm, ao menos a partir de 2021.07
        self.terminator = reader.read(1)
        if self.terminator != '\r':
            logging.info(f"The header terminator should be \\r nas came {self.terminator}.")
        logging.debug(
            {
                "records": self.records,
                "headerlen": self.headerlen,
                "numfields": self.numfields,
                "record_size": self.record_size,
                "fields": [f"{f}" for f in self.fields],
                "terminator": self.terminator,
            }
        )
        if self.terminator != b'\r' and self.terminator != b'\x00':
            raise ValueError(f"The HEADER terminator should be \\r, \\x00 is tolerated, however the character found was {self.terminator}.")


class FieldDefinition:

    """ Definition of each table field, also know how to read and decode the saved value

    Args:
        table (TableDefinition): table definition
        order (int): order of this field in the table
        byte_buffer (bytes): bytes containing the field definition

    Attributes:
        table (TableDefinition): table definition
        order (int): order of this field in the table
        name (str): field name
        type (char): field datatype:
            N=Union[int, float, None], D=Union[datetime.date, None], L=Union[bool, None], C=Union[str, None)
            not supported: F=Float, B=Binary, M=Memo, @=Timestamp, I=Long, +=Autoincrement, O=Double, G=OLE
        size (int): field size
        decimals (int): number of decimal places when it is a decimal field type
        flags (int): other undocumented or unsupported flags
    """

    def __init__(self, table: TableDefinition, order: int, byte_buffer: bytes) -> None:
        # string(11) = field name, right padded with b'\x00' when name is less than 11
        # char(1)    = field datatype
        # ignore(4)  = ignore
        # int(1)     = field size
        # int(1)     = number of decimal places when it is a decimal field type
        name, typ, size, decimals, flags = struct.unpack('<11sc4xBBB13x', byte_buffer)
        self.table = table
        self.order = order
        self.name = name.replace(b'\x00', b'').decode(self.table.reader.encoding)
        self.type = typ.decode("utf-8")
        self.size = int(size)
        self.flags = int(flags)
        self.decimals = int(decimals)
        if self.type not in ["N", "D", "L", "C"]:
            # F 	Float 	Number stored as a string, right justified, and padded with blanks to the width of the field.
            # B 	Binary, a string 	10 digits representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
            # M 	Memo, a string 	10 digits (bytes) representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
            # @ 	Timestamp 	8 bytes - two longs, first for date, second for time.  The date is the number of days since  01/01/4713 BC. Time is hours * 3600000L + minutes * 60000L + Seconds * 1000L
            # I 	Long 	4 bytes. Leftmost bit used to indicate sign, 0 negative.
            # + 	Autoincrement 	Same as a Long
            # O 	Double 	8 bytes - no conversions, stored as a double.
            # G 	OLE 	10 digits (bytes) representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
            raise ValueError(f"Field type '{self.type}' not supported")

    def __str__(self) -> str:
        return f"#{self.order} {self.name} {self.type}({self.size},{self.decimals})"

    @property
    def value(self):
        value = self.table.reader.read(self.size)
        if self.type == "N":
            # N 	Numeric 	Number stored as a string, right justified, and padded with blanks to the width of the field.
            value = value.replace(b'\x00', b'').lstrip()
            if value == b'':
                return None
            if self.decimals > 0:
                return float(value)
            else:
                return int(value)
        elif self.type == 'D':
            # D 	Date 	8 bytes - date stored as a string in the format YYYYMMDD.
            y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
            return datetime.date(y, m, d)
        elif self.type == 'L':
            # L 	Logical 	1 byte - initialized to 0x20 (space) otherwise T or F.
            if value == b'T':
                return True
            elif value == b'F':
                return False
            else:
                return None
        elif self.type == 'C':
            # C 	Character 	All OEM code page characters - padded with blanks to the width of the field.
            return value.decode(self.table.reader.encoding).rstrip()
