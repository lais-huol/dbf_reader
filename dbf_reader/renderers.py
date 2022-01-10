#!/usr/bin/env python


class DbfDescriptionPrinter():
    def __init__(self, definition) -> None:
        self.definition = definition

    def __str__(self):
        result = ''
        result += f"""
FILE DEFINITION
filename: {self.definition.file_object.name}
number of records: {self.definition.records}
header's length:   {self.definition.headerlen}
number of fields:  {self.definition.numfields}
line size:         {self.definition.record_size}
"""
        result += "FIELDS (order, name, type, size, decimals)\n"
        for field in self.definition.fields:
            result += f"  {field.order} {field.name} {field.type} {field.size} {field.decimals}\n"


class DbfDescriptionMarkdown():
    def __init__(self, definition) -> None:
        self.definition = definition

    def __str__(self):
        result = f"""
### File description

| info | value |
| ---- | ---- |
| number of records | {self.definition.records} |
| header's length   | {self.definition.headerlen} |
| number of fields  | {self.definition.numfields} |
| line size         | {self.definition.record_size} |

### Fields

| order | name | type | size | decimals |
| ----- | ---- | ---- | ---- | -------- |
"""
        for field in self.definition.fields:
            result += f"| {field.order} | {field.name} | {field.type} | {field.size} | {field.decimals} |\n"
        return result

    def print(self):
        print(f"{self}")


class DbfDescriptionPostgresDDL():
    def __init__(self, definition, tablename) -> None:
        self.definition = definition
        self.tablename = tablename

    def __str__(self):
        schema, tablename = self.tablename.split(".")
        fields = ",\n".join([DbfDescriptionPostgresDDL.pg_field_definition(field) for field in self.definition.fields])
        return f"CREATE SCHEMA IF NOT EXISTS {schema}; CREATE TABLE IF NOT EXISTS {schema}.{tablename} (\n{fields});"

    def print(self):
        print(f"{self}")

    @staticmethod
    def pg_field_type(field):
        if field.type == "N":
            if field.decimals > 0:
                if field.decimals <= 6:
                    return f"real({field.size}, {field.decimals})"
                elif field.decimals <= 15:
                    return f"double precision({field.size}, {field.decimals})"
                else:
                    raise Exception(f"Too many decimals ({field.decimals}) for field {field.name}.")
            else:
                if field.size <= 4:
                    return "smallint"
                elif field.size <= 9:
                    return "integer"
                elif field.size <= 18:
                    return "bigint"
                else:
                    raise Exception(f"Field {field.name} is too large ({field.size}).")
        elif field.type == 'D':
            return "date"
        elif field.type == 'L':
            return "boolean"
        elif field.type == 'C':
            return f"character varying({field.size})"
        # 'F', 'B', 'M', '@', 'I', '+', 'O', 'G'
        raise Exception(f"Field type '{field.type}' not supported")

    @staticmethod
    def pg_field_definition(field):
        pg_type = DbfDescriptionPostgresDDL.pg_field_type(field)
        return f"{field.name.lower()} {pg_type} NULL"
