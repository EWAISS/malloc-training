"""
init_db.py — creates or migrates brain.db.
On a fresh database: creates every table from schema.sql.
On an existing database: adds any missing tables and columns.
Safe to run repeatedly: tables use IF NOT EXISTS and
columns are checked before ALTER TABLE.
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

    # ── TABLES (from schema.sql) ─────────────────
    # sqlite3 .schema emits plain CREATE TABLE; make each one
    # a no-op when the table already exists
    with open(SCHEMA_PATH) as f:
        schema = f.read()
    schema = re.sub(r'CREATE TABLE (?!IF NOT EXISTS)',
                    'CREATE TABLE IF NOT EXISTS ', schema)
    c.executescript(schema)
    print("OK: all tables from schema.sql exist")

    # ── COLUMN MIGRATIONS ───────────────────────
    # Add adversarial_gap_report to transfer_exams if missing

    try:
        c.execute(
            '''ALTER TABLE transfer_exams
               ADD COLUMN adversarial_gap_report TEXT
               DEFAULT 'none' ''')
        print("Added: transfer_exams.adversarial_gap_report")
    except sqlite3.OperationalError:
        print("OK: transfer_exams.adversarial_gap_report exists")

    # Add resolution notes to adversarial_exams if missing
    try:
        c.execute(
            '''ALTER TABLE adversarial_exams
               ADD COLUMN resolution TEXT''')
        print("Added: adversarial_exams.resolution")
    except sqlite3.OperationalError:
        print("OK: adversarial_exams.resolution exists")

    conn.commit()
    conn.close()

    print("\nMigration complete.")
    print("All tables and columns are in place.")
    print("Run db_check.py to verify.")


migrate()
