CREATE SCHEMA IF NOT EXISTS schemaname;

CREATE TABLE IF NOT EXISTS schemaname.tablename (
  n_id         numeric(19, 5)        NULL,
  c_char10     character varying(10) NULL,
  n_int        numeric(19, 5)        NULL,
  n_decimal    numeric(19, 5)        NULL,
  l_bool       boolean               NULL,
  d_date       date                  NULL
);