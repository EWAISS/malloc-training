import sqlite3
import os
import sys

from db import DB_PATH, connect

SCHEMA_VERSION = 1


def check_database():
    if not os.path.exists(DB_PATH):
        print("brain.db not found. Nothing to check.")
        sys.exit(0)

    conn = connect()
    c = conn.cursor()
    errors = []
    warnings = []

    # An old database has none of the schema's guarantees
    version = c.execute('PRAGMA user_version').fetchone()[0]
    if version < SCHEMA_VERSION:
        print(f"brain.db is schema version {version}; "
              f"scripts expect {SCHEMA_VERSION}.")
        print("Run: python3 init_db.py   (it backs up brain.db first)")
        conn.close()
        sys.exit(1)

    # Duplicate project numbers
    c.execute('''SELECT number, COUNT(*) as cnt
                 FROM projects
                 GROUP BY number HAVING cnt > 1''')
    for d in c.fetchall():
        errors.append(
            f"DUPLICATE: Project {d[0]} appears {d[1]} times")

    # NULL or empty handoffs on completed projects
    c.execute('''SELECT number, name FROM projects
                 WHERE (handoff IS NULL OR handoff = '')
                 AND number > 0''')
    for p in c.fetchall():
        warnings.append(
            f"NULL HANDOFF: Project {p[0]} — {p[1]}")

    # Every project has exactly one concept row of its own.
    # (Comparing totals missed a concept attached to the wrong project.)
    c.execute('''SELECT p.number, COUNT(con.id)
                 FROM projects p
                 LEFT JOIN concepts con ON con.project_number = p.number
                 GROUP BY p.number
                 HAVING COUNT(con.id) != 1''')
    for number, n in c.fetchall():
        errors.append(
            f"MISMATCH: Project {number} has {n} concept rows "
            f"(expected 1)")

    # Orphaned narratives (narrative exists, project does not)
    c.execute('''SELECT pn.project_number
                 FROM project_narrative pn
                 LEFT JOIN projects p
                 ON p.number = pn.project_number
                 WHERE p.number IS NULL''')
    for o in c.fetchall():
        errors.append(
            f"ORPHAN NARRATIVE: project_number={o[0]} "
            f"has no parent in projects table")

    # Any other row whose foreign key points at nothing
    # (orphan concepts, quiz records, validations, unknown labs, ...)
    c.execute('PRAGMA foreign_key_check')
    for table, rowid, parent, _ in c.fetchall():
        if table == 'project_narrative':
            continue  # reported above
        errors.append(
            f"ORPHAN: {table} row {rowid} points at a missing "
            f"{parent} row")

    # Phase transfer exams missing adversarial gap report
    try:
        c.execute('''SELECT phase, lab
                     FROM transfer_exams
                     WHERE adversarial_gap_report IS NULL
                     OR adversarial_gap_report = ''
                     OR adversarial_gap_report = 'none' ''')
        for m in c.fetchall():
            errors.append(
                f"BLOCKED: Phase {m[0]} {m[1]} "
                f"transfer exam missing adversarial gap report. "
                f"Run: python3 adversary.py")
    except sqlite3.OperationalError:
        warnings.append(
            "transfer_exams table missing adversarial_gap_report "
            "column — run init_db.py to migrate")

    # External validations: flag concepts marked owned but never validated
    try:
        c.execute('''SELECT c.name, c.project_number
                     FROM concepts c
                     LEFT JOIN external_validation ev
                     ON ev.concept = c.name
                     AND ev.project_number = c.project_number
                     AND ev.result = 'pass'
                     WHERE c.status = 'owned'
                     AND ev.id IS NULL''')
        unvalidated = c.fetchall()
        if unvalidated:
            for u in unvalidated:
                warnings.append(
                    f"NOT EXTERNALLY VALIDATED: "
                    f"'{u[0]}' (Project {u[1]}) — "
                    f"run validate_concept.py")
    except sqlite3.OperationalError:
        pass  # table may not exist yet


    # Lab transition missing for completed labs
    try:
        c.execute(
            '''SELECT DISTINCT p.lab
               FROM projects p
               LEFT JOIN lab_transitions lt ON lt.lab = p.lab
               WHERE lt.id IS NULL
               GROUP BY p.lab
               HAVING COUNT(p.id) >= 10''')
        missing = c.fetchall()
        for mt in missing:
            warnings.append(
                f"NO LAB TRANSITION: '{mt[0]}' has 10+ projects "
                f"but no transition summary. "
                f"Run: python3 lab_transition.py")
    except sqlite3.OperationalError:
        pass

    conn.close()

    print("=" * 55)
    print("DATABASE INTEGRITY CHECK")
    print("=" * 55)

    if errors:
        print("\nERRORS — must fix before committing:")
        for e in errors:
            print(f"  [ERROR] {e}")

    if warnings:
        print("\nWARNINGS — should fix soon:")
        for w in warnings:
            print(f"  [WARN]  {w}")

    if not errors and not warnings:
        print("\nAll checks passed. Database is clean.")

    print("=" * 55)

    if errors:
        sys.exit(1)
    sys.exit(0)


check_database()
