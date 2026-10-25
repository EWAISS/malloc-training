"""
init_db.py — creates or upgrades brain.db from schema.sql.
schema.sql is the single source of truth for every table.

Fresh database   : creates every table (schema version 1).
Version 0 (old)  : migrates to version 1 — see migrate_v0().
Version 1        : adds any missing tables. Safe to run repeatedly.

Every run also makes sure the ACTIVE LAB from SESSION.md is in the
labs table, so the lab prompts can offer it.
"""
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

from db import DB_PATH, PROJ, lab_key, session_field

SCHEMA_PATH    = os.path.join(PROJ, 'schema.sql')
SCHEMA_VERSION = 1

# Old tables whose lab columns must point at the labs table
LAB_COLUMNS = [
    ('projects', 'lab'), ('transfer_exams', 'lab'),
    ('adversarial_exams', 'lab'), ('quiz_records', 'lab'),
    ('lab_handouts', 'lab'), ('lab_transitions', 'lab'),
    ('lab_transitions', 'next_lab'),
]


def schema_statements():
    """schema.sql split into single statements."""
    with open(SCHEMA_PATH) as f:
        lines = [l for l in f if not l.lstrip().startswith('--')]
    statements, current = [], ''
    for line in lines:
        current += line
        if sqlite3.complete_statement(current):
            statements.append(current.strip())
            current = ''
    return statements


def table_names(conn):
    return [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%'")]


def columns(conn, table):
    return [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]


def ensure_active_lab(conn):
    lab = session_field("ACTIVE LAB")
    course = session_field("ACTIVE COURSE")
    if lab == "unknown":
        return
    known = [r[0] for r in conn.execute('SELECT name FROM labs')]
    if lab_key(lab) not in {lab_key(k) for k in known}:
        conn.execute('INSERT INTO labs (name, course) VALUES (?, ?)',
                     (lab, course))
        print(f"Added active lab to labs table: {lab} ({course})")


def migrate_v0(conn):
    """
    Version 0 → 1, in one transaction (rolled back on any problem):
      1. Normalise values the new CHECK constraints reject:
         'none'/blank adversarial reports → NULL, gap_found/resolved
         lowercased, a pending gap with gap_found 'no' → 'n/a'.
      2. Collect every lab name into labs, merging spellings that differ
         only in case or spacing (SESSION.md's spelling wins), and point
         every lab column at the canonical name.
      3. Rebuild each table from schema.sql and copy the rows across
         (SQLite cannot add foreign keys to an existing table).
      4. PRAGMA foreign_key_check — any orphan row aborts the migration.
    """
    conn.execute('BEGIN')
    old = table_names(conn)

    # 1. Values the new CHECK constraints would reject
    if 'transfer_exams' in old:
        conn.execute(
            r"""UPDATE transfer_exams SET adversarial_gap_report = NULL
                WHERE lower(trim(coalesce(adversarial_gap_report, ''),
                                 ' ' || char(9, 10, 13))) IN ('', 'none')""")
    if 'adversarial_exams' in old:
        conn.execute(
            """UPDATE adversarial_exams
               SET gap_found = lower(trim(gap_found)),
                   resolved  = lower(trim(resolved))""")
        conn.execute(
            """UPDATE adversarial_exams SET resolved = 'pending'
               WHERE resolved NOT IN ('pending', 'yes', 'n/a')""")
        conn.execute(
            """UPDATE adversarial_exams SET resolved = 'n/a'
               WHERE resolved = 'pending' AND gap_found = 'no'""")
    if 'external_validation' in old:
        conn.execute(
            """UPDATE external_validation
               SET result = lower(trim(result))""")

    # 2. Labs: one canonical spelling per lab
    canonical = {}   # lab_key -> (name, course)
    active = session_field("ACTIVE LAB")
    if active != "unknown":
        canonical[lab_key(active)] = (active,
                                      session_field("ACTIVE COURSE"))
    for table, col in LAB_COLUMNS:
        if table not in old or col not in columns(conn, table):
            continue
        has_course = 'course' in columns(conn, table)
        rows = conn.execute(
            f"SELECT DISTINCT {col}, "
            f"{'course' if has_course else 'NULL'} FROM {table}")
        for name, course in rows:
            if name is None or not name.strip():
                continue
            key = lab_key(name)
            if key not in canonical:
                canonical[key] = (' '.join(name.split()),
                                  course or 'unknown')
    for table, col in LAB_COLUMNS:
        if table not in old or col not in columns(conn, table):
            continue
        for name, in conn.execute(
                f'SELECT DISTINCT {col} FROM {table}').fetchall():
            if name is None:
                continue
            new = canonical.get(lab_key(name), (None,))[0]
            conn.execute(f'UPDATE {table} SET {col} = ? WHERE {col} = ?',
                         (new, name))

    # 3. Rebuild every table from schema.sql. Rename all old tables
    # first, so the new tables' foreign keys point at the new tables.
    for t in old:
        conn.execute(f'ALTER TABLE {t} RENAME TO _v0_{t}')
    for stmt in schema_statements():
        conn.execute(stmt)
    conn.executemany('INSERT INTO labs (name, course) VALUES (?, ?)',
                     canonical.values())
    for t in old:
        if t not in table_names(conn):
            print(f"  Dropping table {t}: not in schema.sql")
            conn.execute(f'DROP TABLE _v0_{t}')
            continue
        shared = [c for c in columns(conn, f'_v0_{t}')
                  if c in columns(conn, t)]
        cols = ', '.join(shared)
        conn.execute(f'INSERT INTO {t} ({cols}) '
                     f'SELECT {cols} FROM _v0_{t}')
        conn.execute(f'DROP TABLE _v0_{t}')

    # 4. Every reference must resolve
    orphans = conn.execute('PRAGMA foreign_key_check').fetchall()
    if orphans:
        raise sqlite3.IntegrityError(
            "rows that point at nothing:\n" + "\n".join(
                f"    {table} row {rowid} → missing {parent}"
                for table, rowid, parent, _ in orphans))

    conn.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
    conn.execute('COMMIT')


def main():
    # Autocommit mode: migrate_v0 manages its own transaction
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    version = conn.execute('PRAGMA user_version').fetchone()[0]
    tables = table_names(conn)

    if not tables:
        conn.execute('BEGIN')
        for stmt in schema_statements():
            conn.execute(stmt)
        conn.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
        conn.execute('COMMIT')
        print(f"OK: created brain.db (schema version {SCHEMA_VERSION})")

    elif version < SCHEMA_VERSION:
        backup = f"{DB_PATH}.bak-{datetime.now():%Y%m%d-%H%M%S}"
        conn.close()
        shutil.copy2(DB_PATH, backup)
        conn = sqlite3.connect(DB_PATH, isolation_level=None)
        print(f"Migrating brain.db from schema version {version} "
              f"to {SCHEMA_VERSION}.")
        print(f"Backup: {backup}")
        try:
            migrate_v0(conn)
        except sqlite3.Error as e:
            conn.execute('ROLLBACK')
            conn.close()
            print(f"\nMIGRATION FAILED — brain.db is unchanged.\n  {e}")
            print("Fix those rows (db_check.py helps), then re-run "
                  "init_db.py.")
            sys.exit(1)
        conn.execute('VACUUM')  # drop the pages the old tables used
        print(f"OK: migrated to schema version {SCHEMA_VERSION}")

    else:
        # Same version: only create tables that are missing
        missing = [s for s in schema_statements()
                   if (m := re.match(r'CREATE TABLE (\w+)', s))
                   and m.group(1) not in tables]
        for stmt in missing:
            conn.execute(stmt)
        print("OK: all tables from schema.sql exist")

    ensure_active_lab(conn)
    conn.close()
    print("Run db_check.py to verify.")


main()
