"""
init_db.py — safe migration script.
Run this once to add all new tables and columns
introduced by the 8-fix upgrade.
Safe to run on an existing database: uses IF NOT EXISTS
and checks before ALTER TABLE.
"""
import sqlite3
import os


def migrate():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ── NEW TABLES ──────────────────────────────

    c.execute(
        '''CREATE TABLE IF NOT EXISTS external_validation (
            id INTEGER PRIMARY KEY,
            concept TEXT,
            project_number INTEGER,
            source TEXT,
            question TEXT,
            your_answer TEXT,
            correct_answer TEXT,
            result TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY,
            sleep_hours REAL,
            ate TEXT,
            days_no_break INTEGER,
            state TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

    c.execute(
        '''CREATE TABLE IF NOT EXISTS adversarial_exams (
            id INTEGER PRIMARY KEY,
            phase INTEGER,
            lab TEXT,
            course TEXT,
            concepts_tested TEXT,
            gap_found TEXT,
            gap_location TEXT,
            resolved TEXT DEFAULT 'pending',
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

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

    conn.commit()
    conn.close()

    print("\nMigration complete.")
    print("All new tables and columns are in place.")
    print("Run db_check.py to verify.")


migrate()
