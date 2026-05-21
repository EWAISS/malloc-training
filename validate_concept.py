import sqlite3
import os
import sys


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


def validate():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Ensure table exists
    c.execute(
        '''CREATE TABLE IF NOT EXISTS external_validation (
            id INTEGER PRIMARY KEY,
            concept TEXT,
            project_number INTEGER,
            source TEXT,
            question TEXT,
            your_answer TEXT,
            correct_answer TEXT,
            result TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    conn.commit()

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
           WHERE con.status = 'owned'
           AND ev.id IS NULL
           ORDER BY con.project_number''')
    unvalidated = c.fetchall()

    if unvalidated:
        print("Concepts owned but NOT yet externally validated:")
        for u in unvalidated:
            print(f"  — {u[0]} (Project {u[1]})")
        print()
    else:
        print("All owned concepts are externally validated.\n")

    concept     = input("Concept being validated: ").strip()
    project_num = int(input("Project number when learned: "))
    source      = input(
        "Source (e.g. CS:APP 9.9.12, K&R Ex 5.3, "
        "CMU F23 Exam 2 Q4): ").strip()

    question    = get_multiline("\nPaste the question.")
    your_answer = get_multiline(
        "\nAttempt your answer WITHOUT any help.\n"
        "No Claude. No book. From your head only.")
    correct     = get_multiline(
        "\nPaste the correct answer from the source.")

    result = input("\nResult — did your answer match? (pass/fail): "
                   ).strip().lower()

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
