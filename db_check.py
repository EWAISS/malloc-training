import sqlite3
import os
import sys


def check_database():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')

    if not os.path.exists(os.path.expanduser(db_path)):
        print("brain.db not found. Nothing to check.")
        sys.exit(0)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    errors = []
    warnings = []

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

    # Project / concept count mismatch
    c.execute('SELECT COUNT(*) FROM projects')
    project_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM concepts')
    concept_count = c.fetchone()[0]
    if project_count != concept_count:
        errors.append(
            f"MISMATCH: {project_count} projects "
            f"but {concept_count} concepts")

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
