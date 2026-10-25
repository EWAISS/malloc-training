"""
init_db.py — creates brain.db from schema.sql.
schema.sql is the single source of truth for every table.
On a fresh database: creates every table.
On an existing database: adds any missing tables.
Safe to run repeatedly: tables use IF NOT EXISTS.
New columns need an ALTER TABLE migration here as well, since
IF NOT EXISTS never changes a table that already exists.
"""
import sqlite3
import os
import re

PROJ        = os.path.expanduser('~/projects/malloc-training')
DB_PATH     = os.path.join(PROJ, 'brain.db')
SCHEMA_PATH = os.path.join(PROJ, 'schema.sql')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # sqlite3 .schema emits plain CREATE TABLE; make each one
    # a no-op when the table already exists
    with open(SCHEMA_PATH) as f:
        schema = f.read()
    schema = re.sub(r'CREATE TABLE (?!IF NOT EXISTS)',
                    'CREATE TABLE IF NOT EXISTS ', schema)
    c.executescript(schema)

    conn.commit()
    conn.close()

    print("OK: all tables from schema.sql exist")
    print("Run db_check.py to verify.")


migrate()
