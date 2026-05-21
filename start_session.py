"""
start_session.py
Single entry point for every session.
Runs in fixed order — cannot be skipped or reordered.
STEP 1: Mood check (behavioral facts)
STEP 2: Database integrity check
STEP 3: Validation debt gate (Addition 2)
STEP 4: Context generation
STEP 5: Machine-checked verification answers (Addition 3)
"""

import sqlite3
import os
import sys
import subprocess
from datetime import datetime

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

DB_PATH = os.path.expanduser('~/projects/malloc-training/brain.db')
PROJ    = os.path.expanduser('~/projects/malloc-training')


# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────

def banner(title):
    print("\n" + "=" * 58)
    print(title)
    print("=" * 58)


def get_db():
    return sqlite3.connect(DB_PATH)


def get_session_field(field):
    path = os.path.join(PROJ, 'SESSION.md')
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{field}:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "unknown"


def abort(reason):
    print(f"\nSESSION BLOCKED: {reason}")
    print("Fix the issue above and run start_session.py again.")
    sys.exit(1)


# ─────────────────────────────────────────────
# STEP 1 — MOOD CHECK
# ─────────────────────────────────────────────

def step_mood():
    banner("STEP 1 / 5 — PRE-SESSION STATE CHECK")
    print("Answer honestly. These are facts, not feelings.\n")

    try:
        sleep = float(input("Hours of sleep last night: "))
    except ValueError:
        sleep = 0.0

    ate = input("Did you eat today? (yes/no): ").strip().lower()

    try:
        days_no_break = int(
            input("Days since your last full rest day: "))
    except ValueError:
        days_no_break = 0

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

    if score >= 4:
        state = "SHARP"
        print("\nSTATE: SHARP — proceed normally.")
    elif score >= 2:
        state = "DEGRADED"
        print("\nSTATE: DEGRADED — review only, no new concepts.")
        confirm = input("Proceed anyway? (yes/no): ").strip().lower()
        if confirm != 'yes':
            _log_mood(sleep, ate, days_no_break, state)
            print("Good call. Come back tomorrow.")
            sys.exit(0)
    else:
        state = "CRITICAL"
        print("\nSTATE: CRITICAL — do not work today.")
        print("Sleep. Eat. Rest. The curriculum will be here tomorrow.")
        _log_mood(sleep, ate, days_no_break, state)
        sys.exit(0)

    _log_mood(sleep, ate, days_no_break, state)
    print(f"State logged: {state}")
    return state


def _log_mood(sleep, ate, days_no_break, state):
    try:
        conn = get_db()
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
    except Exception:
        pass


# ─────────────────────────────────────────────
# STEP 2 — DATABASE INTEGRITY CHECK
# ─────────────────────────────────────────────

def step_db_check():
    banner("STEP 2 / 5 — DATABASE INTEGRITY CHECK")
    result = subprocess.run(
        ['python3', os.path.join(PROJ, 'db_check.py')],
        capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        abort("Database integrity check failed.\n"
              "Run db_check.py manually to see full errors.")


# ─────────────────────────────────────────────
# STEP 3 — VALIDATION DEBT GATE  (Addition 2)
# Rate: for every 10 projects, at least 2 must be
# externally validated. Debt hides next project number.
# ─────────────────────────────────────────────

def step_validation_gate():
    banner("STEP 3 / 5 — EXTERNAL VALIDATION GATE")

    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM projects')
    total_projects = c.fetchone()[0]

    try:
        c.execute('SELECT COUNT(*) FROM external_validation '
                  "WHERE result = 'pass'")
        total_validated = c.fetchone()[0]
    except sqlite3.OperationalError:
        total_validated = 0

    conn.close()

    if total_projects == 0:
        print("No projects yet — validation gate not applicable.")
        return True  # no debt at start

    # Required: 2 validations per 10 projects completed
    required = (total_projects // 10) * 2
    debt     = max(0, required - total_validated)

    if debt > 0:
        print(f"VALIDATION DEBT DETECTED")
        print(f"  Projects completed  : {total_projects}")
        print(f"  Validations required: {required} "
              f"(2 per 10 projects)")
        print(f"  Validations done    : {total_validated}")
        print(f"  Debt                : {debt} validation(s)")
        print(
            f"\nNext project number is HIDDEN until debt is cleared.\n"
            f"Run: python3 validate_concept.py\n"
            f"Complete {debt} external validation(s), then re-run "
            f"start_session.py."
        )
        return False  # debt active — caller will hide next project
    else:
        if total_projects > 0:
            print(
                f"Validation rate OK — "
                f"{total_validated}/{required} required validations done.")
        return True  # no debt


# ─────────────────────────────────────────────
# STEP 4 — CONTEXT GENERATION
# ─────────────────────────────────────────────

def step_context(validation_ok):
    banner("STEP 4 / 5 — CONTEXT GENERATION")

    conn = get_db()
    c = conn.cursor()

    active_lab    = get_session_field("ACTIVE LAB")
    active_course = get_session_field("ACTIVE COURSE")

    try:
        now = datetime.now(pytz.timezone('Africa/Cairo')) \
            if HAS_PYTZ else datetime.now()
    except Exception:
        now = datetime.now()

    print(f"\nDate   : {now.strftime('%A %d %B %Y %I:%M %p Cairo')}")
    print(f"Course : {active_course}")
    print(f"Lab    : {active_lab}")

    c.execute('SELECT COUNT(*) FROM projects')
    count = c.fetchone()[0]

    if count == 0:
        print("\nNo projects completed yet. Starting from Project 1.")
        conn.close()
        return

    # Last project
    c.execute(
        '''SELECT number, name, concept, status,
                  what_failed, handoff, phase
           FROM projects ORDER BY number DESC LIMIT 1''')
    last = c.fetchone()

    print(f"\nLast project   : {last[0]} — {last[1]}")
    print(f"Core concept   : {last[2]}")
    print(f"Status         : {last[3]}")
    print(f"Phase          : {last[6]}")

    if validation_ok:
        print(f"Next project   : {last[0] + 1}")
    else:
        print(f"Next project   : HIDDEN — clear validation debt first")

    if last[5]:
        print(f"\nHANDOFF:\n{last[5]}")

    # Active weaknesses
    c.execute(
        '''SELECT concept, watch_for_recurrence
           FROM weakness_patterns
           ORDER BY project_number DESC LIMIT 3''')
    weaknesses = c.fetchall()
    if weaknesses:
        print("\nACTIVE WEAKNESSES:")
        for w in weaknesses:
            print(f"  — {w[0]}: {w[1]}")

    # Owned concepts (last 5)
    c.execute(
        '''SELECT c.name, c.how_it_clicked
           FROM concepts c
           JOIN projects p ON p.number = c.project_number
           WHERE p.lab = ? AND c.status = 'owned'
           ORDER BY c.project_number DESC LIMIT 5''',
        (active_lab,))
    owned = c.fetchall()
    if owned:
        print(f"\nRECENT OWNED CONCEPTS:")
        for o in owned:
            print(f"  — {o[0]}: {o[1]}")

    # External validation status
    try:
        c.execute(
            '''SELECT concept, source, result
               FROM external_validation
               ORDER BY validated_at DESC LIMIT 3''')
        vals = c.fetchall()
        if vals:
            print("\nEXTERNAL VALIDATIONS (recent):")
            for v in vals:
                mark = "PASS" if v[2] == 'pass' else "FAIL"
                print(f"  [{mark}] {v[0]} — {v[1]}")
    except sqlite3.OperationalError:
        pass

    # Mind model
    try:
        c.execute(
            '''SELECT content FROM mind_model
               ORDER BY project_number DESC LIMIT 1''')
        mm = c.fetchone()
        if mm:
            print(f"\nMIND MODEL (latest):\n{mm[0][:400]}")
    except sqlite3.OperationalError:
        pass

    conn.close()


# ─────────────────────────────────────────────
# STEP 5 — MACHINE-CHECKED VERIFICATION  (Addition 3)
# Prints correct answers from DB BEFORE Claude sees anything.
# After Claude answers, comparison is instant.
# ─────────────────────────────────────────────

def step_verification():
    banner("STEP 5 / 5 — CONTEXT VERIFICATION ANSWERS")

    conn = get_db()
    c = conn.cursor()
    active_lab = get_session_field("ACTIVE LAB")

    c.execute('SELECT COUNT(*) FROM projects')
    count = c.fetchone()[0]

    if count == 0:
        print("No projects yet — verification not applicable.")
        conn.close()
        return

    # Pull correct answers from database
    c.execute(
        '''SELECT number, name, concept,
                  what_failed, handoff
           FROM projects
           WHERE lab = ?
           ORDER BY number DESC LIMIT 1''',
        (active_lab,))
    last = c.fetchone()

    c.execute(
        '''SELECT concept, watch_for_recurrence
           FROM weakness_patterns
           ORDER BY project_number DESC LIMIT 1''')
    weakness = c.fetchone()

    print("\nCORRECT ANSWERS — from your database.")
    print("Keep this visible. After Claude answers, compare line by line.")
    print("Vague or wrong answer = repaste context, verify again.\n")
    print("─" * 58)

    if last:
        print(f"Q1 Last concept    : {last[2]}")
        print(f"Q2 Struggled with  : {last[3]}")
        print(f"Q3 Handoff says    : {last[4] or '(none recorded)'}")
    else:
        print("Q1 Last concept    : (no projects yet)")
        print("Q2 Struggled with  : (no projects yet)")
        print("Q3 Handoff says    : (no projects yet)")

    if weakness:
        print(f"Q4 Active weakness : {weakness[0]} — {weakness[1]}")
    else:
        print("Q4 Active weakness : (none recorded yet)")

    print("─" * 58)
    print(
        "\nNow paste into Claude:\n"
        "  1. PROMPT.md contents\n"
        "  2. The context output above (Step 4)\n"
        "  3. SESSION.md contents\n\n"
        "Claude must output its four answers before teaching.\n"
        "Check them against the correct answers above.\n"
        "If any answer is wrong or vague: stop, repaste, reverify."
    )
    print("=" * 58)

    conn.close()


# ─────────────────────────────────────────────
# MAIN — fixed order, no skipping
# ─────────────────────────────────────────────

def main():
    banner("MALLOC-TRAINING — SESSION START")
    print("Running all pre-session checks in fixed order.")
    print("Do not interrupt. Do not run steps separately.")

    # Step 1 — mood (exits if CRITICAL or declined)
    step_mood()

    # Step 2 — db integrity (exits if errors)
    step_db_check()

    # Step 3 — validation debt gate
    validation_ok = step_validation_gate()

    # Step 4 — context (hides next project if debt active)
    step_context(validation_ok)

    # Step 5 — machine-checked verification answers
    step_verification()


main()
