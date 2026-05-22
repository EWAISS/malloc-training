"""
start_session.py
Single entry point for every session.
Runs in fixed order — cannot be skipped or reordered.
STEP 1: Mood check (behavioral facts)
STEP 2: Database integrity check
STEP 3: Validation debt gate
STEP 4: Context generation (last 5 projects)
STEP 5: Machine-checked verification answers

FIXES vs previous version:
- step_context: pulls last 5 projects, not 1
- step_context: surfaces cross-lab weakness patterns
- step_verification: joins concepts table for accurate struggled_with
- step_verification: writes correct answers to verification.txt
  so they survive terminal close
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
# STEP 3 — VALIDATION DEBT GATE
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
        return True

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
        return False
    else:
        if total_projects > 0:
            print(
                f"Validation rate OK — "
                f"{total_validated}/{required} required validations done.")
        return True


# ─────────────────────────────────────────────
# STEP 4 — CONTEXT GENERATION
# FIX: pulls last 5 projects (was 1)
# FIX: surfaces cross-lab weakness patterns
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

    # ── LAST 5 PROJECTS (was LIMIT 1) ───────────
    c.execute(
        '''SELECT number, name, concept, status,
                  what_failed, handoff, phase
           FROM projects
           ORDER BY number DESC LIMIT 5''')
    last_five = c.fetchall()
    last = last_five[0]  # most recent

    print(f"\nPhase  : {last[6]}")

    if validation_ok:
        print(f"Next project   : {last[0] + 1}")
    else:
        print(f"Next project   : HIDDEN — clear validation debt first")

    print(f"\nLAST 5 PROJECTS:")
    for p in last_five:
        print(f"\n  Project {p[0]} — {p[1]}")
        print(f"  Concept : {p[2]} | Status: {p[3]}")
        print(f"  Failed  : {p[4]}")
        if p[5]:
            print(f"  Handoff : {p[5]}")

    # ── MOST RECENT HANDOFF ──────────────────────
    if last[5]:
        print(f"\nACTIVE HANDOFF (Project {last[0]}):\n{last[5]}")

    # ── OWNED CONCEPTS — current lab (last 5) ───
    c.execute(
        '''SELECT c.name, c.how_it_clicked
           FROM concepts c
           JOIN projects p ON p.number = c.project_number
           WHERE p.lab = ? AND c.status = 'owned'
           ORDER BY c.project_number DESC LIMIT 5''',
        (active_lab,))
    owned = c.fetchall()
    if owned:
        print(f"\nRECENT OWNED CONCEPTS ({active_lab}):")
        for o in owned:
            print(f"  — {o[0]}: {o[1]}")

    # ── CROSS-LAB WEAKNESS PATTERNS ─────────────
    # FIX: was missing from step_context entirely
    c.execute(
        '''SELECT wp.concept,
                  wp.specific_misconception,
                  wp.watch_for_recurrence,
                  p.lab
           FROM weakness_patterns wp
           JOIN projects p ON p.number = wp.project_number
           ORDER BY wp.project_number DESC LIMIT 5''')
    weaknesses = c.fetchall()
    if weaknesses:
        print(f"\nACTIVE WEAKNESS PATTERNS (cross-lab):")
        for w in weaknesses:
            print(f"  — [{w[3]}] {w[0]}: {w[2]}")
            if w[1]:
                print(f"    Misconception: {w[1]}")

    # ── EXTERNAL VALIDATION STATUS ───────────────
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

    # ── MIND MODEL ───────────────────────────────
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
# STEP 5 — MACHINE-CHECKED VERIFICATION
# FIX: joins concepts table for accurate struggled_with
# FIX: writes correct answers to verification.txt
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

    # FIX: join concepts for accurate struggled_with
    # (was using what_failed from projects as proxy)
    c.execute(
        '''SELECT p.number, p.name, p.concept,
                  con.struggled_with, p.handoff
           FROM projects p
           LEFT JOIN concepts con
               ON con.project_number = p.number
               AND con.name = p.concept
           WHERE p.lab = ?
           ORDER BY p.number DESC LIMIT 1''',
        (active_lab,))
    last = c.fetchone()

    c.execute(
        '''SELECT concept, watch_for_recurrence
           FROM weakness_patterns
           ORDER BY project_number DESC LIMIT 1''')
    weakness = c.fetchone()

    # Build answer block
    lines = []
    lines.append("=" * 58)
    lines.append("CONTEXT VERIFICATION — CORRECT ANSWERS")
    lines.append("Generated: " + datetime.now().strftime(
        '%Y-%m-%d %H:%M'))
    lines.append("=" * 58)
    lines.append("")
    lines.append("Keep this visible. After Claude answers, "
                 "compare line by line.")
    lines.append("Vague or wrong answer = repaste context, "
                 "verify again.")
    lines.append("")
    lines.append("─" * 58)

    if last:
        lines.append(f"Q1 Last concept    : {last[2]}")
        lines.append(f"Q2 Struggled with  : "
                     f"{last[3] or '(none recorded)'}")
        lines.append(f"Q3 Handoff says    : "
                     f"{last[4] or '(none recorded)'}")
    else:
        lines.append("Q1 Last concept    : (no projects yet)")
        lines.append("Q2 Struggled with  : (no projects yet)")
        lines.append("Q3 Handoff says    : (no projects yet)")

    if weakness:
        lines.append(f"Q4 Active weakness : "
                     f"{weakness[0]} — {weakness[1]}")
    else:
        lines.append("Q4 Active weakness : (none recorded yet)")

    lines.append("─" * 58)
    lines.append("")
    lines.append("Now paste into Claude:")
    lines.append("  1. PROMPT.md contents")
    lines.append("  2. The context output above (Step 4)")
    lines.append("  3. SESSION.md contents")
    lines.append("")
    lines.append("Claude must output its four answers before teaching.")
    lines.append("Check them against the correct answers above.")
    lines.append("If any answer is wrong or vague: stop, repaste, "
                 "reverify.")
    lines.append("=" * 58)

    output = "\n".join(lines)

    # Print to terminal
    print(output)

    # FIX: also write to file so answers survive terminal close
    verify_path = os.path.join(PROJ, 'verification.txt')
    try:
        with open(verify_path, 'w') as f:
            f.write(output + "\n")
        print(f"\nAnswers also saved to: verification.txt")
    except Exception as e:
        print(f"\nWarning: Could not write verification.txt: {e}")

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

    # Step 4 — context: last 5 projects + cross-lab weaknesses
    step_context(validation_ok)

    # Step 5 — machine-checked verification answers
    step_verification()


main()
