import sqlite3
import os
import sys

from prompts import ask_choice, ask_int, ask_multiline, ask_text


def require_table(c, name):
    """Tables come from schema.sql — stop if this database predates it."""
    c.execute("SELECT 1 FROM sqlite_master "
              "WHERE type = 'table' AND name = ?", (name,))
    if not c.fetchone():
        print(f"{name} table missing. Run: python3 init_db.py")
        sys.exit(1)


def validate():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check before asking anything, so no answers are lost
    require_table(c, 'external_validation')

    print("=" * 50)
    print("EXTERNAL CONCEPT VALIDATION")
    print("=" * 50)
    print(
        "Source must be EXTERNAL.\n"
        "Valid: CS:APP practice problem, K&R exercise,\n"
        "       old CMU 15-213 exam question.\n"
        "Invalid: anything Claude wrote, anything you wrote.\n"
    )

    # Show owned concepts not yet externally validated
    c.execute(
        '''SELECT con.name, con.project_number
           FROM concepts con
           LEFT JOIN external_validation ev
           ON ev.concept = con.name
           AND ev.project_number = con.project_number
           AND ev.result = 'pass'
           WHERE con.status = 'owned'
           AND ev.id IS NULL
           ORDER BY con.project_number''')
    unvalidated = c.fetchall()

    if unvalidated:
        print("Concepts owned but NOT yet externally validated:")
        for i, u in enumerate(unvalidated, 1):
            print(f"  {i}. {u[0]} (Project {u[1]})")
        print()
    else:
        print("All owned concepts are externally validated.\n")

    # Pick by number so the name matches the concepts table exactly
    choice = ask_text(
        "Concept being validated (list number, or type the name): ")
    if choice.isdigit() and 1 <= int(choice) <= len(unvalidated):
        concept, project_num = unvalidated[int(choice) - 1]
        print(f"  → {concept} (Project {project_num})")
    else:
        concept     = choice
        project_num = ask_int("Project number when learned: ", 1)
    source      = ask_text(
        "Source (e.g. CS:APP 9.9.12, K&R Ex 5.3, "
        "CMU F23 Exam 2 Q4): ")

    question    = ask_multiline("\nPaste the question.")
    your_answer = ask_multiline(
        "\nAttempt your answer WITHOUT any help.\n"
        "No Claude. No book. From your head only.")
    correct     = ask_multiline(
        "\nPaste the correct answer from the source.")

    result = ask_choice("\nResult — did your answer match? (pass/fail): ",
                        ('pass', 'fail'))

    c.execute(
        '''INSERT INTO external_validation
           (concept, project_number, source,
            question, your_answer, correct_answer, result)
           VALUES (?,?,?,?,?,?,?)''',
        (concept, project_num, source,
         question, your_answer, correct, result))

    if result == 'fail':
        print(
            f"\nConcept '{concept}' did NOT pass external validation.\n"
            f"Downgrading status from 'owned' to 'cracked'."
        )
        c.execute(
            '''UPDATE concepts SET status = 'cracked'
               WHERE name = ? AND project_number = ?''',
            (concept, project_num))
        print(
            "Claude will see this crack at next session start.\n"
            "The concept re-enters the curriculum."
        )
    else:
        print(
            f"\nConcept '{concept}' PASSED external validation.\n"
            f"This is the only confirmation that actually matters."
        )

    conn.commit()
    conn.close()

    print(
        "\nValidation recorded.\n"
        "git add . && git commit -m "
        f"'External validation: {concept}' && git push"
    )


validate()
