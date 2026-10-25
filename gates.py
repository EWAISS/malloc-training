"""
gates.py — every session gate, in one place.

context.py, start_session.py and db_check.py all call these, so they
can never disagree about whether a gate is shut.

  missing_adversarial_reports — transfer exams still owed an adversary.py
                                report (blocks the session)
  gap_gate                    — > 7 days since the last project or last
                                cleared spaced-repetition quiz
  validation_debt             — 2 passed external validations per 10
                                projects
  next_project_hidden         — either of the last two hides the next
                                project number everywhere
  missing_lab_transitions     — finished labs with 10+ projects and no
                                transition summary
"""
from datetime import datetime, timezone

from db import lab_key

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

GAP_DAYS = 7
VALIDATIONS_PER_10 = 2
TRANSITION_MIN_PROJECTS = 10


def elapsed_since(timestamp):
    """Time since a CURRENT_TIMESTAMP value (stored as UTC)."""
    last = datetime.fromisoformat(timestamp)
    if HAS_PYTZ:
        cairo = pytz.timezone('Africa/Cairo')
        return datetime.now(cairo) - \
            last.replace(tzinfo=pytz.utc).astimezone(cairo)
    # No pytz: compare UTC with UTC
    return datetime.now(timezone.utc).replace(tzinfo=None) - last


# ─────────────────────────────────────────────
# ADVERSARIAL GATE
# ─────────────────────────────────────────────

def missing_adversarial_reports(c):
    """(phase, lab) of every transfer exam without a gap report.
    The schema stores a missing report as NULL and nothing else."""
    c.execute('''SELECT phase, lab FROM transfer_exams
                 WHERE adversarial_gap_report IS NULL
                 ORDER BY completed_at''')
    return c.fetchall()


def print_adversarial_block(missing, rerun):
    print("=" * 60)
    print("BLOCKED — ADVERSARIAL EXAM NOT COMPLETED")
    print("=" * 60)
    for phase, lab in missing:
        print(f"Phase {phase} | {lab}")
    print(
        "Transfer exam has no adversarial gap report.\n\n"
        "Run:  python3 adversary.py\n"
        f"Complete it, then re-run {rerun}."
    )
    print("=" * 60)


# ─────────────────────────────────────────────
# GAP GATE
# ─────────────────────────────────────────────

def gap_gate(c):
    """Days since the last activity if the gap gate is shut, else None.
    A passed spaced repetition quiz counts as activity."""
    c.execute('''SELECT completed_at FROM projects
                 ORDER BY number DESC LIMIT 1''')
    row = c.fetchone()
    if not row or not row[0]:
        return None
    last_activity = row[0]

    c.execute('SELECT MAX(cleared_at) FROM gap_gate_clears')
    cleared = c.fetchone()[0]
    if cleared and cleared > last_activity:
        last_activity = cleared

    try:
        days = elapsed_since(last_activity).days
    except ValueError:
        return None
    return days if days > GAP_DAYS else None


def print_gap_gate(c, days):
    print("=" * 60)
    print(f"GAP GATE ACTIVE — {days} days since last project")
    print("=" * 60)
    print(
        "New material is locked.\n"
        "Before continuing, Claude must quiz these concepts:"
    )
    c.execute('''SELECT name FROM concepts
                 WHERE status = 'owned'
                 ORDER BY project_number DESC LIMIT 5''')
    for row in c.fetchall():
        print(f"  — {row[0]}")
    print(
        "\nTell Claude: 'Run spaced repetition quiz now.'\n"
        "After passing all 5, run:\n"
        "  python3 context.py --clear-gap-gate\n"
        "Curriculum position is hidden until gate clears."
    )
    print("=" * 60)


# ─────────────────────────────────────────────
# VALIDATION DEBT
# ─────────────────────────────────────────────

def validation_debt(c):
    """(projects, required, done, debt). Only passes for a recorded
    concept count."""
    c.execute('SELECT COUNT(*) FROM projects')
    total = c.fetchone()[0]
    c.execute('''SELECT COUNT(*) FROM external_validation ev
                 JOIN concepts con
                   ON con.name = ev.concept
                  AND con.project_number = ev.project_number
                 WHERE ev.result = 'pass' ''')
    done = c.fetchone()[0]
    required = (total // 10) * VALIDATIONS_PER_10
    return total, required, done, max(0, required - done)


def next_project_hidden(c):
    """Why the next project number must not be shown, or None."""
    if gap_gate(c) is not None:
        return "gap gate active"
    if validation_debt(c)[3] > 0:
        return "clear validation debt first"
    return None


# ─────────────────────────────────────────────
# LAB TRANSITIONS
# ─────────────────────────────────────────────

def missing_lab_transitions(c, active_lab):
    """Labs with 10+ projects and no transition summary, except the
    active lab — it is still in progress."""
    c.execute(
        '''SELECT p.lab
           FROM projects p
           LEFT JOIN lab_transitions lt ON lt.lab = p.lab
           WHERE lt.id IS NULL AND p.lab IS NOT NULL
           GROUP BY p.lab
           HAVING COUNT(p.id) >= ?''', (TRANSITION_MIN_PROJECTS,))
    return [row[0] for row in c.fetchall()
            if lab_key(row[0]) != lab_key(active_lab)]
