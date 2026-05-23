"""
lab_transition.py
Run when you finish a lab and are about to start a new one.
Generates a transition summary prompt for Claude,
collects Claude's response, stores it in brain.db,
and appends it to LAB_HISTORY.md.

Run BEFORE changing ACTIVE LAB in SESSION.md.
"""

import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = os.path.expanduser('~/projects/malloc-training/brain.db')
PROJ    = os.path.expanduser('~/projects/malloc-training')


def get_multiline(prompt):
    print(prompt)
    print("Type END on a new line when done:")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def get_db():
    return sqlite3.connect(DB_PATH)


def ensure_table(c):
    c.execute('''CREATE TABLE IF NOT EXISTS lab_transitions (
        id INTEGER PRIMARY KEY,
        lab TEXT,
        course TEXT,
        concepts_owned TEXT,
        carried_forward TEXT,
        watch_for TEXT,
        key_analogy TEXT,
        full_summary TEXT,
        next_lab TEXT,
        transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')


def run_transition():
    conn = get_db()
    c = conn.cursor()
    ensure_table(c)
    conn.commit()

    print("=" * 60)
    print("LAB TRANSITION")
    print("=" * 60)
    print("Run this BEFORE changing ACTIVE LAB in SESSION.md.\n")

    # Get current lab from SESSION.md
    session_path = os.path.join(PROJ, 'SESSION.md')
    current_lab = "unknown"
    current_course = "unknown"
    try:
        with open(session_path) as f:
            for line in f:
                if line.startswith("ACTIVE LAB:"):
                    current_lab = line.split(":", 1)[1].strip()
                if line.startswith("ACTIVE COURSE:"):
                    current_course = line.split(":", 1)[1].strip()
    except Exception:
        pass

    print(f"Completing lab : {current_lab}")
    print(f"Course         : {current_course}")

    next_lab = input("\nNext lab name: ").strip()

    # Check if transition already exists
    c.execute(
        'SELECT id FROM lab_transitions WHERE lab = ?',
        (current_lab,))
    existing = c.fetchone()
    if existing:
        redo = input(
            f"Transition for {current_lab} already exists. "
            "Replace? (yes/no): ").lower()
        if redo != 'yes':
            conn.close()
            return
        c.execute(
            'DELETE FROM lab_transitions WHERE lab = ?',
            (current_lab,))

    # Pull owned concepts for this lab
    c.execute(
        '''SELECT con.name, con.how_it_clicked
           FROM concepts con
           JOIN projects p ON p.number = con.project_number
           WHERE p.lab = ? AND con.status = 'owned'
           ORDER BY con.project_number''',
        (current_lab,))
    owned = c.fetchall()

    # Pull weakness patterns for this lab
    c.execute(
        '''SELECT wp.concept, wp.watch_for_recurrence,
                  wp.exact_analogy_that_clicked
           FROM weakness_patterns wp
           JOIN projects p ON p.number = wp.project_number
           WHERE p.lab = ?
           ORDER BY wp.project_number''',
        (current_lab,))
    weaknesses = c.fetchall()

    # Pull project count
    c.execute(
        'SELECT COUNT(*) FROM projects WHERE lab = ?',
        (current_lab,))
    project_count = c.fetchone()[0]

    # Build the prompt for Claude
    owned_str = "\n".join(
        f"- {o[0]}: {o[1]}" for o in owned) if owned else "none"
    weakness_str = "\n".join(
        f"- {w[0]}: watch for {w[1]}, analogy: {w[2]}"
        for w in weaknesses) if weaknesses else "none"

    print("\n" + "=" * 60)
    print("PASTE THIS INTO CLAUDE PROJECT NOW:")
    print("=" * 60)
    print(f"""
Generate a lab transition summary for {current_lab}.

Student completed {project_count} projects in this lab.

Concepts owned:
{owned_str}

Weakness patterns:
{weakness_str}

Next lab: {next_lab}

Format exactly:
LAB: {current_lab} | COURSE: {current_course}
OWNED: [top 5 concepts comma separated]
CARRIED FORWARD: [what transfers to {next_lab} specifically]
WATCH FOR: [top weakness patterns to remember]
KEY ANALOGY: [the one analogy that worked best]
SUMMARY: [one paragraph connecting this lab to the next]

Be specific to this student's actual performance.
Reference the weakness patterns above.
Connect explicitly to what {next_lab} will require.
""")
    print("=" * 60)

    summary = get_multiline(
        "\nPaste Claude's transition summary:")

    if not summary.strip():
        print("ERROR: No summary provided. Transition not recorded.")
        conn.close()
        return

    # Parse the summary fields
    concepts_owned = ""
    carried_forward = ""
    watch_for = ""
    key_analogy = ""

    for line in summary.split('\n'):
        if line.startswith('OWNED:'):
            concepts_owned = line.split(':', 1)[1].strip()
        elif line.startswith('CARRIED FORWARD:'):
            carried_forward = line.split(':', 1)[1].strip()
        elif line.startswith('WATCH FOR:'):
            watch_for = line.split(':', 1)[1].strip()
        elif line.startswith('KEY ANALOGY:'):
            key_analogy = line.split(':', 1)[1].strip()

    # Store in database
    c.execute(
        '''INSERT INTO lab_transitions
           (lab, course, concepts_owned, carried_forward,
            watch_for, key_analogy, full_summary, next_lab)
           VALUES (?,?,?,?,?,?,?,?)''',
        (current_lab, current_course,
         concepts_owned, carried_forward,
         watch_for, key_analogy, summary, next_lab))

    conn.commit()
    conn.close()

    # Append to LAB_HISTORY.md
    lab_history_path = os.path.join(PROJ, 'LAB_HISTORY.md')
    try:
        with open(lab_history_path, 'a') as f:
            f.write(f"\n\n# Completed: "
                    f"{datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(summary)
            f.write("\n")
        print(f"\nAppended to LAB_HISTORY.md.")
    except Exception as e:
        print(f"\nWarning: Could not write LAB_HISTORY.md: {e}")

    print(f"\nLab transition recorded: {current_lab} → {next_lab}")
    print("\nNEXT STEPS:")
    print("1. Re-upload LAB_HISTORY.md to Claude Project")
    print("2. Update SESSION.md: change ACTIVE LAB and ACTIVE COURSE")
    print("3. Run start_session.py to verify")
    print(
        f"\ngit add . && git commit -m "
        f"'Lab transition: {current_lab} → {next_lab}' && git push")


run_transition()
