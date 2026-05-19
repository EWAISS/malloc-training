import sqlite3
import os
import sys

def query_project(number):
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print(f"=" * 60)
    print(f"FULL DETAIL — PROJECT {number}")
    print(f"=" * 60)

    c.execute('''SELECT name, phase, lab, course,
                        concept, status, what_worked,
                        what_failed, final_code, handoff,
                        code_review, appears_in_future_labs
                 FROM projects WHERE number = ?''',
              (number,))
    p = c.fetchone()
    if not p:
        print(f"Project {number} not found.")
        conn.close()
        return

    print(f"\nName    : {p[0]}")
    print(f"Phase   : {p[1]} | Lab: {p[2]} | Course: {p[3]}")
    print(f"Concept : {p[4]} | Status: {p[5]}")
    print(f"Worked  : {p[6]}")
    print(f"Failed  : {p[7]}")
    print(f"Handoff : {p[9]}")
    print(f"Review  : {p[10]}")
    print(f"Future  : {p[11]}")

    c.execute('''SELECT micro_projects_generated,
                        all_quiz_questions,
                        all_quiz_answers,
                        exact_failure_moments,
                        exact_success_moments,
                        memory_model_evolution
                 FROM project_full_detail
                 WHERE project_number = ?''', (number,))
    d = c.fetchone()
    if d:
        print(f"\nMICRO-PROJECTS:\n{d[0]}")
        print(f"\nQUIZ QUESTIONS:\n{d[1]}")
        print(f"\nQUIZ ANSWERS:\n{d[2]}")
        print(f"\nFAILURE MOMENTS:\n{d[3]}")
        print(f"\nSUCCESS MOMENTS:\n{d[4]}")
        print(f"\nMEMORY MODEL:\n{d[5]}")

    c.execute('''SELECT why_designed_this_way,
                        gap_it_closes,
                        what_response_revealed,
                        connection_to_lab,
                        what_breaks_without_this,
                        what_next_project_must_do
                 FROM project_narrative
                 WHERE project_number = ?''', (number,))
    n = c.fetchone()
    if n:
        print(f"\nDESIGN NARRATIVE:")
        print(f"Why      : {n[0]}")
        print(f"Gap      : {n[1]}")
        print(f"Revealed : {n[2]}")
        print(f"Connect  : {n[3]}")
        print(f"Without  : {n[4]}")
        print(f"Next must: {n[5]}")

    print(f"\nFINAL CODE:\n{p[8]}")
    print(f"\n" + "=" * 60)
    conn.close()

if len(sys.argv) > 1:
    query_project(int(sys.argv[1]))
else:
    number = int(input("Project number: "))
    query_project(number)
