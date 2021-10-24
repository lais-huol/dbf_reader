#!/usr/bin/env python
import struct, datetime, decimal
import logging

"""
    http://dbase.com/Knowledgebase/INT/db7_file_fmt.htm
    https://wiki.dbfmanager.com/dbf-structure
    https://epics.anl.gov/EpicsDocumentation/AppDevManuals/AppDevGuide/3.12BookFiles/chapter12.html
    https://www.dbf2002.com/dbf-file-format.html

    | Byte	| Contents	    | Description |
    | 0     | 1 byte	    | Valid dBASE for Windows table file, bits 0-2 indicate version number: 3 for dBASE Level 5, 4 for dBASE Level 7. Bit 3 and bit 7 indicate presence of a dBASE IV or dBASE for Windows memo file; bits 4-6 indicate the presence of a dBASE IV SQL table; bit 7 indicates the presence of any .DBT memo file (either a dBASE III PLUS type or a dBASE IV or dBASE for Windows memo file). |
    | 1-3	| 3 bytes	    | Date of last update; in YYMMDD format.  Each byte contains the number as a binary.  YY is added to a base of 1900 decimal to determine the actual year. Therefore, YY has possible values from 0x00-0xFF, which allows for a range from 1900-2155. |
    | 4-7	| 32-bit number	| Number of records in the table. (Least significant byte first.) |
    | 8-9	| 16-bit number	| Number of bytes in the header. (Least significant byte first.) |
    | 10-11	| 16-bit number	| Number of bytes in the record. (Least significant byte first.) |
    | 12-13	| 2 bytes	    | Reserved; filled with zeros. |
    | 14	| 1 byte	    | Flag indicating incomplete dBASE IV transaction. |
    | 15	| 1 byte	    | dBASE IV encryption flag. |
    | 16-27	| 12 bytes	    | Reserved for multi-user processing. |
    | 28	| 1 byte	    | Production MDX flag; 0x01 if a production .MDX file exists for this table; 0x00 if no .MDX file exists. |
    | 29	| 1 byte	    | Language driver ID. |
    | 30-31	| 2 bytes	    | Reserved; filled with zeros. |
    | 32-63	| 32 bytes	    | Language driver name. |
    | 64-67	| 4 bytes	    | Reserved. |
    | 68-n	| 48 bytes each | Field Descriptor Array (see 1.2). |
    | n+1	| 1 byte	    | 0x0D stored as the Field Descriptor terminator. |
    | n+2	| Complex       | Field Properties Structure. See below for calculations of size. |
"""

class FieldDefinition:
    
    def __init__(self, table, order, byte_buffer) -> None:
        # string(11) = nome do campo, prenchido à direita com b'\x00' quando o nome for menor do que 11
        # char(1)    = tipo de campo
        # ignore(4)  = ignore
        # int(1)     = tamanho do campo
        # int(1)     = número de decimais, para campos que têm decimais
        name, typ, size, decimals, flags = struct.unpack('<11sc4xBBB13x', byte_buffer)
        self.table = table
        self.order = order
        self.name = name.replace(b'\x00', b'').decode(self.table.encoding)
        self.type = typ.decode("utf-8")
        self.size = int(size)
        self.flags = int(flags)
        self.decimals = int(decimals)

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
                return decimal.Decimal(value)
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
            return value.decode(self.table.encoding).rstrip()
        # F 	Float 	Number stored as a string, right justified, and padded with blanks to the width of the field. 
        # B 	Binary, a string 	10 digits representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
        # M 	Memo, a string 	10 digits (bytes) representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
        # @ 	Timestamp 	8 bytes - two longs, first for date, second for time.  The date is the number of days since  01/01/4713 BC. Time is hours * 3600000L + minutes * 60000L + Seconds * 1000L
        # I 	Long 	4 bytes. Leftmost bit used to indicate sign, 0 negative.
        # + 	Autoincrement 	Same as a Long
        # O 	Double 	8 bytes - no conversions, stored as a double.
        # G 	OLE 	10 digits (bytes) representing a .DBT block number. The number is stored as a string, right justified and padded with blanks.
        raise Exception(f"Field type '{self.type}' nor supported")


class TableDefinition:

    def __init__(self, reader, encoding='iso-8859-1') -> None:
        self.reader = reader
        self.encoding = encoding

        # ignora os 4 primeiros bytes
        # lê um long, que é a quantidade de registros
        # lê um short, que é o tamanho do header, incluíndo este dados que estão sendo lidos agora e a lista de definição de campos
        # ignora os últimos 22 bytes
        self.records, self.headerlen = struct.unpack('<xxxxLH22x', reader.read(32))

        # a definição de cada campo tem 32 caracteres
        # ignorando os bytes que já foram lidos (32)
        # e avançando para o caractere seguinte (32 + 1 = 33)
        # para saber a quantidade de campos 
        # é só dividir os bytes restantes no header 
        # pelo tamanho da definição de um campo (32 bytes)
        self.numfields = int((self.headerlen - 32 - 1) / 32)


        # agora é só ler a definição de cada campo
        self.record_size = 1
        self.fields = []
        for fieldno in range(self.numfields):
            field = FieldDefinition(self, fieldno+1, reader.read(32))
            self.record_size += field.size
            self.fields.append(field)

        # em algum momento o arquivo DBF passou a ser gerado com erro
        # ao invés de ter uma quebra de linha usando \r, passou a ter
        # uma quebra de linha usando \x00
        # não foi necessariamente em todos os tipos de arquivos, 
        # dado que não identifiquei em PFuuaamm , mas 
        # identifiquei em STuuaamm, ao menos a partir da 
        # competência 2021.07
        self.terminator = reader.read(1)
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
        assert self.terminator == b'\r' or self.terminator == b'\x00'
