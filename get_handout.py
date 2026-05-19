import sqlite3
import os
import sys

def get_handout(lab):
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''SELECT functions_to_implement,
                        grading_criteria,
                        critical_constraints,
                        hardest_concept,
                        edge_cases,
                        required_tools,
                        book_chapters
                 FROM lab_handouts
                 WHERE lab = ?
                 ORDER BY stored_at DESC LIMIT 1''',
              (lab,))
    h = c.fetchone()
    if not h:
        print(f"No handout stored for: {lab}")
        conn.close()
        return

    print("=" * 50)
    print(f"HANDOUT — {lab}")
    print("=" * 50)
    print(f"\nFUNCTIONS:\n{h[0]}")
    print(f"\nGRADING:\n{h[1]}")
    print(f"\nCONSTRAINTS:\n{h[2]}")
    print(f"\nHARDEST:\n{h[3]}")
    print(f"\nEDGE CASES:\n{h[4]}")
    print(f"\nTOOLS:\n{h[5]}")
    print(f"\nBOOK CHAPTERS:\n{h[6]}")
    print("=" * 50)
    conn.close()

if len(sys.argv) > 1:
    get_handout(' '.join(sys.argv[1:]))
else:
    lab = input("Lab name: ")
    get_handout(lab)
