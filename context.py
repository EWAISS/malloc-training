import sqlite3
import os
import sys
from datetime import datetime

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False


# ─────────────────────────────────────────────
# SESSION FILE READERS
# ─────────────────────────────────────────────

def get_session_field(field):
    session_path = os.path.expanduser(
        '~/projects/malloc-training/SESSION.md')
    try:
        with open(session_path) as f:
            for line in f:
                if line.startswith(f"{field}:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "unknown"


def get_active_lab():
    return get_session_field("ACTIVE LAB")


def get_active_course():
    return get_session_field("ACTIVE COURSE")


def get_cairo_time():
    if HAS_PYTZ:
        cairo = pytz.timezone('Africa/Cairo')
        return datetime.now(cairo)
    return datetime.now()


# ─────────────────────────────────────────────
# GATE CHECKS — run before anything else prints
# ─────────────────────────────────────────────

def adversarial_gate(c):
    """Block if last phase transfer exam has no gap report."""
    try:
        c.execute(
            '''SELECT phase, lab, adversarial_gap_report
               FROM transfer_exams
               ORDER BY completed_at DESC LIMIT 1''')
        last_exam = c.fetchone()
        if last_exam:
            gap = last_exam[2]
            if not gap or gap.strip() in ('', 'none'):
                print("=" * 60)
                print("BLOCKED — ADVERSARIAL EXAM NOT COMPLETED")
                print("=" * 60)
                print(
                    f"Phase {last_exam[0]} | {last_exam[1]}\n"
                    f"Transfer exam has no adversarial gap report.\n\n"
                    f"Run:  python3 adversary.py\n"
                    f"Complete it, then re-run context.py."
                )
                print("=" * 60)
                return False
    except sqlite3.OperationalError:
        pass  # table may not exist yet — no exams taken
    return True


def gap_gate(c, now):
    """
    If > 7 days since last project: hide curriculum position,
    show spaced repetition gate instead.
    Returns True if gate is ACTIVE (caller should exit after printing).
    """
    c.execute(
        '''SELECT completed_at FROM projects
           ORDER BY number DESC LIMIT 1''')
    last_time = c.fetchone()
    if not last_time or not last_time[0]:
        return False

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
        if days <= 7:
            return False

        # Gate is active
        print("=" * 60)
        print(f"GAP GATE ACTIVE — {days} days since last project")
        print("=" * 60)
        print(
            "New material is locked.\n"
            "Before continuing, Claude must quiz these concepts:"
        )

        c.execute(
            '''SELECT name FROM concepts
               WHERE status = 'owned'
               ORDER BY project_number DESC LIMIT 5''')
        for row in c.fetchall():
            print(f"  — {row[0]}")

        print(
            "\nTell Claude: 'Run spaced repetition quiz now.'\n"
            "After passing all 5, resume normally.\n"
            "Curriculum position is hidden until gate clears."
        )
        print("=" * 60)
        return True

    except Exception:
        return False


# ─────────────────────────────────────────────
# CONTEXT VERIFICATION BLOCK
# ─────────────────────────────────────────────

def print_verification_block(c, active_lab):
    """
    Prints the 4-question block Claude must answer at session start.
    Answers are checkable against SESSION.md and brain.db.
    """
    c.execute(
        '''SELECT number, name, concept,
                  what_failed, handoff
           FROM projects
           WHERE lab = ?
           ORDER BY number DESC LIMIT 1''',
        (active_lab,))
    last = c.fetchone()

    c.execute(
        '''SELECT concept, watch_for_recurrence
           FROM weakness_patterns
           ORDER BY project_number DESC LIMIT 1''')
    weakness = c.fetchone()

    print("\n" + "=" * 60)
    print("CONTEXT VERIFICATION — CLAUDE MUST ANSWER BEFORE TEACHING")
    print("=" * 60)
    print(
        "Claude: Read the context above and answer all four.\n"
        "Student: Check each answer against SESSION.md.\n"
        "If any answer is wrong or vague: STOP.\n"
        "Run context.py again, repaste, re-verify.\n"
    )
    print("Q1. What was the exact concept of the last project?")
    if last:
        print(f"    [Answer should be: {last[2]}]")
    print("Q2. What did the student struggle with in that project?")
    if last:
        print(f"    [Answer should mention: {last[3]}]")
    print("Q3. Restate the handoff instruction verbatim.")
    if last and last[4]:
        print(f"    [Answer should be: {last[4]}]")
    print("Q4. What is the active weakness pattern to watch for?")
    if weakness:
        print(f"    [Answer should mention: {weakness[0]} — {weakness[1]}]")
    print("=" * 60)


# ─────────────────────────────────────────────
# MINI CONTEXT
# ─────────────────────────────────────────────

def generate_mini_context():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    now = get_cairo_time()

    if not adversarial_gate(c):
        conn.close()
        sys.exit(1)

    print("=" * 40)
    print("MINI CONTEXT")
    print(now.strftime('%A %d %B %Y %I:%M %p Cairo'))
    print("=" * 40)

    c.execute('SELECT COUNT(*) FROM projects')
    count = c.fetchone()[0]
    active_lab    = get_active_lab()
    active_course = get_active_course()

    print(f"Course : {active_course}")
    print(f"Lab    : {active_lab}")

    if count == 0:
        print("No projects yet. Start from Project 1.")
        conn.close()
        return

    if gap_gate(c, now):
        conn.close()
        return

    c.execute(
        '''SELECT number, name, phase
           FROM projects ORDER BY number DESC LIMIT 1''')
    last = c.fetchone()
    print(f"Last   : Project {last[0]} — {last[1]}")
    print(f"Phase  : {last[2]}")
    print(f"Next   : Project {last[0] + 1}")

    c.execute(
        '''SELECT handoff FROM projects
           ORDER BY number DESC LIMIT 1''')
    handoff = c.fetchone()
    if handoff and handoff[0]:
        print(f"\nHANDOFF:\n{handoff[0]}")

    c.execute(
        '''SELECT concept, watch_for_recurrence
           FROM weakness_patterns
           ORDER BY project_number DESC LIMIT 2''')
    weaknesses = c.fetchall()
    if weaknesses:
        print("\nACTIVE WEAKNESSES:")
        for w in weaknesses:
            print(f"  {w[0]}: {w[1]}")

    c.execute(
        '''SELECT content FROM mind_model
           ORDER BY project_number DESC LIMIT 1''')
    mm = c.fetchone()
    if mm:
        print(f"\nLAST MIND NOTE:\n{mm[0][:300]}")

    print("\n" + "=" * 40)
    print("For full context run: python3 context.py")
    print("=" * 40)

    print_verification_block(c, active_lab)
    conn.close()


# ─────────────────────────────────────────────
# FULL CONTEXT
# ─────────────────────────────────────────────

def generate_context():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    now = get_cairo_time()

    # ── GATES ──────────────────────────────────
    if not adversarial_gate(c):
        conn.close()
        sys.exit(1)

    print("=" * 60)
    print("CONTEXT FOR NEW SESSION")
    print(now.strftime('%A %d %B %Y %I:%M %p Cairo'))
    print("=" * 60)

    active_lab    = get_active_lab()
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

    # ── TIME GAP GATE ───────────────────────────
    if gap_gate(c, now):
        conn.close()
        return

    # ── TIME SINCE LAST PROJECT ─────────────────
    c.execute(
        '''SELECT completed_at FROM projects
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
            days  = diff.days
            hours = diff.seconds // 3600
            if days > 0:
                print(f"\nTime since last project: {days} days")
            else:
                print(f"\nTime since last project: {hours} hours")
        except Exception:
            pass

    # ── CURRENT STATE ───────────────────────────
    c.execute(
        '''SELECT number, name, lab, course, phase
           FROM projects ORDER BY number DESC LIMIT 1''')
    last = c.fetchone()
    print(f"\nCURRENT STATE:")
    print(f"  Last completed : Project {last[0]} — {last[1]}")
    print(f"  Course         : {last[3]}")
    print(f"  Lab            : {last[2]}")
    print(f"  Phase          : {last[4]}")
    print(f"  Next project   : {last[0] + 1}")

    # ── CONCEPTS OWNED ──────────────────────────
    print(f"\nCONCEPTS OWNED — {active_lab} (last 10):")
    c.execute(
        '''SELECT c.name, c.how_it_clicked
           FROM concepts c
           JOIN projects p ON p.number = c.project_number
           WHERE p.lab = ? AND c.status = 'owned'
           ORDER BY c.project_number DESC LIMIT 10''',
        (active_lab,))
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  — {row[0]}: {row[1]}")
    else:
        print("  None yet in this lab.")

    # ── RECENT PROJECTS ─────────────────────────
    print(f"\nRECENT PROJECTS — {active_lab} (last 5):")
    c.execute(
        '''SELECT number, name, concept, status,
                  what_worked, what_failed, handoff,
                  appears_in_future_labs
           FROM projects WHERE lab = ?
           ORDER BY number DESC LIMIT 5''',
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

    # ── PROJECT NARRATIVES ──────────────────────
    print(f"\nPROJECT DESIGN NARRATIVES (last 5):")
    c.execute(
        '''SELECT pn.project_number, p.name,
                  pn.why_designed_this_way,
                  pn.gap_it_closes,
                  pn.what_response_revealed,
                  pn.what_breaks_without_this,
                  pn.what_next_project_must_do
           FROM project_narrative pn
           JOIN projects p ON p.number = pn.project_number
           WHERE p.lab = ?
           ORDER BY pn.project_number DESC LIMIT 5''',
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

    # ── MOST RECENT CODE ────────────────────────
    print(f"\nMOST RECENT CODE:")
    c.execute(
        '''SELECT number, name, final_code
           FROM projects WHERE lab = ?
           ORDER BY number DESC LIMIT 1''',
        (active_lab,))
    code = c.fetchone()
    if code and code[2]:
        print(f"  Project {code[0]} — {code[1]}")
        print(code[2])
    else:
        print("  None yet.")

    # ── LAB HANDOUT ─────────────────────────────
    print(f"\nACTIVE LAB HANDOUT:")
    try:
        c.execute(
            '''SELECT functions_to_implement,
                      grading_criteria,
                      critical_constraints,
                      hardest_concept,
                      edge_cases
               FROM lab_handouts WHERE lab = ?
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
    except sqlite3.OperationalError:
        print("  lab_handouts table not found.")

    # ── WEAKNESS PATTERNS ───────────────────────
    print(f"\nCROSS-LAB WEAKNESS PATTERNS:")
    c.execute(
        '''SELECT wp.concept,
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
            print(f"  Misconception : {w[1]}")
            print(f"  Analogy       : {w[2]}")
            print(f"  Wording       : {w[3]}")
            print(f"  Watch for     : {w[5]}")
            print(f"  Sub-project   : {w[4]}")
    else:
        print("  None recorded yet.")

    # ── CODING PATTERNS ─────────────────────────
    print(f"\nCRITICAL CODING PATTERNS:")
    try:
        c.execute(
            '''SELECT pattern, frequency, severity
               FROM patterns ORDER BY frequency DESC LIMIT 3''')
        patterns = c.fetchall()
        if patterns:
            for p in patterns:
                print(f"  [{p[2]}] {p[0]} (seen {p[1]} times)")
        else:
            print("  None yet.")
    except sqlite3.OperationalError:
        print("  patterns table not found.")

    # ── TEACHING DECISIONS ──────────────────────
    print(f"\nRECENT TEACHING DECISIONS:")
    try:
        c.execute(
            '''SELECT d.project_number, d.concept,
                      d.angle_used, d.analogy_used, d.result
               FROM decisions d
               JOIN projects p ON p.number = d.project_number
               WHERE p.lab = ?
               ORDER BY d.project_number DESC LIMIT 5''',
            (active_lab,))
        decisions = c.fetchall()
        if decisions:
            for d in decisions:
                print(
                    f"  P{d[0]}: {d[1]} → {d[2]} "
                    f"({d[3]}) → {d[4]}")
        else:
            print("  None yet.")
    except sqlite3.OperationalError:
        print("  decisions table not found.")

    # ── FOUNDATION STATUS ───────────────────────
    print(f"\nFOUNDATION STATUS:")
    c.execute(
        '''SELECT c.name, c.struggled_with
           FROM concepts c
           JOIN projects p ON p.number = c.project_number
           WHERE c.status != 'owned' AND p.lab = ?''',
        (active_lab,))
    cracked = c.fetchall()
    if cracked:
        for con in cracked:
            print(f"  CRACKED: {con[0]} — {con[1]}")
    else:
        print("  All concepts solid.")

    # ── EXTERNAL VALIDATION STATUS ──────────────
    print(f"\nEXTERNAL VALIDATION STATUS:")
    try:
        c.execute(
            '''SELECT concept, source, result
               FROM external_validation
               ORDER BY validated_at DESC LIMIT 5''')
        validations = c.fetchall()
        if validations:
            for v in validations:
                mark = "PASS" if v[2] == 'pass' else "FAIL"
                print(f"  [{mark}] {v[0]} — {v[1]}")
        else:
            print("  No external validations yet.")
            print(
                "  WARNING: No concepts have been externally verified.\n"
                "  Run validate_concept.py after the next project.")
    except sqlite3.OperationalError:
        print("  external_validation table not found.")

    # ── NOVEL QUESTIONS ─────────────────────────
    print(f"\nNOVEL QUESTION HISTORY (last 5):")
    try:
        c.execute(
            '''SELECT question_text, project_number,
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
    except sqlite3.OperationalError:
        print("  quiz_records table not found.")

    # ── EXAM HISTORY ────────────────────────────
    print(f"\nEXAM HISTORY:")
    try:
        c.execute(
            '''SELECT phase, lab, status, gaps_found,
                      adversarial_gap_report
               FROM transfer_exams
               ORDER BY completed_at DESC LIMIT 3''')
        exams = c.fetchall()
        if exams:
            for e in exams:
                adv = "ADV:done" if (
                    e[4] and e[4].strip() not in ('', 'none')
                ) else "ADV:MISSING"
                print(
                    f"  Phase {e[0]} {e[1]}: {e[2]} "
                    f"| Gaps: {e[3]} | {adv}")
        else:
            print("  No exams completed yet.")
    except sqlite3.OperationalError:
        print("  transfer_exams table not found.")

    # ── MIND MODEL ──────────────────────────────
    print(f"\nLATEST MIND MODEL UPDATE:")
    try:
        c.execute(
            '''SELECT content, project_number, update_type
               FROM mind_model
               ORDER BY project_number DESC LIMIT 1''')
        mm = c.fetchone()
        if mm:
            print(f"  Type: {mm[2]} | After Project: {mm[1]}")
            print(f"  {mm[0]}")
        else:
            print("  Not yet generated (triggers at Project 5).")
    except sqlite3.OperationalError:
        print("  mind_model table not found.")

    print("\n" + "=" * 60)
    conn.close()


    # ── LAB TRANSITION HISTORY ───────────────────
    try:
        c.execute(
            '''SELECT lab, next_lab, concepts_owned,
                      carried_forward, watch_for, key_analogy
               FROM lab_transitions
               ORDER BY transitioned_at DESC LIMIT 3''')
        transitions = c.fetchall()
        if transitions:
            print(f"\nCOMPLETED LAB TRANSITIONS (last 3):")
            for t in transitions:
                print(f"\n  {t[0]} → {t[1]}")
                print(f"  Owned         : {t[2]}")
                print(f"  Carried forward: {t[3]}")
                print(f"  Watch for     : {t[4]}")
                print(f"  Key analogy   : {t[5]}")
    except Exception:
        pass

    # ── CURRICULUM STATUS ────────────────────────
    curr_path = os.path.join(
        os.path.expanduser('~/projects/malloc-training'),
        'CURRICULUM.md')
    reason_path = os.path.join(
        os.path.expanduser('~/projects/malloc-training'),
        'CURRICULUM_REASONING.md')

    if os.path.exists(curr_path):
        # Count pending projects
        pending = []
        current = {}
        try:
            conn3 = sqlite3.connect(db_path)
            c3 = conn3.cursor()
            c3.execute('SELECT number FROM projects')
            done_nums = {row[0] for row in c3.fetchall()}
            conn3.close()

            with open(curr_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#'):
                        continue
                    if line.startswith('PROJECT '):
                        if current:
                            pending.append(current)
                        try:
                            num = int(line.split()[1])
                            current = {'number': num}
                        except (IndexError, ValueError):
                            current = {}
                    elif ':' in line and current:
                        key, _, value = line.partition(':')
                        current[key.strip().lower()] = value.strip()
            if current:
                pending.append(current)

            not_done = [p for p in pending
                        if p.get('number') not in done_nums]
            next_p = not_done[0] if not_done else None

            print(f"\nCURRICULUM STATUS:")
            print(f"  Planned  : {len(pending)} projects")
            print(f"  Completed: {len(done_nums)}")
            print(f"  Pending  : {len(not_done)}")

            if next_p:
                print(f"\nNEXT PROJECT FROM CURRICULUM:")
                print(f"  Project {next_p.get('number')} — "
                      f"{next_p.get('name', '?')}")
                print(f"  Concept : {next_p.get('concept', '?')}")
                print(f"  Gap     : {next_p.get('gap', '?')}")

        except Exception as e:
            print(f"  (Could not parse CURRICULUM.md: {e})")

    if os.path.exists(reason_path):
        print(f"\nNEXT PROJECT REASONING:")
        try:
            lines_r = []
            in_next = False
            count_r = 0
            with open(reason_path) as f:
                for line in f:
                    if line.startswith('NEXT PROJECT:') and count_r < 1:
                        in_next = True
                        count_r += 1
                        lines_r.append(line.rstrip())
                    elif line.startswith('NEXT PROJECT:') and count_r >= 1:
                        break
                    elif in_next and not line.startswith('#'):
                        lines_r.append(line.rstrip())
            if lines_r:
                for l in lines_r[:10]:
                    print(f"  {l}")
            else:
                print("  No reasoning for next project yet.")
                print("  Ask Claude to generate CURRICULUM_REASONING.md")
        except Exception as e:
            print(f"  (Could not read CURRICULUM_REASONING.md: {e})")


    # ── VERIFICATION BLOCK ──────────────────────
    # Reopen briefly to print this last
    conn2 = sqlite3.connect(db_path)
    c2 = conn2.cursor()
    print_verification_block(c2, active_lab)
    conn2.close()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if len(sys.argv) > 1 and sys.argv[1] == '--mini':
    generate_mini_context()
else:
    generate_context()
