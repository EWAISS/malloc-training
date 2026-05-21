import sqlite3
import os
import sys


def run_adversarial():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get last transfer exam
    c.execute(
        '''SELECT id, phase, lab, course,
                  adversarial_gap_report
           FROM transfer_exams
           ORDER BY completed_at DESC LIMIT 1''')
    exam = c.fetchone()

    if not exam:
        print("No transfer exam found.")
        print("Complete a phase transfer exam first.")
        conn.close()
        return

    exam_id   = exam[0]
    phase     = exam[1]
    lab       = exam[2]
    course    = exam[3]
    existing  = exam[4]

    if existing and existing.strip() not in ('', 'none'):
        print(f"Phase {phase} {lab} already has an adversarial report.")
        redo = input("Replace it? (yes/no): ").lower()
        if redo != 'yes':
            conn.close()
            return

    # Get all concepts owned in this lab
    c.execute(
        '''SELECT DISTINCT con.name
           FROM concepts con
           JOIN projects p ON p.number = con.project_number
           WHERE p.lab = ? AND con.status = 'owned'
           ORDER BY con.project_number''',
        (lab,))
    concepts = [row[0] for row in c.fetchall()]

    if not concepts:
        print("No owned concepts found for this lab.")
        conn.close()
        return

    concepts_str = "\n".join(f"- {con}" for con in concepts)

    print("\n" + "=" * 60)
    print(f"ADVERSARIAL EXAM — Phase {phase} | {lab} | {course}")
    print("=" * 60)
    print("\nStep 1: Open a NEW Claude conversation (new tab/window).")
    print("Step 2: Paste EXACTLY the prompt below.")
    print("Step 3: Answer the adversary's questions from first principles.")
    print("Step 4: When the adversary reports the gap, paste it here.")
    print("\n" + "─" * 60)
    print("PASTE THIS INTO THE NEW CONVERSATION:\n")
    print(
        f"You are an adversarial examiner. Your only job is to find\n"
        f"the exact gap in this student's understanding.\n\n"
        f"The student claims to understand these concepts:\n"
        f"{concepts_str}\n\n"
        f"Rules:\n"
        f"- Do not teach. Do not explain. Do not encourage.\n"
        f"- Ask questions that cannot be answered from memory alone.\n"
        f"- Every answer must be derived from first principles.\n"
        f"- Push until you find the exact crack.\n"
        f"- End with exactly one sentence: the precise location of the gap.\n\n"
        f"Start immediately with your first question."
    )
    print("─" * 60)

    input("\nPress ENTER when you have finished the adversarial session...")

    print("\nPaste the adversary's final gap report (one sentence).")
    print("Type END on a new line when done:")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    gap_report = "\n".join(lines).strip()

    if not gap_report:
        print("\nERROR: No gap report provided. Exam not recorded.")
        conn.close()
        return

    # Write gap report to transfer_exams
    c.execute(
        '''UPDATE transfer_exams
           SET adversarial_gap_report = ?
           WHERE id = ?''',
        (gap_report, exam_id))

    # Write to adversarial_exams table
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

    c.execute(
        '''INSERT INTO adversarial_exams
           (phase, lab, course, concepts_tested,
            gap_found, gap_location, resolved)
           VALUES (?,?,?,?,?,?,?)''',
        (phase, lab, course, concepts_str,
         'yes', gap_report, 'pending'))

    conn.commit()
    conn.close()

    print("\nAdversarial exam recorded.")
    print("The gap must be repaired before phase progression.")
    print(f"\nGAP IDENTIFIED:\n  {gap_report}")
    print(
        "\ngit add . && git commit -m "
        f"'Adversarial exam Phase {phase} {lab} complete' && git push")


run_adversarial()
