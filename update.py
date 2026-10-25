import os
import re
import sys

from db import ask_lab, connect, find_lab
from prompts import (ask_choice, ask_int, ask_multiline, ask_text,
                     ask_yes_no)

CONCEPT_STATUSES = ('owned', 'cracked', 'struggling')


# Every key the auto block may contain. Only these start a new
# field, so multi-line values (handoff, code review) stay whole.
AUTO_KEYS = [
    'number', 'name', 'phase', 'lab', 'course', 'concept',
    'status', 'prediction', 'actual_output', 'what_worked',
    'what_failed', 'teaching_angle', 'handoff', 'code_review',
    'key_exchange', 'appears_in_future_labs', 'concept_status',
    'how_clicked', 'struggled_with', 'resolved_by', 'connects_to',
    'why_designed', 'gap_closed', 'response_revealed',
    'lab_connection', 'breaks_without', 'next_must',
    'position_reasoning', 'sub_projects_generated',
    'coding_pattern', 'pattern_severity', 'analogy_used',
    'decision_result',
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def parse_auto_block(block):
    keys = '|'.join(sorted(AUTO_KEYS, key=len, reverse=True))
    if '\n' in block.strip():
        # Pasted block: keys only count at the start of a line
        pattern = re.compile(rf'^[ \t]*({keys})[ \t]*:', re.M)
    else:
        # Block passed as arguments arrives flattened onto one line
        pattern = re.compile(rf'(?:^|(?<=\s))({keys})\s*:')

    matches = list(pattern.finditer(block))
    data = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) \
            else len(block)
        data[m.group(1)] = block[m.end():end].strip()
    return data


def get_db():
    return connect()


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


def ask_mind_model(total):
    """Every 5th project: collect the mind model update before saving.
    Returns the text, or '' when skipped."""
    if total % 5 != 0:
        return ''
    print("\n" + "=" * 55)
    print(f"PROJECT {total} — MIND MODEL UPDATE REQUIRED")
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
    mind_update = ask_multiline("")

    if not mind_update.strip():
        print("\nWARNING: Mind model update skipped.")
        print("This weakens the system. Do not skip again.")
    return mind_update.strip()


def next_total(c):
    """Project count once this project is saved."""
    c.execute('SELECT COUNT(*) FROM projects')
    return c.fetchone()[0] + 1


def save_project(conn, r):
    """Write one collected project record in a single transaction,
    then append the mind model note. Nothing is written before this."""
    number = r['number']
    with conn:
        c = conn.cursor()
        c.execute(
            '''INSERT INTO projects
               (number, name, phase, lab, course,
                concept, status, prediction,
                actual_output, final_code,
                teaching_angle, what_worked,
                what_failed, handoff, code_review,
                key_exchange, appears_in_future_labs)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (number, r['name'], r['phase'], r['lab'], r['course'],
             r['concept'], r['status'], r['prediction'],
             r['actual_output'], r['final_code'],
             r['teaching_angle'], r['what_worked'],
             r['what_failed'], r['handoff'], r['code_review'],
             r['key_exchange'], r['appears_in']))

        c.execute(
            '''INSERT INTO concepts
               (name, status, how_it_clicked,
                struggled_with, resolved_by,
                connects_to, project_number)
               VALUES (?,?,?,?,?,?,?)''',
            (r['concept'], r['concept_status'], r['how_clicked'],
             r['struggled'], r['resolved'], r['connects'], number))

        c.execute(
            '''INSERT INTO project_narrative
               (project_number, why_designed_this_way,
                gap_it_closes, what_response_revealed,
                connection_to_lab,
                what_breaks_without_this,
                what_next_project_must_do,
                curriculum_position_reasoning)
               VALUES (?,?,?,?,?,?,?,?)''',
            (number, r['why'], r['gap'], r['revealed'], r['lab_conn'],
             r['breaks'], r['next_must'], r['position']))

        w = r.get('weakness')
        if w:
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
                (r['concept'], w['specific'], w['failed'], w['worked'],
                 w['analogy'], w['wording'], w['exact_sub'],
                 w['recurrence'], number))

        pattern = r.get('pattern')
        if pattern:
            c.execute(
                'SELECT id FROM patterns WHERE pattern = ?',
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
                    (pattern, number, number, r['pattern_severity']))

        decision = r.get('decision')
        if decision:
            c.execute(
                '''INSERT INTO decisions
                   (project_number, concept,
                    angle_used, analogy_used, result)
                   VALUES (?,?,?,?,?)''',
                (number, r['concept'], *decision))

        if r['mind_update']:
            c.execute(
                '''INSERT INTO mind_model
                   (project_number, update_type, content)
                   VALUES (?,?,?)''',
                (r['total'], 'micro', r['mind_update']))
    conn.close()

    print(f"\nDatabase updated — Project {number} complete.")

    if r['mind_update']:
        md_path = os.path.expanduser(
            '~/projects/malloc-training/MIND_MODEL.md')
        with open(md_path, 'a') as f:
            f.write(
                f"\n\nMICRO UPDATE — After Project {r['total']}:\n"
                f"{r['mind_update']}\n")
        print("Mind model updated and written to MIND_MODEL.md.")

    print(
        f"git add . && git commit -m "
        f"'Project {number} complete — {r['concept']}' && git push")


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

    if not d.get('number', '').isdigit():
        print("\nERROR: Auto block has no valid 'number:' line.")
        print("Nothing was saved.")
        conn.close()
        sys.exit(1)
    number = int(d['number'])
    duplicate_guard(c, number)

    phase_raw = d.get('phase', '1')
    if phase_raw.isdigit() and 1 <= int(phase_raw) <= 5:
        phase = int(phase_raw)
    else:
        print(f"\nAuto block has phase {phase_raw!r}; expected 1-5.")
        phase = ask_int("Phase (1-5): ", 1, 5)

    r = {
        'number':         number,
        'name':           d.get('name', ''),
        'phase':          phase,
        'concept':        d.get('concept', ''),
        'status':         d.get('status', '').lower(),
        'prediction':     d.get('prediction', ''),
        'actual_output':  d.get('actual_output', ''),
        'what_worked':    d.get('what_worked', ''),
        'what_failed':    d.get('what_failed', ''),
        'teaching_angle': d.get('teaching_angle', ''),
        'handoff':        d.get('handoff', ''),
        'code_review':    d.get('code_review', ''),
        'key_exchange':   d.get('key_exchange', 'none'),
        'appears_in':     d.get('appears_in_future_labs', ''),
        'concept_status': d.get('concept_status', '').lower(),
        'how_clicked':    d.get('how_clicked', ''),
        'struggled':      d.get('struggled_with', ''),
        'resolved':       d.get('resolved_by', ''),
        'connects':       d.get('connects_to', ''),
        'why':            d.get('why_designed', ''),
        'gap':            d.get('gap_closed', ''),
        'revealed':       d.get('response_revealed', ''),
        'lab_conn':       d.get('lab_connection', ''),
        'breaks':         d.get('breaks_without', ''),
        'next_must':      d.get('next_must', ''),
        'position':       d.get('position_reasoning', ''),
    }

    # The block's lab must be a known lab; course always comes from it
    lab = find_lab(c, d.get('lab', ''))
    if not lab:
        print(f"\nAuto block has lab {d.get('lab', '')!r}, "
              f"which is not a known lab.")
        lab = ask_lab(c)
    r['lab'], r['course'] = lab

    if r['concept_status'] not in CONCEPT_STATUSES:
        print(f"\nAuto block has concept_status "
              f"{r['concept_status']!r}.")
        r['concept_status'] = ask_choice(
            "Concept status (owned/cracked/struggling): ",
            CONCEPT_STATUSES)

    r['final_code'] = ask_multiline("\nPaste final code.")

    sub = d.get('sub_projects_generated', 'no')
    if sub.strip().lower() == 'yes':
        r['weakness'] = {
            'specific':   ask_text("Specific misconception: "),
            'failed':     ask_text("Sub-projects that failed: "),
            'worked':     ask_text("Sub-project that worked: "),
            'analogy':    ask_text("Exact analogy that clicked: "),
            'wording':    ask_text("Exact wording that clicked: "),
            'recurrence': ask_text("Watch for recurrence: "),
            'exact_sub':  ask_multiline("Paste exact sub-project text."),
        }

    pattern = d.get('coding_pattern', '')
    if pattern and pattern.lower() != 'none':
        r['pattern'] = pattern
        r['pattern_severity'] = d.get('pattern_severity', '')

    if r['teaching_angle'] or d.get('analogy_used'):
        r['decision'] = (r['teaching_angle'],
                         d.get('analogy_used', ''),
                         d.get('decision_result', ''))

    r['total'] = next_total(c)
    r['mind_update'] = ask_mind_model(r['total'])

    save_project(conn, r)


# ─────────────────────────────────────────────
# INTERACTIVE MODE
# ─────────────────────────────────────────────

def update_interactive():
    conn = get_db()
    c = conn.cursor()

    print("=" * 45)
    print("POST-PROJECT UPDATE — INTERACTIVE")
    print("=" * 45)

    number = ask_int("Project number: ", 1)
    duplicate_guard(c, number)

    r = {'number': number}
    r['name']           = ask_text("Project name: ")
    r['phase']          = ask_int("Phase (1-5): ", 1, 5)
    r['lab'], r['course'] = ask_lab(c, "Lab name")
    r['concept']        = ask_text("Core concept: ")
    r['status']         = ask_text(
        "Status (owned/cracked/struggling): ").lower()
    r['prediction']     = ask_text("Your prediction was: ")
    r['actual_output']  = ask_text("Actual output was: ")
    r['what_worked']    = ask_text("What worked: ")
    r['what_failed']    = ask_text("What failed (or 'nothing'): ")
    r['teaching_angle'] = ask_text("Teaching angle used: ")

    # Handoff collected here — mid-session, not at token limit
    print("\nHandoff (generate this in Claude NOW while sharp):")
    r['handoff']        = ask_text("> ")

    r['code_review']    = ask_text("Code patterns observed: ")
    r['key_exchange']   = ask_text("Critical exchange (or 'none'): ")
    r['appears_in']     = ask_text("Appears in future labs: ")
    r['final_code']     = ask_multiline("\nPaste final code.")

    r['concept_status'] = ask_choice(
        "\nConcept status (owned/cracked/struggling): ", CONCEPT_STATUSES)
    r['how_clicked']    = ask_text("How it clicked: ")
    r['struggled']      = ask_text("Struggled with: ")
    r['resolved']       = ask_text("Resolved by: ")
    r['connects']       = ask_text("Connects to: ")

    r['why']       = ask_text("\nWhy designed this way: ")
    r['gap']       = ask_text("Gap it closes: ")
    r['revealed']  = ask_text("Response revealed: ")
    r['lab_conn']  = ask_text("Lab connection: ")
    r['breaks']    = ask_text("Breaks without this: ")
    r['next_must'] = ask_text("Next project must: ")
    r['position']  = ask_text("Position reasoning: ")

    if ask_yes_no("\nSub-projects generated? (yes/no): "):
        r['weakness'] = {
            'specific':   ask_text("Specific misconception: "),
            'failed':     ask_text("Sub-projects that failed: "),
            'worked':     ask_text("Sub-project that worked: "),
            'analogy':    ask_text("Exact analogy: "),
            'wording':    ask_text("Exact wording: "),
            'recurrence': ask_text("Watch for: "),
            'exact_sub':  ask_multiline("Paste exact sub-project text."),
        }

    pattern = ask_text("\nCoding pattern (or enter to skip): ")
    if pattern:
        r['pattern'] = pattern
        r['pattern_severity'] = ask_text("Severity (low/medium/high): ")

    r['decision'] = (ask_text("\nTeaching angle used: "),
                     ask_text("Analogy used: "),
                     ask_text("Result (landed/struggled/failed): "))

    r['total'] = next_total(c)
    r['mind_update'] = ask_mind_model(r['total'])

    save_project(conn, r)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if len(sys.argv) > 1 and sys.argv[1] == '--auto':
    if len(sys.argv) > 2:
        block = ' '.join(sys.argv[2:])
    else:
        block = ask_multiline("Paste auto update block.")
    update_auto(block)
else:
    update_interactive()
