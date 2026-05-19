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

def store_handout():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 40)
    print("STORE LAB HANDOUT EXTRACTION")
    print("=" * 40)

    course = input("Course name: ")
    lab = input("Lab name: ")
    functions = get_multiline("Functions to implement:")
    grading = get_multiline("Grading criteria:")
    autograder = get_multiline("Autograder behavior:")
    constraints = get_multiline("Critical constraints:")
    edges = get_multiline("Edge cases:")
    tools = get_multiline("Required tools:")
    hardest = get_multiline("Hardest concept:")
    chapters = get_multiline("Book chapters:")
    raw = get_multiline("Full raw extraction:")

    c.execute('''INSERT INTO lab_handouts
                 (course, lab, functions_to_implement,
                  grading_criteria, autograder_behavior,
                  critical_constraints, edge_cases,
                  required_tools, hardest_concept,
                  book_chapters, raw_extraction)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (course, lab, functions, grading,
               autograder, constraints, edges,
               tools, hardest, chapters, raw))

    conn.commit()
    conn.close()
    print(f"\nHandout stored for {course} — {lab}")
    print("git add . && git commit -m 'Store handout' && git push")

store_handout()
