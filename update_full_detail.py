"""
update_full_detail.py
Writes to project_full_detail and quiz_records tables.
Run this AFTER update.py for every project.
Captures: micro-projects, quiz questions/answers,
exact failure/success moments, memory model evolution,
and all quiz records with novel question tracking.
"""

import sqlite3
import os
import sys

from prompts import (ask_choice, ask_int, ask_multiline, ask_text,
                     ask_yes_no)

DB_PATH = os.path.expanduser('~/projects/malloc-training/brain.db')
PROJ    = os.path.expanduser('~/projects/malloc-training')


def get_db():
    return sqlite3.connect(DB_PATH)


def update_full_detail():
    conn = get_db()
    c = conn.cursor()

    print("=" * 55)
    print("POST-PROJECT FULL DETAIL UPDATE")
    print("=" * 55)
    print("Run this after update.py.")
    print("Captures quiz records and session detail.\n")

    number = ask_int("Project number: ", 1)

    # Verify project exists
    c.execute('SELECT name, concept, lab, course FROM projects '
              'WHERE number = ?', (number,))
    project = c.fetchone()
    if not project:
        print(f"ERROR: Project {number} not found in database.")
        print("Run update.py first.")
        conn.close()
        sys.exit(1)

    name, concept, lab, course = project
    print(f"\nProject {number} — {name}")
    print(f"Concept: {concept}\n")

    # Check if full detail already exists
    c.execute('SELECT id FROM project_full_detail '
              'WHERE project_number = ?', (number,))
    existing = c.fetchone()
    if existing:
        if not ask_yes_no(
                "Full detail already exists. Replace? (yes/no): "):
            conn.close()
            return
        c.execute('DELETE FROM project_full_detail '
                  'WHERE project_number = ?', (number,))

    # ── FULL DETAIL ──────────────────────────────
    print("\n--- PROJECT FULL DETAIL ---")

    full_spec = ask_multiline(
        "\nFull project specification as given by Claude:")

    micro = ask_multiline(
        "\nMicro-projects generated (or 'none'):")

    all_questions = ask_multiline(
        "\nAll quiz questions asked:")

    all_answers = ask_multiline(
        "\nAll your quiz answers:")

    failures = ask_multiline(
        "\nExact failure moments — what broke, what you said:")

    successes = ask_multiline(
        "\nExact success moments — what clicked and when:")

    memory_evolution = ask_multiline(
        "\nHow your memory model evolved this project:")

    c.execute(
        '''INSERT INTO project_full_detail
           (project_number, full_specification,
            micro_projects_generated,
            all_quiz_questions, all_quiz_answers,
            exact_failure_moments, exact_success_moments,
            memory_model_evolution)
           VALUES (?,?,?,?,?,?,?,?)''',
        (number, full_spec, micro,
         all_questions, all_answers,
         failures, successes, memory_evolution))

    print("\nFull detail saved.")

    # ── QUIZ RECORDS ─────────────────────────────
    print("\n--- QUIZ RECORDS ---")
    print("Enter each quiz question individually.")
    print("Press Enter with empty question to stop.\n")

    question_num = 1
    while True:
        print(f"Question {question_num}:")
        q_text = ask_text("  Question text (or Enter to stop): ")
        if not q_text:
            break

        your_answer = ask_text("  Your answer: ")
        evaluation  = ask_choice(
            "  Evaluation (correct/partial/wrong): ",
            ('correct', 'partial', 'wrong'))
        result      = ask_choice("  Result (pass/fail): ",
                                 ('pass', 'fail'))
        is_novel_int = 1 if ask_yes_no(
            "  Novel question? Never asked before? (yes/no): ") else 0

        c.execute(
            '''INSERT INTO quiz_records
               (project_number, question_number,
                question_text, your_answer,
                evaluation, is_novel_question,
                result, concept, lab, course)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (number, question_num, q_text,
             your_answer, evaluation,
             is_novel_int, result,
             concept, lab, course))

        print(f"  Question {question_num} saved.\n")
        question_num += 1

    conn.commit()
    conn.close()

    print(f"\nFull detail and {question_num - 1} quiz records saved.")
    print(f"Project {number} is now fully documented.")
    print(
        f"\ngit add . && git commit -m "
        f"'Full detail: Project {number}' && git push")


update_full_detail()
