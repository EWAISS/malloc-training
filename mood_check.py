import sqlite3
import os
import sys
from datetime import datetime


def ask_number(prompt, cast):
    """Re-ask until valid — a typo must not count as a good answer."""
    while True:
        try:
            value = cast(input(prompt))
            if value >= 0:
                return value
        except ValueError:
            pass
        print("  Please enter a number.")


def mood_check():
    print("=" * 45)
    print("PRE-SESSION STATE CHECK")
    print("Answer honestly. These are facts, not feelings.")
    print("=" * 45)

    sleep = ask_number("\nHours of sleep last night: ", float)

    ate = input("Did you eat today? (yes/no): ").strip().lower()

    days_no_break = ask_number(
        "Days since your last full rest day: ", int)

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
        confirm = input("\nProceed anyway? (yes/no): ").strip().lower()
        if confirm != 'yes':
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
        input("\nPress ENTER to exit.")
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
            '''CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY,
                sleep_hours REAL,
                ate TEXT,
                days_no_break INTEGER,
                state TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
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
