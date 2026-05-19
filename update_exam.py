import sqlite3
import os

def get_multiline(prompt):
    print(prompt)
    print("Type END on new line when done:")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def update_transfer_exam():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 40)
    print("TRANSFER EXAM UPDATE")
    print("=" * 40)

    phase = int(input("Phase (1-5): "))
    lab = input("Lab name: ")
    course = input("Course name: ")
    scenario = get_multiline("Exam scenario:")
    implementation = get_multiline("Your implementation:")
    evaluation = get_multiline("Claude evaluation:")
    gaps = input("Gaps found (or 'none'): ")
    adversarial = get_multiline("Adversarial gap report:")
    status = input("Status (passed/failed): ")

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

    phase = int(input("Phase (1-5): "))
    lab = input("Lab name: ")
    course = input("Course name: ")
    concepts = input("Concepts tested: ")
    questions = get_multiline("Questions asked:")
    answers = get_multiline("Your answers:")
    gap_found = input("Gap found (yes/no): ")
    gap_location = input("Gap location: ")
    resolved = input("Resolved (yes/no): ")

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
choice = input("Which? (1/2): ")
if choice == "1":
    update_transfer_exam()
else:
    update_adversarial_exam()
