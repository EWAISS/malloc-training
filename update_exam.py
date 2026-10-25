import sqlite3
import os

from prompts import ask_int, ask_multiline, ask_text, ask_yes_no

def update_transfer_exam():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 40)
    print("TRANSFER EXAM UPDATE")
    print("=" * 40)

    phase = ask_int("Phase (1-5): ", 1, 5)
    lab = ask_text("Lab name: ")
    course = ask_text("Course name: ")
    scenario = ask_multiline("Exam scenario:")
    implementation = ask_multiline("Your implementation:")
    evaluation = ask_multiline("Claude evaluation:")
    gaps = ask_text("Gaps found (or 'none'): ")
    adversarial = ask_multiline("Adversarial gap report:")
    status = ask_text("Status (passed/failed): ")

    c.execute('''INSERT INTO transfer_exams
                 (phase, lab, course, exam_scenario,
                  your_implementation, evaluation,
                  gaps_found, adversarial_gap_report,
                  status)
                 VALUES (?,?,?,?,?,?,?,?,?)''',
              (phase, lab, course, scenario,
               implementation, evaluation,
               gaps, adversarial, status))

    conn.commit()
    conn.close()
    print("Transfer exam recorded.")

def update_adversarial_exam():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 40)
    print("ADVERSARIAL EXAM UPDATE")
    print("=" * 40)

    phase = ask_int("Phase (1-5): ", 1, 5)
    lab = ask_text("Lab name: ")
    course = ask_text("Course name: ")
    concepts = ask_text("Concepts tested: ")
    questions = ask_multiline("Questions asked:")
    answers = ask_multiline("Your answers:")
    gap_found = 'yes' if ask_yes_no("Gap found (yes/no): ") else 'no'
    gap_location = ask_text("Gap location: ")
    # Unresolved gaps must be 'pending' so resolve_gap.py finds them
    resolved = 'yes' if ask_yes_no("Resolved (yes/no): ") else 'pending'

    c.execute('''INSERT INTO adversarial_exams
                 (phase, lab, course, concepts_tested,
                  questions_asked, your_answers,
                  gap_found, gap_location, resolved)
                 VALUES (?,?,?,?,?,?,?,?,?)''',
              (phase, lab, course, concepts,
               questions, answers, gap_found,
               gap_location, resolved))

    conn.commit()
    conn.close()
    print("Adversarial exam recorded.")

print("1. Transfer exam")
print("2. Adversarial exam")
if ask_int("Which? (1/2): ", 1, 2) == 1:
    update_transfer_exam()
else:
    update_adversarial_exam()
