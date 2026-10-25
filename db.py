"""
db.py — the one way to open brain.db, plus the lookups and value
normalisers every script shares.

connect() turns foreign keys on. SQLite leaves them off for every new
connection, so a script that opens brain.db any other way would skip
the schema's guarantees.
"""
import os
import sqlite3

from prompts import ask_text

PROJ    = os.path.expanduser('~/projects/malloc-training')
DB_PATH = os.path.join(PROJ, 'brain.db')


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def session_field(field):
    try:
        with open(os.path.join(PROJ, 'SESSION.md')) as f:
            for line in f:
                if line.startswith(f"{field}:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


def lab_key(name):
    """Compare lab names ignoring case and spacing."""
    return ' '.join((name or '').split()).lower()


def find_lab(c, name):
    """(canonical name, course) of a known lab, or None."""
    key = lab_key(name)
    c.execute('SELECT name, course FROM labs')
    for lab, course in c.fetchall():
        if lab_key(lab) == key:
            return lab, course
    return None


def ask_lab(c, prompt="Lab"):
    """Ask for a lab from the labs table. Enter picks the active lab."""
    active = find_lab(c, session_field("ACTIVE LAB"))
    default = active[0] if active else None
    shown = f"{prompt} [{default}]: " if default else f"{prompt}: "
    while True:
        found = find_lab(c, ask_text(shown, default=default, required=True))
        if found:
            return found
        c.execute('SELECT name FROM labs ORDER BY name')
        known = ', '.join(row[0] for row in c.fetchall()) or 'none'
        print(f"  Unknown lab. Known labs: {known}")
        print("  (lab_transition.py adds the next lab.)")


def clean_report(text):
    """An adversarial gap report, or None when there isn't one.
    '', whitespace and 'none' (any case) all mean missing."""
    text = (text or '').strip()
    if not text or text.lower() == 'none':
        return None
    return text
