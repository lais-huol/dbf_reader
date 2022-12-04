import os
import unittest
import datetime
from dbf_reader.reader import DbfReader
from dbf_reader.renderers import DbfDescriptionText, DbfDescriptionMarkdown, DbfDescriptionPostgresDDL


PATH_ROOT = os.path.dirname(os.path.abspath(__file__))


class TestDbfReader(unittest.TestCase):
    def test_not_in_rb_mode(self):
        with open("tests/__init__.py") as f:
            with self.assertRaises(IOError):
                DbfReader(f)

    def test_not_valid_encoding(self):
        with open("tests/__init__.py", 'rb') as f:
            with self.assertRaises(LookupError):
                DbfReader(f, 'invalid_enconding')

    def test_another_dbase3_invalid_last_update(self):
        with open("tests/data/dbase3_invalid_last_update.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            self.assertIsNone(dbf_reader.last_update, None)

    def test_read_another_dbase3_valid_dbf_definition(self):
        with open("tests/data/another_dbase3.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            self.assertEqual(dbf_reader.file_object, f)
            self.assertEqual(dbf_reader.actual_record, 0)
            self.assertEqual(dbf_reader.file_size, 9286)
            self.assertEqual(dbf_reader.records, 14)
            self.assertEqual(dbf_reader.last_update, datetime.date(1905, 7, 13))
            self.assertIsNotNone(dbf_reader.definition)
            self.assertEqual(dbf_reader.definition.reader, dbf_reader)
            self.assertEqual(dbf_reader.definition.encoding, 'iso-8859-1')
            self.assertEqual(dbf_reader.definition.dbf_format, 3)
            self.assertEqual(dbf_reader.definition.headerlen, 1025)
            self.assertEqual(dbf_reader.definition.numfields, 31)
            self.assertEqual(dbf_reader.definition.record_size, 590)
            self.assertIsNotNone(dbf_reader.definition.fields)
            self.assertEqual(dbf_reader.definition.terminator, b'\r')

    def test_dbase3_invalid_terminator(self):
        with open("tests/data/dbase3_invalid_terminator.dbf", 'rb') as f:
            with self.assertRaisesRegex(ValueError, "The HEADER terminator should.*"):
                DbfReader(f)

    def test_dbase3_empty_number(self):
        with open("tests/data/dbase3_empty_number.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            for row in dbf_reader:
                if dbf_reader.actual_record == 1:
                    self.assertEqual(None, row['N_DECIMAL'])
                    self.assertEqual(1, row['N_ID'])

    def test_dbase3_empty_boolean(self):
        with open("tests/data/dbase3_empty_boolean.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            for row in dbf_reader:
                if dbf_reader.actual_record == 2:
                    self.assertEqual(None, row['L_BOOL'])

    def test_read_valid_dbase3(self):
        with open("tests/data/dbase3.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            self.assertEqual(dbf_reader.file_object, f)
            self.assertEqual(dbf_reader.encoding, 'iso-8859-1')
            self.assertEqual(dbf_reader.actual_record, 0)
            self.assertEqual(dbf_reader.records, 2)
            self.assertEqual(dbf_reader.last_update, datetime.date(2022, 12, 3))
            self.assertEqual(dbf_reader.file_size, 380)
            self.assertIsNotNone(dbf_reader.definition)
            self.assertEqual(dbf_reader.definition.reader, dbf_reader)
            self.assertEqual(dbf_reader.definition.dbf_format, 3)
            self.assertEqual(dbf_reader.definition.headerlen, 225)
            self.assertEqual(dbf_reader.definition.numfields, 6)
            self.assertEqual(dbf_reader.definition.record_size, 77)
            self.assertIsNotNone(dbf_reader.definition.fields)
            self.assertEqual(dbf_reader.definition.terminator, b'\r')
            self.assertEqual(dbf_reader.actual_record, 0)

    def test_iterate_another_dbase3_dbf(self):
        with open("tests/data/dbase3.dbf", 'rb') as f:
            dbf_reader = DbfReader(f)
            readed_rows = 0
            for row in dbf_reader:
                readed_rows += 1
            self.assertEqual(dbf_reader.actual_record, dbf_reader.records)

    def test_render_txt(self):
        for filename in ['another_dbase3', 'dbase3', 'dbase4', 'dbase5']:
            with open(f"tests/data/{filename}.dbf", 'rb') as f:
                with open(f"tests/data/{filename}.txt", 'r') as txt:
                    # txt.write(DbfDescriptionText(DbfReader(f).definition).__str__())
                    self.assertEqual(txt.read(), str(DbfDescriptionText(DbfReader(f).definition)))

    def test_render_markdown(self):
        for filename in ['another_dbase3', 'dbase3', 'dbase4', 'dbase5']:
            with open(f"tests/data/{filename}.dbf", 'rb') as f:
                with open(f"tests/data/{filename}.md", 'r') as txt:
                    # txt.write(DbfDescriptionMarkdown(DbfReader(f).definition).__str__())
                    self.assertEqual(txt.read(), DbfDescriptionMarkdown(DbfReader(f).definition).__str__())

    def test_render_postgres_ddl(self):
        for filename in ['another_dbase3', 'dbase3', 'dbase4', 'dbase5']:
            with open(f"tests/data/{filename}.dbf", 'rb') as f:
                with open(f"tests/data/{filename}.sql", 'r') as txt:
                    # txt.write(str(DbfDescriptionPostgresDDL(DbfReader(f).definition)))
                    self.assertEqual(txt.read(), DbfDescriptionPostgresDDL(DbfReader(f).definition).__str__())

    def test_render_postgres_ddl_invalid_sizes(self):
        with open("tests/data/dbase3_invalid_fields.dbf", 'rb') as f:
            definition = DbfReader(f).definition
            definition.fields[2].decimals = 0

            definition.fields[2].size = 4
            DbfDescriptionPostgresDDL(definition).__str__()

            definition.fields[2].size = 9
            DbfDescriptionPostgresDDL(definition).__str__()

            definition.fields[2].size = 18
            DbfDescriptionPostgresDDL(definition).__str__()

            definition.fields[2].size = 20
            with self.assertRaises(ValueError):
                DbfDescriptionPostgresDDL(definition).__str__()

    def test_render_postgres_ddl_invalid_fieldtype(self):
        with open("tests/data/dbase3_invalid_fields_type.dbf", 'rb') as f:
            with self.assertRaises(ValueError):
                DbfDescriptionPostgresDDL(DbfReader(f).definition).__str__()

    def test_io_open_str(self):
        dbf_reader = DbfReader("tests/data/dbase3.dbf")
        self.assertFalse(dbf_reader.closed)
        self.assertIsNone(dbf_reader.close())
        self.assertTrue(dbf_reader.closed)

    def test_io_close(self):
        dbf_reader = DbfReader(open("tests/data/dbase3.dbf", 'rb'))
        self.assertFalse(dbf_reader.closed)
        self.assertIsNone(dbf_reader.close())
        self.assertTrue(dbf_reader.closed)

    def test_io_fileno(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertGreater(dbf_reader.fileno(), 0)

    def test_io_isatty(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertFalse(dbf_reader.isatty())

    def test_io_seek(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertFalse(dbf_reader.seek(0))

    def test_io_seekable(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertTrue(dbf_reader.seekable())

    def test_io_tell(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertEqual(dbf_reader.tell(), 225)

    def test_io__del__(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertIsNone(dbf_reader.__del__())

    def test_io_readable(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertTrue(dbf_reader.readable())

    def test_io_read(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertEqual(dbf_reader.read(1), b' ')
            self.assertEqual(dbf_reader.read(2), b'  ')

    def test_io_readline(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.readline()

    def test_io_readlines(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.readlines()

    def test_io_readall(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.readall()

    def test_io_readinto(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.readinto()

    def test_io_writable(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            self.assertFalse(dbf_reader.writable())

    def test_io_write(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.write()

    def test_io_writelines(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.writelines()

    def test_io_flush(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.flush()

    def test_io_truncate(self):
        with DbfReader(open("tests/data/dbase3.dbf", 'rb')) as dbf_reader:
            with self.assertRaises(NotImplementedError):
                dbf_reader.truncate()
