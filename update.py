import sqlite3
import os
import sys


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

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


def parse_auto_block(block):
    data = {}
    for line in block.strip().split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            data[key.strip()] = value.strip()
    return data


def get_db():
    db_path = os.path.expanduser(
        '~/projects/malloc-training/brain.db')
    return sqlite3.connect(db_path)


def duplicate_guard(c, number):
    """Block if project number already exists."""
    c.execute(
        "SELECT number FROM projects WHERE number = ?",
        (number,))
    if c.fetchone():
        print(f"\nERROR: Project {number} already exists.")
        print("Run db_check.py to inspect the database.")
        print("Aborting to prevent data corruption.")
        sys.exit(1)


def mind_model_trigger(conn, c, total):
    """Auto-trigger mind model update every 5 projects."""
    if total % 5 != 0:
        return
    print("\n" + "=" * 55)
    print(f"PROJECT {total} COMPLETE — MIND MODEL UPDATE REQUIRED")
    print("=" * 55)
    print("Paste this prompt into Claude RIGHT NOW:\n")
    print("─" * 55)
    print(
        f"Generate a MIND_MODEL micro-update paragraph.\n"
        f"One paragraph only. Based on the last 5 projects,\n"
        f"describe this student's thinking patterns,\n"
        f"misconception tendencies, learning rhythm,\n"
        f"what analogies worked, what did not.\n"
        f"Format exactly:\n"
        f"MICRO UPDATE — After Project {total}: [paragraph]"
    )
    print("─" * 55)
    print("\nPaste Claude's response below.")
    mind_update = get_multiline("")

    if not mind_update.strip():
        print("\nWARNING: Mind model update skipped.")
        print("This weakens the system. Do not skip again.")
        return

    c.execute(
        '''INSERT INTO mind_model
           (project_number, update_type, content)
           VALUES (?,?,?)''',
        (total, 'micro', mind_update))
    conn.commit()

    md_path = os.path.expanduser(
        '~/projects/malloc-training/MIND_MODEL.md')
    with open(md_path, 'a') as f:
        f.write(
            f"\n\nMICRO UPDATE — After Project {total}:\n"
            f"{mind_update}\n")
    print(f"\nMind model updated and written to MIND_MODEL.md.")


def post_project_handoff_prompt(number):
    """Remind Claude to generate handoff NOW, not at session end."""
    print("\n" + "=" * 55)
    print("HANDOFF — GENERATE NOW (not at session end)")
    print("=" * 55)
    print(
        "Tell Claude:\n"
        "  'Generate the handoff instruction for Project "
        f"{number} now.\n"
        "   The quiz just passed. Context is sharp.'\n"
        "Paste the handoff into the next update.py run."
    )
    print("=" * 55)


# ─────────────────────────────────────────────
# AUTO MODE
# ─────────────────────────────────────────────

def update_auto(block):
    conn = get_db()
    c = conn.cursor()
    d = parse_auto_block(block)

    number = int(d.get('number', 0))
    duplicate_guard(c, number)

    name               = d.get('name', '')
    phase              = int(d.get('phase', 1))
    lab                = d.get('lab', '')
    course             = d.get('course', '')
    concept            = d.get('concept', '')
    status             = d.get('status', '')
    prediction         = d.get('prediction', '')
    actual_output      = d.get('actual_output', '')
    what_worked        = d.get('what_worked', '')
    what_failed        = d.get('what_failed', '')
    teaching_angle     = d.get('teaching_angle', '')
    handoff            = d.get('handoff', '')
    code_review        = d.get('code_review', '')
    key_exchange       = d.get('key_exchange', 'none')
    appears_in         = d.get('appears_in_future_labs', '')
    concept_status     = d.get('concept_status', '')
    how_clicked        = d.get('how_clicked', '')
    struggled          = d.get('struggled_with', '')
    resolved           = d.get('resolved_by', '')
    connects           = d.get('connects_to', '')
    why                = d.get('why_designed', '')
    gap                = d.get('gap_closed', '')
    revealed           = d.get('response_revealed', '')
    lab_conn           = d.get('lab_connection', '')
    breaks             = d.get('breaks_without', '')
    next_must          = d.get('next_must', '')
    position           = d.get('position_reasoning', '')

    final_code = get_multiline("\nPaste final code.")

    c.execute(
        '''INSERT INTO projects
           (number, name, phase, lab, course,
            concept, status, prediction,
            actual_output, final_code,
            teaching_angle, what_worked,
            what_failed, handoff, code_review,
            key_exchange, appears_in_future_labs)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (number, name, phase, lab, course,
         concept, status, prediction,
         actual_output, final_code,
         teaching_angle, what_worked,
         what_failed, handoff, code_review,
         key_exchange, appears_in))

    c.execute(
        '''INSERT INTO concepts
           (name, status, how_it_clicked,
            struggled_with, resolved_by,
            connects_to, project_number)
           VALUES (?,?,?,?,?,?,?)''',
        (concept, concept_status, how_clicked,
         struggled, resolved, connects, number))

    c.execute(
        '''INSERT INTO project_narrative
           (project_number, why_designed_this_way,
            gap_it_closes, what_response_revealed,
            connection_to_lab,
            what_breaks_without_this,
            what_next_project_must_do,
            curriculum_position_reasoning)
           VALUES (?,?,?,?,?,?,?,?)''',
        (number, why, gap, revealed, lab_conn,
         breaks, next_must, position))

    sub = d.get('sub_projects_generated', 'no')
    if sub.lower() == 'yes':
        specific  = input("Specific misconception: ")
        failed    = input("Sub-projects that failed: ")
        worked    = input("Sub-project that worked: ")
        analogy   = input("Exact analogy that clicked: ")
        wording   = input("Exact wording that clicked: ")
        recurrence = input("Watch for recurrence: ")
        exact_sub = get_multiline("Paste exact sub-project text.")

        c.execute(
            '''INSERT INTO weakness_patterns
               (concept, specific_misconception,
                sub_projects_that_failed,
                sub_projects_that_worked,
                exact_analogy_that_clicked,
                exact_wording_that_clicked,
                exact_sub_project_that_worked,
                watch_for_recurrence,
                project_number)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (concept, specific, failed, worked,
             analogy, wording, exact_sub,
             recurrence, number))

    conn.commit()

    # Mind model auto-trigger
    c.execute('SELECT COUNT(*) FROM projects')
    total = c.fetchone()[0]
    mind_model_trigger(conn, c, total)

    conn.close()

    print(f"\nDatabase updated — Project {number} complete.")
    print(
        f"git add . && git commit -m "
        f"'Project {number} complete — {concept}' && git push")


# ─────────────────────────────────────────────
# INTERACTIVE MODE
# ─────────────────────────────────────────────

def update_interactive():
    conn = get_db()
    c = conn.cursor()

    print("=" * 45)
    print("POST-PROJECT UPDATE — INTERACTIVE")
    print("=" * 45)

    number = int(input("Project number: "))
    duplicate_guard(c, number)

    name           = input("Project name: ")
    phase          = int(input("Phase (1-5): "))
    lab            = input("Lab name: ")
    course         = input("Course name: ")
    concept        = input("Core concept: ")
    status         = input("Status (owned/cracked/struggling): ")
    prediction     = input("Your prediction was: ")
    actual_output  = input("Actual output was: ")
    what_worked    = input("What worked: ")
    what_failed    = input("What failed (or 'nothing'): ")
    teaching_angle = input("Teaching angle used: ")

    # Handoff collected here — mid-session, not at token limit
    print("\nHandoff (generate this in Claude NOW while sharp):")
    handoff        = input("> ")

    code_review    = input("Code patterns observed: ")
    key_exchange   = input("Critical exchange (or 'none'): ")
    appears_in     = input("Appears in future labs: ")
    final_code     = get_multiline("\nPaste final code.")

    c.execute(
        '''INSERT INTO projects
           (number, name, phase, lab, course,
            concept, status, prediction,
            actual_output, final_code,
            teaching_angle, what_worked,
            what_failed, handoff, code_review,
            key_exchange, appears_in_future_labs)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (number, name, phase, lab, course,
         concept, status, prediction,
         actual_output, final_code,
         teaching_angle, what_worked,
         what_failed, handoff, code_review,
         key_exchange, appears_in))

    concept_status = input("\nConcept status (owned/cracked): ")
    how_clicked    = input("How it clicked: ")
    struggled      = input("Struggled with: ")
    resolved       = input("Resolved by: ")
    connects       = input("Connects to: ")

    c.execute(
        '''INSERT INTO concepts
           (name, status, how_it_clicked,
            struggled_with, resolved_by,
            connects_to, project_number)
           VALUES (?,?,?,?,?,?,?)''',
        (concept, concept_status, how_clicked,
         struggled, resolved, connects, number))

    why      = input("\nWhy designed this way: ")
    gap      = input("Gap it closes: ")
    revealed = input("Response revealed: ")
    lab_conn = input("Lab connection: ")
    breaks   = input("Breaks without this: ")
    next_must = input("Next project must: ")
    position  = input("Position reasoning: ")

    c.execute(
        '''INSERT INTO project_narrative
           (project_number, why_designed_this_way,
            gap_it_closes, what_response_revealed,
            connection_to_lab,
            what_breaks_without_this,
            what_next_project_must_do,
            curriculum_position_reasoning)
           VALUES (?,?,?,?,?,?,?,?)''',
        (number, why, gap, revealed, lab_conn,
         breaks, next_must, position))

    sub = input("\nSub-projects generated? (yes/no): ")
    if sub.lower() == 'yes':
        specific   = input("Specific misconception: ")
        failed     = input("Sub-projects that failed: ")
        worked     = input("Sub-project that worked: ")
        analogy    = input("Exact analogy: ")
        wording    = input("Exact wording: ")
        recurrence = input("Watch for: ")
        exact_sub  = get_multiline("Paste exact sub-project text.")

        c.execute(
            '''INSERT INTO weakness_patterns
               (concept, specific_misconception,
                sub_projects_that_failed,
                sub_projects_that_worked,
                exact_analogy_that_clicked,
                exact_wording_that_clicked,
                exact_sub_project_that_worked,
                watch_for_recurrence,
                project_number)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (concept, specific, failed, worked,
             analogy, wording, exact_sub,
             recurrence, number))

    pattern = input("\nCoding pattern (or enter to skip): ")
    if pattern.strip():
        severity = input("Severity (low/medium/high): ")
        c.execute(
            'SELECT id, frequency FROM patterns WHERE pattern = ?',
            (pattern,))
        existing = c.fetchone()
        if existing:
            c.execute(
                '''UPDATE patterns
                   SET frequency = frequency + 1,
                       last_seen_project = ?
                   WHERE id = ?''',
                (number, existing[0]))
        else:
            c.execute(
                '''INSERT INTO patterns
                   (pattern, first_seen_project,
                    last_seen_project, severity)
                   VALUES (?,?,?,?)''',
                (pattern, number, number, severity))

    angle   = input("\nTeaching angle used: ")
    analogy2 = input("Analogy used: ")
    result  = input("Result (landed/struggled/failed): ")

    c.execute(
        '''INSERT INTO decisions
           (project_number, concept,
            angle_used, analogy_used, result)
           VALUES (?,?,?,?,?)''',
        (number, concept, angle, analogy2, result))

    conn.commit()

    # Mind model auto-trigger
    c.execute('SELECT COUNT(*) FROM projects')
    total = c.fetchone()[0]
    mind_model_trigger(conn, c, total)

    conn.close()
    print(f"\nDatabase updated — Project {number} complete.")
    print(
        f"git add . && git commit -m "
        f"'Project {number} complete — {concept}' && git push")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if len(sys.argv) > 1 and sys.argv[1] == '--auto':
    if len(sys.argv) > 2:
        block = ' '.join(sys.argv[2:])
    else:
        print("Paste auto update block. Type END when done:")
        lines = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        block = '\n'.join(lines)
    update_auto(block)
else:
    update_interactive()
