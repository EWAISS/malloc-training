import sqlite3
import os
import sys
from datetime import datetime

from prompts import ask_float, ask_int, ask_text, ask_yes_no


def require_table(c, name):
    """Tables come from schema.sql — stop if this database predates it."""
    c.execute("SELECT 1 FROM sqlite_master "
              "WHERE type = 'table' AND name = ?", (name,))
    if not c.fetchone():
        print(f"{name} table missing. Run: python3 init_db.py")
        sys.exit(1)


def mood_check():
    # Check before asking anything, so no answers are lost
    conn = sqlite3.connect(os.path.expanduser(
        '~/projects/malloc-training/brain.db'))
    require_table(conn.cursor(), 'mood_logs')
    conn.close()

    print("=" * 45)
    print("PRE-SESSION STATE CHECK")
    print("Answer honestly. These are facts, not feelings.")
    print("=" * 45)

    sleep = ask_float("\nHours of sleep last night: ", 0, 24)

    ate = 'yes' if ask_yes_no("Did you eat today? (yes/no): ") else 'no'

    days_no_break = ask_int(
        "Days since your last full rest day: ", 0)

    # Score
    score = 0
    if sleep >= 7:
        score += 2
    elif sleep >= 5:
        score += 1

    if ate == 'yes':
        score += 1

    if days_no_break <= 3:
        score += 2
    elif days_no_break <= 6:
        score += 1

    print()

    if score >= 4:
        state = "SHARP"
        print("STATE: SHARP")
        print("Proceed normally. New material allowed.")

    elif score >= 2:
        state = "DEGRADED"
        print("STATE: DEGRADED")
        print(
            "Recommendation: review-only session.\n"
            "Do not introduce new concepts today.\n"
            "Update SESSION.md: EMOTIONAL STATE: degraded"
        )
        if not ask_yes_no("\nProceed anyway? (yes/no): "):
            print("\nGood call. The curriculum will be here tomorrow.")
            _log_state(sleep, ate, days_no_break, state)
            sys.exit(0)

    else:
        state = "CRITICAL"
        print("STATE: CRITICAL")
        print(
            "Do not work today.\n"
            "Sleep. Eat. Rest.\n"
            "The curriculum will be here tomorrow.\n"
            "Nothing learned on a broken brain is retained."
        )
        _log_state(sleep, ate, days_no_break, state)
        ask_text("\nPress ENTER to exit.")
        sys.exit(0)

    _log_state(sleep, ate, days_no_break, state)

    print(f"\nState logged: {state}")
    print("\nNow run:")
    print("  git pull")
    print("  python3 context.py --mini")
    print("=" * 45)


def _log_state(sleep, ate, days_no_break, state):
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            '''INSERT INTO mood_logs
               (sleep_hours, ate, days_no_break, state)
               VALUES (?,?,?,?)''',
            (sleep, ate, days_no_break, state))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"(Could not log to database: {e})")


mood_check()
