import sqlite3
import os
import sys
from datetime import datetime

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

def get_active_lab():
    session_path = os.path.expanduser(
        '~/projects/malloc-training/SESSION.md')
    try:
        with open(session_path) as f:
            for line in f:
                if line.startswith("ACTIVE LAB:"):
                    return line.split(":", 1)[1].strip()
    except:
        pass
    return "unknown"

def get_active_course():
    session_path = os.path.expanduser(
        '~/projects/malloc-training/SESSION.md')
    try:
        with open(session_path) as f:
            for line in f:
                if line.startswith("ACTIVE COURSE:"):
                    return line.split(":", 1)[1].strip()
    except:
        pass
    return "unknown"

def get_cairo_time():
    if HAS_PYTZ:
        cairo = pytz.timezone('Africa/Cairo')
        now = datetime.now(cairo)
    else:
        now = datetime.now()
    return now

def generate_mini_context():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    now = get_cairo_time()
    print("=" * 40)
    print("MINI CONTEXT")
    print(now.strftime('%A %d %B %Y %I:%M %p Cairo'))
    print("=" * 40)

    c.execute('SELECT COUNT(*) FROM projects')
    count = c.fetchone()[0]

    active_lab = get_active_lab()
    active_course = get_active_course()
    print(f"Course : {active_course}")
    print(f"Lab    : {active_lab}")

    if count == 0:
        print("No projects yet. Start from Project 1.")
        conn.close()
        return

    c.execute('''SELECT number, name, phase
                 FROM projects
                 ORDER BY number DESC LIMIT 1''')
    last = c.fetchone()
    print(f"Last   : Project {last[0]} — {last[1]}")
    print(f"Phase  : {last[2]}")
    print(f"Next   : Project {last[0] + 1}")

    c.execute('''SELECT handoff FROM projects
                 ORDER BY number DESC LIMIT 1''')
    handoff = c.fetchone()
    if handoff and handoff[0]:
        print(f"\nHANDOFF:\n{handoff[0]}")

    c.execute('''SELECT concept, watch_for_recurrence
                 FROM weakness_patterns
                 ORDER BY project_number DESC LIMIT 2''')
    weaknesses = c.fetchall()
    if weaknesses:
        print(f"\nACTIVE WEAKNESSES:")
        for w in weaknesses:
            print(f"  {w[0]}: {w[1]}")

    c.execute('''SELECT content FROM mind_model
                 ORDER BY project_number DESC LIMIT 1''')
    mm = c.fetchone()
    if mm:
        print(f"\nLAST MIND NOTE:\n{mm[0][:300]}")

    print("\n" + "=" * 40)
    print("For full context run: python3 context.py")
    print("=" * 40)
    conn.close()

def generate_context():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    now = get_cairo_time()
    print("=" * 60)
    print("CONTEXT FOR NEW SESSION")
    print(now.strftime('%A %d %B %Y %I:%M %p Cairo'))
    print("=" * 60)

    active_lab = get_active_lab()
    active_course = get_active_course()
    print(f"Active course: {active_course}")
    print(f"Active lab   : {active_lab}")

    c.execute('SELECT COUNT(*) FROM projects')
    count = c.fetchone()[0]

    if count == 0:
        print("\nNo projects completed yet.")
        print("Starting from Project 1.")
        print("=" * 60)
        conn.close()
        return

    # Time since last project
    c.execute('''SELECT completed_at FROM projects
                 ORDER BY number DESC LIMIT 1''')
    last_time = c.fetchone()
    if last_time and last_time[0]:
        try:
            last = datetime.fromisoformat(last_time[0])
            if HAS_PYTZ:
                cairo = pytz.timezone('Africa/Cairo')
                now_aware = datetime.now(cairo)
                last_aware = last.replace(
                    tzinfo=pytz.utc).astimezone(cairo)
                diff = now_aware - last_aware
            else:
                diff = now - last
            days = diff.days
            hours = diff.seconds // 3600
            if days > 0:
                print(f"Time since last project: {days} days")
                if days > 7:
                    print("WARNING: OVER ONE WEEK.")
                    print("SPACED REPETITION REQUIRED.")
                    print("Quiz last 5 concepts before continuing.")
            else:
                print(f"Time since last project: {hours} hours")
        except:
            pass

    # Current state
    c.execute('''SELECT number, name, lab, course, phase
                 FROM projects
                 ORDER BY number DESC LIMIT 1''')
    last = c.fetchone()
    print(f"\nCURRENT STATE:")
    print(f"Last completed : Project {last[0]} — {last[1]}")
    print(f"Course         : {last[3]}")
    print(f"Lab            : {last[2]}")
    print(f"Phase          : {last[4]}")
    print(f"Next project   : {last[0] + 1}")

    # Concepts owned
    print(f"\nCONCEPTS OWNED — {active_lab} (last 10):")
    c.execute('''SELECT c.name, c.how_it_clicked
                 FROM concepts c
                 JOIN projects p ON p.number = c.project_number
                 WHERE p.lab = ? AND c.status = 'owned'
                 ORDER BY c.project_number DESC LIMIT 10''',
              (active_lab,))
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  - {row[0]}: {row[1]}")
    else:
        print("  None yet in this lab.")

    # Recent projects
    print(f"\nRECENT PROJECTS — {active_lab} (last 3):")
    c.execute('''SELECT number, name, concept, status,
                        what_worked, what_failed, handoff,
                        appears_in_future_labs
                 FROM projects
                 WHERE lab = ?
                 ORDER BY number DESC LIMIT 3''',
              (active_lab,))
    for p in c.fetchall():
        print(f"\n  Project {p[0]} — {p[1]}")
        print(f"  Concept : {p[2]} | Status: {p[3]}")
        print(f"  Worked  : {p[4]}")
        print(f"  Failed  : {p[5]}")
        if p[6]:
            print(f"  Handoff : {p[6]}")
        if p[7]:
            print(f"  Appears in: {p[7]}")

    # Project narratives
    print(f"\nPROJECT DESIGN NARRATIVES (last 3):")
    c.execute('''SELECT pn.project_number, p.name,
                        pn.why_designed_this_way,
                        pn.gap_it_closes,
                        pn.what_response_revealed,
                        pn.what_breaks_without_this,
                        pn.what_next_project_must_do
                 FROM project_narrative pn
                 JOIN projects p ON p.number = pn.project_number
                 WHERE p.lab = ?
                 ORDER BY pn.project_number DESC LIMIT 3''',
              (active_lab,))
    narratives = c.fetchall()
    if narratives:
        for n in narratives:
            print(f"\n  Project {n[0]} — {n[1]}")
            print(f"  Why      : {n[2]}")
            print(f"  Gap      : {n[3]}")
            print(f"  Revealed : {n[4]}")
            print(f"  Without  : {n[5]}")
            print(f"  Next must: {n[6]}")
    else:
        print("  None yet.")

    # Most recent code
    print(f"\nMOST RECENT CODE:")
    c.execute('''SELECT number, name, final_code
                 FROM projects
                 WHERE lab = ?
                 ORDER BY number DESC LIMIT 1''',
              (active_lab,))
    code = c.fetchone()
    if code and code[2]:
        print(f"  Project {code[0]} — {code[1]}")
        print(code[2])
    else:
        print("  None yet.")

    # Active lab handout
    print(f"\nACTIVE LAB HANDOUT:")
    c.execute('''SELECT functions_to_implement,
                        grading_criteria,
                        critical_constraints,
                        hardest_concept,
                        edge_cases
                 FROM lab_handouts
                 WHERE lab = ?
                 ORDER BY stored_at DESC LIMIT 1''',
              (active_lab,))
    handout = c.fetchone()
    if handout:
        print(f"  FUNCTIONS:\n{handout[0]}")
        print(f"  GRADING:\n{handout[1]}")
        print(f"  CONSTRAINTS:\n{handout[2]}")
        print(f"  HARDEST:\n{handout[3]}")
        print(f"  EDGE CASES:\n{handout[4]}")
    else:
        print("  No handout stored yet.")
        print("  Run: python3 get_handout.py")

    # Cross-lab weakness patterns
    print(f"\nCROSS-LAB WEAKNESS PATTERNS:")
    c.execute('''SELECT wp.concept,
                        wp.specific_misconception,
                        wp.exact_analogy_that_clicked,
                        wp.exact_wording_that_clicked,
                        wp.exact_sub_project_that_worked,
                        wp.watch_for_recurrence,
                        p.lab, p.course
                 FROM weakness_patterns wp
                 JOIN projects p ON p.number = wp.project_number
                 ORDER BY wp.project_number DESC''')
    weaknesses = c.fetchall()
    if weaknesses:
        for w in weaknesses:
            print(f"\n  [{w[7]} — {w[6]}] {w[0]}")
            print(f"  Misconception: {w[1]}")
            print(f"  Analogy      : {w[2]}")
            print(f"  Wording      : {w[3]}")
            print(f"  Watch for    : {w[5]}")
            print(f"  EXACT SUB-PROJECT:")
            print(f"  {w[4]}")
    else:
        print("  None recorded yet.")

    # Coding patterns
    print(f"\nCRITICAL CODING PATTERNS:")
    c.execute('''SELECT pattern, frequency, severity
                 FROM patterns
                 ORDER BY frequency DESC LIMIT 3''')
    patterns = c.fetchall()
    if patterns:
        for p in patterns:
            print(f"  [{p[2]}] {p[0]} (seen {p[1]} times)")
    else:
        print("  None yet.")

    # Teaching decisions
    print(f"\nRECENT TEACHING DECISIONS:")
    c.execute('''SELECT d.project_number, d.concept,
                        d.angle_used, d.analogy_used,
                        d.result
                 FROM decisions d
                 JOIN projects p ON p.number = d.project_number
                 WHERE p.lab = ?
                 ORDER BY d.project_number DESC LIMIT 5''',
              (active_lab,))
    decisions = c.fetchall()
    if decisions:
        for d in decisions:
            print(f"  P{d[0]}: {d[1]} → {d[2]}"
                  f" ({d[3]}) → {d[4]}")
    else:
        print("  None yet.")

    # Foundation status
    print(f"\nFOUNDATION STATUS:")
    c.execute('''SELECT c.name, c.struggled_with
                 FROM concepts c
                 JOIN projects p ON p.number = c.project_number
                 WHERE c.status != 'owned'
                 AND p.lab = ?''', (active_lab,))
    cracked = c.fetchall()
    if cracked:
        for concept in cracked:
            print(f"  CRACKED: {concept[0]}"
                  f" — {concept[1]}")
    else:
        print("  All concepts solid.")

    # Novel question history
    print(f"\nNOVEL QUESTION HISTORY (last 5):")
    c.execute('''SELECT question_text, project_number,
                        result, concept
                 FROM quiz_records
                 WHERE is_novel_question = 1
                 ORDER BY project_number DESC LIMIT 5''')
    novel_qs = c.fetchall()
    if novel_qs:
        for q in novel_qs:
            print(f"  P{q[1]} [{q[2]}]: {q[0][:60]}...")
    else:
        print("  No novel questions recorded yet.")

    # Exam history
    print(f"\nEXAM HISTORY:")
    c.execute('''SELECT phase, lab, status, gaps_found
                 FROM transfer_exams
                 ORDER BY completed_at DESC LIMIT 3''')
    exams = c.fetchall()
    if exams:
        for e in exams:
            print(f"  Phase {e[0]} {e[1]}: {e[2]}"
                  f" | Gaps: {e[3]}")
    else:
        print("  No exams completed yet.")

    # Latest mind model
    print(f"\nLATEST MIND MODEL UPDATE:")
    c.execute('''SELECT content, project_number, update_type
                 FROM mind_model
                 ORDER BY project_number DESC LIMIT 1''')
    mm = c.fetchone()
    if mm:
        print(f"  Type: {mm[2]} | After Project: {mm[1]}")
        print(f"  {mm[0]}")
    else:
        print("  Not yet generated.")

    print("\n" + "=" * 60)
    conn.close()

if len(sys.argv) > 1 and sys.argv[1] == '--mini':
    generate_mini_context()
else:
    generate_context()
