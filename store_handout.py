import sqlite3
import os

from prompts import ask_multiline, ask_text

def store_handout():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 40)
    print("STORE LAB HANDOUT EXTRACTION")
    print("=" * 40)

    course = ask_text("Course name: ")
    lab = ask_text("Lab name: ")
    functions = ask_multiline("Functions to implement:")
    grading = ask_multiline("Grading criteria:")
    autograder = ask_multiline("Autograder behavior:")
    constraints = ask_multiline("Critical constraints:")
    edges = ask_multiline("Edge cases:")
    tools = ask_multiline("Required tools:")
    hardest = ask_multiline("Hardest concept:")
    chapters = ask_multiline("Book chapters:")
    raw = ask_multiline("Full raw extraction:")

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
