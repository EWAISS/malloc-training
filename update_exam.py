from db import ask_lab, clean_report, connect
from prompts import ask_choice, ask_int, ask_multiline, ask_text, ask_yes_no

def update_transfer_exam():
    conn = connect()
    c = conn.cursor()

    print("=" * 40)
    print("TRANSFER EXAM UPDATE")
    print("=" * 40)

    phase = ask_int("Phase (1-5): ", 1, 5)
    lab, course = ask_lab(c, "Lab name")
    scenario = ask_multiline("Exam scenario:")
    implementation = ask_multiline("Your implementation:")
    evaluation = ask_multiline("Claude evaluation:")
    gaps = ask_text("Gaps found (or 'none'): ")
    # Blank or 'none' is stored as NULL: adversary.py still owes a report
    adversarial = clean_report(ask_multiline("Adversarial gap report:"))
    status = ask_choice("Status (passed/failed): ", ('passed', 'failed'))

    with conn:
        c.execute('''INSERT INTO transfer_exams
                     (phase, lab, course, exam_scenario,
                      your_implementation, evaluation,
                      gaps_found, adversarial_gap_report,
                      status)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (phase, lab, course, scenario,
                   implementation, evaluation,
                   gaps, adversarial, status))
    conn.close()
    print("Transfer exam recorded.")
    if adversarial is None:
        print("No adversarial report yet — run: python3 adversary.py")

def update_adversarial_exam():
    conn = connect()
    c = conn.cursor()

    print("=" * 40)
    print("ADVERSARIAL EXAM UPDATE")
    print("=" * 40)

    phase = ask_int("Phase (1-5): ", 1, 5)
    lab, course = ask_lab(c, "Lab name")
    concepts = ask_text("Concepts tested: ")
    questions = ask_multiline("Questions asked:")
    answers = ask_multiline("Your answers:")
    if ask_yes_no("Gap found (yes/no): "):
        gap_found = 'yes'
        gap_location = ask_text("Gap location: ")
        # Unresolved gaps must be 'pending' so resolve_gap.py finds them
        resolved = 'yes' if ask_yes_no("Resolved (yes/no): ") \
            else 'pending'
    else:
        # No gap: nothing for resolve_gap.py to resolve
        gap_found, gap_location, resolved = 'no', '', 'n/a'

    with conn:
        c.execute('''INSERT INTO adversarial_exams
                     (phase, lab, course, concepts_tested,
                      questions_asked, your_answers,
                      gap_found, gap_location, resolved)
                     VALUES (?,?,?,?,?,?,?,?,?)''',
                  (phase, lab, course, concepts,
                   questions, answers, gap_found,
                   gap_location, resolved))
    conn.close()
    print("Adversarial exam recorded.")

print("1. Transfer exam")
print("2. Adversarial exam")
if ask_int("Which? (1/2): ", 1, 2) == 1:
    update_transfer_exam()
else:
    update_adversarial_exam()
