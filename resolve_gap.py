"""
resolve_gap.py
Marks an adversarial exam gap as resolved.
Run after repairing a gap identified by adversary.py.
Updates adversarial_exams.resolved from 'pending' to 'yes'.
"""

import sqlite3
import os
import sys

DB_PATH = os.path.expanduser('~/projects/malloc-training/brain.db')


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


def resolve_gap():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("=" * 55)
    print("GAP RESOLUTION")
    print("=" * 55)

    # Show all pending gaps
    c.execute(
        '''SELECT id, phase, lab, gap_location, completed_at
           FROM adversarial_exams
           WHERE resolved = 'pending'
           ORDER BY completed_at DESC''')
    pending = c.fetchall()

    if not pending:
        print("\nNo pending gaps found.")
        print("All adversarial exam gaps are resolved.")
        conn.close()
        return

    print(f"\nPENDING GAPS ({len(pending)} unresolved):\n")
    for p in pending:
        print(f"  ID {p[0]} — Phase {p[1]} | {p[2]}")
        print(f"  Gap: {p[3]}")
        print(f"  Found: {p[4]}")
        print()

    gap_id = int(input("Enter gap ID to resolve: "))

    # Verify it exists and is pending
    c.execute(
        '''SELECT id, phase, lab, gap_location
           FROM adversarial_exams
           WHERE id = ? AND resolved = 'pending' ''',
        (gap_id,))
    gap = c.fetchone()

    if not gap:
        print(f"\nERROR: Gap ID {gap_id} not found or already resolved.")
        conn.close()
        return

    print(f"\nResolving gap:")
    print(f"  Phase {gap[1]} | {gap[2]}")
    print(f"  Gap: {gap[3]}")

    how_resolved = get_multiline(
        "\nHow was this gap repaired? "
        "(which project, which analogy, what clicked):")

    confirm = input(
        "\nMark this gap as resolved? (yes/no): ").lower()
    if confirm != 'yes':
        print("Cancelled.")
        conn.close()
        return

    c.execute(
        '''UPDATE adversarial_exams
           SET resolved = 'yes'
           WHERE id = ?''',
        (gap_id,))

    # Also log to weakness_patterns if not already there
    log_pattern = input(
        "\nLog repair as weakness pattern? (yes/no): ").lower()
    if log_pattern == 'yes':
        concept    = input("Concept: ").strip()
        misconception = input("Specific misconception: ").strip()
        analogy    = input("Analogy that clicked: ").strip()
        wording    = input("Exact wording that clicked: ").strip()
        watch      = input("Watch for recurrence: ").strip()
        proj_num   = int(input("Project number where it resolved: "))

        c.execute(
            '''INSERT INTO weakness_patterns
               (concept, specific_misconception,
                exact_analogy_that_clicked,
                exact_wording_that_clicked,
                watch_for_recurrence,
                project_number)
               VALUES (?,?,?,?,?,?)''',
            (concept, misconception, analogy,
             wording, watch, proj_num))

    conn.commit()
    conn.close()

    print(f"\nGap ID {gap_id} marked as resolved.")
    print(
        "\ngit add . && git commit -m "
        f"'Gap resolved: Phase {gap[1]} {gap[2]}' && git push")


resolve_gap()
