"""
One test (or group) per bug in the phase-1 audit table.
Test names carry the bug number from that table.
"""
import signal
import subprocess
import sys
import time

import pytest

from conftest import (ACTIVE_COURSE, ACTIVE_LAB, FINAL_CODE, PYTHON, REPO,
                      auto_block, full_detail_input, lines)

CANCELLED = 'Cancelled, nothing saved.'
SHARP = lines('8', 'yes', '1')   # sleep, ate, days since rest


def step(n):
    return getattr(pytest.mark, f'step{n}')


def table_counts(env):
    tables = [r[0] for r in env.q(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'")]
    return {t: env.q(f'SELECT COUNT(*) FROM {t}')[0][0] for t in tables}


def add_pending_gap(env):
    env.ex("INSERT INTO adversarial_exams (phase, lab, course, gap_found, "
           "gap_location, resolved) VALUES (1, ?, ?, 'yes', 'loc', "
           "'pending')", (ACTIVE_LAB, ACTIVE_COURSE))


# ─────────────────────────────────────────────
# Bug 1 — Ctrl+D / Ctrl+C give a traceback
# ─────────────────────────────────────────────

def seed_for(env, script):
    """State each script needs before it reaches its first prompt."""
    if script == 'adversary.py':
        env.add_project(1)
        env.add_transfer_exam(None)
    if script == 'resolve_gap.py':
        add_pending_gap(env)


EOF_SCRIPTS = [
    ('update.py',),
    ('update.py', '--auto'),
    ('start_session.py',),
    ('mood_check.py',),
    ('update_exam.py',),
    ('validate_concept.py',),
    ('lab_transition.py',),
    ('query_project.py',),
    ('store_handout.py',),
    ('get_handout.py',),
    ('update_full_detail.py',),
    ('resolve_gap.py',),
    ('adversary.py',),
    ('context.py', '--clear-gap-gate'),
]


@step(1)
@pytest.mark.parametrize('cmd', EOF_SCRIPTS, ids=' '.join)
def test_bug01_eof_at_first_prompt_cancels_cleanly(env, cmd):
    seed_for(env, cmd[0])
    r = env.run(*cmd, input=None)
    assert 'Traceback' not in r.out
    assert CANCELLED in r.out
    assert r.returncode == 1


@step(1)
def test_bug01_ctrl_c_cancels_cleanly(env):
    p = subprocess.Popen(
        [PYTHON, str(env.proj / 'mood_check.py')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, env=env.environ())
    time.sleep(1.0)              # let it reach the first prompt
    p.send_signal(signal.SIGINT)
    out, _ = p.communicate(timeout=10)
    assert 'Traceback' not in out
    assert CANCELLED in out
    assert p.returncode == 1


# Full valid answer streams. Cutting each one short at every prompt
# must cancel cleanly and leave the database exactly as it was.
def full_streams():
    return {
        'update.py': lines(
            '1', 'Proj 1', '1', ACTIVE_LAB, 'Concept 1', 'owned',
            'pred', 'out', 'worked', 'failed', 'angle', 'handoff',
            'review', 'none', 'malloc') + FINAL_CODE + lines(
            'owned', 'clicked', 'struggled', 'resolved', 'connects',
            'why', 'gap', 'revealed', 'labconn', 'breaks', 'next',
            'position', 'no', '', 'angle', 'analogy', 'landed'),
        'update.py --auto': auto_block(1) + FINAL_CODE,
        'update_exam.py transfer': lines(
            '1', '1', ACTIVE_LAB, 'scen', 'END', 'impl', 'END',
            'eval', 'END', 'none', 'gap report', 'END', 'passed'),
        'update_exam.py adversarial': lines(
            '2', '1', ACTIVE_LAB, 'concepts', 'q', 'END', 'a', 'END',
            'yes', 'location', 'no'),
        'validate_concept.py': lines(
            '1', 'CS:APP 2.1', 'q', 'END', 'a', 'END', 'c', 'END', 'pass'),
        'update_full_detail.py': full_detail_input(1),
        'resolve_gap.py': lines(
            '1', 'fixed', 'END', 'yes', 'yes', 'c', 'm', 'a', 'w',
            'watch', '1'),
        'adversary.py': lines('', 'gap report', 'END'),
        'lab_transition.py': lines(
            'L1 Data Lab', ACTIVE_COURSE, 'OWNED: x', 'END'),
        'store_handout.py': lines(ACTIVE_LAB) + lines('x', 'END') * 9,
        'context.py --clear-gap-gate': lines('yes'),
    }


# Streams that answer the step-3 lab prompt (no "Course" question) only
# line up once step 3 lands; the rest need only step 2's transactions.
STEP3_STREAMS = {'update.py', 'update_exam.py transfer',
                 'update_exam.py adversarial', 'store_handout.py',
                 'lab_transition.py'}


@pytest.mark.parametrize('name', [
    pytest.param(n, marks=step(3 if n in STEP3_STREAMS else 2))
    for n in full_streams()])
def test_bugs_01_02_04_12_eof_at_every_prompt_saves_nothing(env, name):
    script, *rest = name.split(' ')
    args = [a for a in rest if a.startswith('--')]
    if script in ('update_full_detail.py', 'validate_concept.py',
                  'resolve_gap.py'):
        env.add_project(1)
    seed_for(env, script)
    stream = full_streams()[name].splitlines(keepends=True)
    before = table_counts(env)

    for k in range(len(stream)):
        r = env.run(script, *args, input=''.join(stream[:k]))
        where = f'EOF after {k} lines'
        assert 'Traceback' not in r.out, f'{where}:\n{r.out}'
        assert CANCELLED in r.out, f'{where}:\n{r.out}'
        assert r.returncode == 1, where
        assert table_counts(env) == before, where

    # Sanity: the complete stream is valid and does save
    r = env.run(script, *args, input=''.join(stream))
    assert r.returncode == 0, r.out
    assert table_counts(env) != before


# ─────────────────────────────────────────────
# Bug 2 — update_full_detail says "saved", then loses everything
# ─────────────────────────────────────────────

@step(2)
def test_bug02_full_detail_eof_in_quiz_loop_claims_nothing(env):
    env.add_project(2)
    stream = full_detail_input(2).split('Q one\n')[0] + 'Q one\n'
    r = env.run('update_full_detail.py', input=stream)
    assert 'Full detail saved' not in r.out
    assert CANCELLED in r.out
    assert env.q('SELECT COUNT(*) FROM project_full_detail')[0][0] == 0


# ─────────────────────────────────────────────
# Bug 3 — replacing full detail duplicates quiz records
# ─────────────────────────────────────────────

@step(3)
def test_bug03_replace_full_detail_does_not_duplicate_quiz(env):
    env.add_project(1)
    r1 = env.run('update_full_detail.py', input=full_detail_input(1))
    assert r1.returncode == 0, r1.out
    r2 = env.run('update_full_detail.py',
                 input=full_detail_input(1, replace='yes'))
    assert r2.returncode == 0, r2.out
    assert env.q('SELECT COUNT(*) FROM project_full_detail')[0][0] == 1
    assert env.q('SELECT question_number, question_text FROM quiz_records '
                 'ORDER BY question_number') == [(1, 'Q one'), (2, 'Q two')]


# ─────────────────────────────────────────────
# Bug 4 — resolve_gap crashes on a typo and loses the resolution
# ─────────────────────────────────────────────

@step(1)
def test_bug04_resolve_gap_reasks_on_bad_numbers(env):
    env.add_projects(range(1, 7))
    add_pending_gap(env)
    r = env.run('resolve_gap.py', input=lines(
        'one', '1', 'repaired via project 6', 'END', 'yes', 'yes',
        'c', 'm', 'a', 'w', 'watch', 'six', '6'))
    assert 'Traceback' not in r.out, r.out
    assert r.returncode == 0, r.out
    assert env.q('SELECT resolved, resolution FROM adversarial_exams') == \
        [('yes', 'repaired via project 6')]
    assert env.q('SELECT project_number FROM weakness_patterns') == [(6,)]


# ─────────────────────────────────────────────
# Bug 5 — exam lab typo deadlocks adversary.py / context.py
# ─────────────────────────────────────────────

@step(3)
def test_bug05_exam_lab_typo_cannot_deadlock(env):
    env.add_project(1)
    r = env.run('update_exam.py', input=lines(
        '1', '1', 'L0', ACTIVE_LAB, 'scen', 'END', 'impl', 'END',
        'eval', 'END', 'none', 'END', 'passed'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT lab FROM transfer_exams') == [(ACTIVE_LAB,)]

    r = env.run('adversary.py', input=lines('', 'gap X', 'END'))
    assert 'No owned concepts' not in r.out
    r = env.run('context.py')
    assert 'BLOCKED' not in r.out, r.out


@step(3)
def test_bug05_lab_name_is_normalised(env):
    env.add_project(1)
    r = env.run('update_exam.py', input=lines(
        '1', '1', '  l0 c programming LAB ', 'scen', 'END', 'impl',
        'END', 'eval', 'END', 'none', 'report', 'END', 'passed'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT lab, course FROM transfer_exams') == \
        [(ACTIVE_LAB, ACTIVE_COURSE)]


# ─────────────────────────────────────────────
# Bug 6 — "no gap found" still recorded as a pending gap
# ─────────────────────────────────────────────

@step(3)
def test_bug06_no_gap_is_not_pending(env):
    r = env.run('update_exam.py', input=lines(
        '2', '1', ACTIVE_LAB, 'concepts', 'q', 'END', 'a', 'END', 'no'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT COUNT(*) FROM adversarial_exams')[0][0] == 1
    assert env.q("SELECT COUNT(*) FROM adversarial_exams "
                 "WHERE resolved = 'pending'")[0][0] == 0
    assert 'No pending gaps' in env.run('resolve_gap.py').out


# ─────────────────────────────────────────────
# Bug 7 — out-of-range list number becomes the concept name
# ─────────────────────────────────────────────

@step(3)
def test_bug07_validation_needs_a_real_concept(env):
    env.add_projects([1, 2, 3])
    r = env.run('validate_concept.py', input=lines(
        '12', 'No such concept', '1', 'CS:APP 2.1',
        'q', 'END', 'a', 'END', 'c', 'END', 'pass'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT concept, project_number, result '
                 'FROM external_validation') == [('Concept 1', 1, 'pass')]


@step(3)
def test_bug07_bogus_validation_does_not_clear_debt(env):
    env.add_projects(range(1, 11))
    for _ in range(2):
        try:
            env.ex("INSERT INTO external_validation (concept, "
                   "project_number, result) VALUES ('12', 12, 'pass')")
        except Exception:
            pass   # the schema refusing it is also a fix
    r = env.run('start_session.py', input=SHARP)
    assert 'VALIDATION DEBT DETECTED' in r.out, r.out


# ─────────────────────────────────────────────
# Bug 8 — Q5 leaks the hidden next project number
# ─────────────────────────────────────────────

@step(4)
def test_bug08_validation_debt_hides_next_number_everywhere(env):
    env.add_projects(range(1, 11))
    r = env.run('start_session.py', input=SHARP)
    assert 'VALIDATION DEBT DETECTED' in r.out, r.out
    assert 'Project 11' not in r.out
    assert 'Next project   : 11' not in r.out


# ─────────────────────────────────────────────
# Bug 9 — start_session ignores the gap gate
# ─────────────────────────────────────────────

@step(4)
def test_bug09_start_session_applies_gap_gate(env):
    env.add_projects(range(1, 11), days_ago=10)
    env.add_validation(1)
    env.add_validation(2)
    assert 'GAP GATE ACTIVE' in env.run('context.py').out
    r = env.run('start_session.py', input=SHARP)
    assert 'GAP GATE ACTIVE' in r.out, r.out
    assert 'Next project   : 11' not in r.out
    assert 'Project 11' not in r.out


# ─────────────────────────────────────────────
# Bug 10 — db_check and context.py disagree on a missing report
# ─────────────────────────────────────────────

@step(3)
@pytest.mark.parametrize('report', ['none\n', 'None', '   ', 'NONE '])
def test_bug10_db_check_and_context_agree(env, report):
    env.add_project(1)
    try:
        env.add_transfer_exam(report)
    except Exception:
        return   # the schema refusing the ambiguous value is also a fix
    blocked_context = 'BLOCKED' in env.run('context.py').out
    blocked_db_check = env.run('db_check.py').returncode != 0
    assert blocked_context and blocked_db_check


@step(3)
@pytest.mark.parametrize('report_lines', [['none', ''], ['None'], ['  ']])
def test_bug10_update_exam_none_report_is_missing(env, report_lines):
    env.add_project(1)
    r = env.run('update_exam.py', input=lines(
        '1', '1', ACTIVE_LAB, 'scen', 'END', 'impl', 'END', 'eval',
        'END', 'none', *report_lines, 'END', 'passed'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT adversarial_gap_report FROM transfer_exams') \
        == [(None,)]
    assert env.run('db_check.py').returncode != 0
    assert 'BLOCKED' in env.run('context.py').out
    r = env.run('start_session.py', input=SHARP)
    assert r.returncode != 0
    assert 'Next project' not in r.out


# ─────────────────────────────────────────────
# Bug 11 — db_check compares counts only
# ─────────────────────────────────────────────

@step(3)
@pytest.mark.parametrize('target', [42, 2])
def test_bug11_concept_on_wrong_project_is_caught(env, target):
    env.add_projects([1, 2, 3])
    env.ex('UPDATE concepts SET project_number = ? '
           'WHERE project_number = 3', (target,))
    r = env.run('db_check.py')
    assert r.returncode == 1, r.out
    assert 'Project 3' in r.out


# ─────────────────────────────────────────────
# Bug 12 — mind model prompt dies after the project is committed
# ─────────────────────────────────────────────

@step(2)
def test_bug12_mind_model_cancel_saves_nothing_and_retries(env):
    env.add_projects([1, 2, 3, 4])
    r = env.run('update.py', '--auto', input=auto_block(5) + FINAL_CODE)
    assert 'Traceback' not in r.out
    assert env.q('SELECT COUNT(*) FROM projects')[0][0] == 4

    r = env.run('update.py', '--auto', input=auto_block(5) + FINAL_CODE
                + lines('MICRO UPDATE — After Project 5: thinks in bytes',
                        'END'))
    assert r.returncode == 0, r.out
    assert env.q('SELECT COUNT(*) FROM projects')[0][0] == 5
    assert env.q('SELECT COUNT(*) FROM mind_model')[0][0] == 1
    assert 'thinks in bytes' in (env.proj / 'MIND_MODEL.md').read_text()


# ─────────────────────────────────────────────
# Bug 13 — bad phase in the auto block crashes update.py
# ─────────────────────────────────────────────

@step(1)
@pytest.mark.parametrize('phase',['', '1 (pointers)', '9'])
def test_bug13_bad_phase_reasks(env, phase):
    r = env.run('update.py', '--auto',
                input=auto_block(1, phase=phase) + lines('1') + FINAL_CODE)
    assert 'Traceback' not in r.out
    assert r.returncode == 0, r.out
    assert env.q('SELECT number, phase FROM projects') == [(1, 1)]


# ─────────────────────────────────────────────
# Bug 14 — new_project.sh reads 08/09 as octal
# ─────────────────────────────────────────────

@step(5)
@pytest.mark.parametrize('number,expected', [
    ('8', 'project08.c'), ('08', 'project08.c'), ('09', 'project09.c'),
    ('12', 'project12.c')])
def test_bug14_new_project_numbering(env, number, expected):
    r = env.sh('new_project.sh', '1', number)
    assert r.returncode == 0, r.out
    assert (env.proj / 'phase1' / expected).exists()
    assert not (env.proj / 'phase1' / 'project00.c').exists()


@step(5)
def test_bug14_new_project_rejects_non_numbers(env):
    r = env.sh('new_project.sh', '1', 'abc')
    assert r.returncode != 0
    assert not (env.proj / 'phase1' / 'project00.c').exists()


# ─────────────────────────────────────────────
# Bug 15 — curriculum_status miscounts with off-curriculum projects
# ─────────────────────────────────────────────

@step(5)
def test_bug15_pending_ignores_off_curriculum_projects(env):
    env.add_projects(list(range(1, 11)) + [99])
    out = env.run('curriculum_status.py').out
    assert 'Completed      : 10' in out
    assert 'Pending        : 20' in out
    assert '33%' in out


# ─────────────────────────────────────────────
# Bug 16 — "no lab transition" warning fires for the active lab
# ─────────────────────────────────────────────

@step(4)
def test_bug16_no_transition_warning_for_active_lab(env):
    env.add_projects(range(1, 11))
    assert 'NO LAB TRANSITION' not in env.run('db_check.py').out


@step(4)
def test_bug16_still_warns_for_a_finished_lab(env):
    env.add_projects(range(101, 111), lab='L1 Data Lab')
    assert 'NO LAB TRANSITION' in env.run('db_check.py').out


# ─────────────────────────────────────────────
# Bug 17 — without pytz, time since last project is off by the UTC offset
# ─────────────────────────────────────────────

@step(5)
@pytest.mark.parametrize('tz',['Africa/Cairo', 'America/New_York', 'UTC'])
def test_bug17_time_since_without_pytz(env, tz):
    env.add_project(1)
    env.ex("UPDATE projects SET completed_at = datetime('now', '-1 hour')")
    script = env.proj / 'context.py'
    code = (
        "import sys; sys.modules['pytz'] = None; "
        f"sys.path.insert(0, {str(env.proj)!r}); "
        f"sys.argv = [{str(script)!r}]; "
        f"exec(compile(open({str(script)!r}).read(), {str(script)!r}, "
        "'exec'), {'__name__': '__main__'})")
    r = env.run_py(code, env={'TZ': tz})
    assert 'Time since last project: 1 hours' in r.out, r.out


# ─────────────────────────────────────────────
# Bug 18 — switch_account.sh `git add .` sweeps up untracked files
# ─────────────────────────────────────────────

@step(5)
@pytest.mark.parametrize('path',['handouts/cprogramminglab.pdf',
                                  'verification.txt'])
def test_bug18_generated_files_are_ignored(path):
    r = subprocess.run(['git', '-C', str(REPO), 'check-ignore', '-q',
                        '--no-index', path])
    assert r.returncode == 0, f'{path} is not in .gitignore'
