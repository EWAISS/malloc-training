"""
resolve_gap.py
Marks an adversarial exam gap as resolved.
Run after repairing a gap identified by adversary.py.
Updates adversarial_exams.resolved from 'pending' to 'yes'.
"""

import sqlite3
import os
import sys

from prompts import ask_int, ask_multiline, ask_text, ask_yes_no

DB_PATH = os.path.expanduser('~/projects/malloc-training/brain.db')


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

    # Re-ask until the ID is one of the pending gaps listed above
    while True:
        gap_id = ask_int("Enter gap ID to resolve: ", 1)
        c.execute(
            '''SELECT id, phase, lab, gap_location
               FROM adversarial_exams
               WHERE id = ? AND resolved = 'pending' ''',
            (gap_id,))
        gap = c.fetchone()
        if gap:
            break
        print(f"  Gap ID {gap_id} is not pending. Pick an ID listed above.")

    print(f"\nResolving gap:")
    print(f"  Phase {gap[1]} | {gap[2]}")
    print(f"  Gap: {gap[3]}")

    how_resolved = ask_multiline(
        "\nHow was this gap repaired? "
        "(which project, which analogy, what clicked):")

    if not ask_yes_no("\nMark this gap as resolved? (yes/no): "):
        print("Cancelled.")
        conn.close()
        return

    # Also log to weakness_patterns if not already there
    pattern = None
    if ask_yes_no("\nLog repair as weakness pattern? (yes/no): "):
        pattern = (ask_text("Concept: "),
                   ask_text("Specific misconception: "),
                   ask_text("Analogy that clicked: "),
                   ask_text("Exact wording that clicked: "),
                   ask_text("Watch for recurrence: "),
                   ask_int("Project number where it resolved: ", 1))

    # Everything is collected — write it all or nothing
    with conn:
        c.execute(
            '''UPDATE adversarial_exams
               SET resolved = 'yes', resolution = ?
               WHERE id = ?''',
            (how_resolved, gap_id))
        if pattern:
            c.execute(
                '''INSERT INTO weakness_patterns
                   (concept, specific_misconception,
                    exact_analogy_that_clicked,
                    exact_wording_that_clicked,
                    watch_for_recurrence,
                    project_number)
                   VALUES (?,?,?,?,?,?)''',
                pattern)
    conn.close()

    print(f"\nGap ID {gap_id} marked as resolved.")
    print(
        "\ngit add . && git commit -m "
        f"'Gap resolved: Phase {gap[1]} {gap[2]}' && git push")


resolve_gap()
