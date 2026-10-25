"""
Test harness. Every test gets its own fake HOME containing a copy of the
repo at ~/projects/malloc-training and a brain.db built by init_db.py
from schema.sql. Scripts run as subprocesses, exactly as you run them.
The real brain.db is never touched.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
# Scripts run under the system python3 (the one with pytz), even when
# pytest itself runs from a virtualenv.
PYTHON = os.environ.get('MALLOC_PYTHON', '/usr/bin/python3')
if not os.path.exists(PYTHON):
    PYTHON = sys.executable
ACTIVE_LAB = 'L0 C Programming Lab'
ACTIVE_COURSE = 'CMU 15-213'
COPY_GLOBS = ['*.py', '*.sh', '*.md', '*.sql', '*.txt']


class Env:
    def __init__(self, tmp_path):
        self.home = tmp_path / 'home'
        self.proj = self.home / 'projects' / 'malloc-training'
        self.proj.mkdir(parents=True)
        for pattern in COPY_GLOBS:
            for f in REPO.glob(pattern):
                shutil.copy(f, self.proj / f.name)
        # Fake `code` so new_project.sh never opens an editor
        self.bin = tmp_path / 'bin'
        self.bin.mkdir()
        (self.bin / 'code').write_text('#!/bin/sh\nexit 0\n')
        (self.bin / 'code').chmod(0o755)
        self.db_path = self.proj / 'brain.db'
        r = self.run('init_db.py')
        assert r.returncode == 0, r.out

    def environ(self, **extra):
        env = {
            'HOME': str(self.home),
            'PATH': f"{self.bin}:{os.environ['PATH']}",
            'LANG': 'C.UTF-8',
        }
        env.update(extra)
        return env

    def _finish(self, r):
        r.out = r.stdout + r.stderr
        return r

    def run(self, script, *args, input='', env=None, timeout=30):
        """Run a repo script. input=None means stdin hits EOF at once."""
        r = subprocess.run(
            [PYTHON, str(self.proj / script), *args],
            input=input if input is not None else '',
            capture_output=True, text=True, cwd=self.home,
            env=self.environ(**(env or {})), timeout=timeout)
        return self._finish(r)

    def run_py(self, code, env=None):
        r = subprocess.run(
            [PYTHON, '-c', code],
            capture_output=True, text=True, cwd=self.home,
            env=self.environ(**(env or {})), timeout=30)
        return self._finish(r)

    def sh(self, script, *args, input=''):
        r = subprocess.run(
            ['bash', str(self.proj / script), *args],
            input=input, capture_output=True, text=True, cwd=self.home,
            env=self.environ(), timeout=30)
        return self._finish(r)

    # ── direct database access (foreign keys OFF, like an old db) ──
    def db(self):
        return sqlite3.connect(self.db_path)

    def q(self, sql, params=()):
        with self.db() as conn:
            return conn.execute(sql, params).fetchall()

    def ex(self, sql, params=()):
        conn = self.db()
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    def has_table(self, name):
        return bool(self.q("SELECT 1 FROM sqlite_master "
                           "WHERE type='table' AND name=?", (name,)))

    def add_lab(self, lab, course=ACTIVE_COURSE):
        if self.has_table('labs'):
            self.ex('INSERT OR IGNORE INTO labs (name, course) '
                    'VALUES (?, ?)', (lab, course))

    def add_project(self, n, lab=ACTIVE_LAB, days_ago=0,
                    status='owned', phase=1):
        self.add_lab(lab)
        self.ex(
            "INSERT INTO projects (number, name, phase, lab, course, "
            "concept, status, handoff, completed_at) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))",
            (n, f'Proj {n}', phase, lab, ACTIVE_COURSE, f'Concept {n}',
             status, f'handoff {n}', f'-{days_ago} days'))
        self.ex('INSERT INTO concepts (name, status, struggled_with, '
                'project_number) VALUES (?, ?, ?, ?)',
                (f'Concept {n}', status, 'sw', n))

    def add_projects(self, numbers, **kw):
        for n in numbers:
            self.add_project(n, **kw)

    def add_validation(self, n, result='pass'):
        self.ex('INSERT INTO external_validation (concept, '
                'project_number, source, result) VALUES (?, ?, ?, ?)',
                (f'Concept {n}', n, 'CS:APP', result))

    def add_transfer_exam(self, report, lab=ACTIVE_LAB):
        self.ex('INSERT INTO transfer_exams (phase, lab, course, '
                'adversarial_gap_report, status) VALUES (1, ?, ?, ?, ?)',
                (lab, ACTIVE_COURSE, report, 'passed'))


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def pytest_configure(config):
    # stepN = the fix step expected to make the test pass.
    # After step N: pytest -m "step1 or ... or stepN" must be all green.
    for n in range(1, 6):
        config.addinivalue_line('markers', f'step{n}: fixed in step {n}')


# ── input builders ───────────────────────────────────

def lines(*items):
    """Join answers into a stdin stream, one per line."""
    return ''.join(f'{i}\n' for i in items)


def auto_block(number, phase='1', lab=ACTIVE_LAB, **overrides):
    fields = {
        'number': number, 'name': f'Proj {number}', 'phase': phase,
        'lab': lab, 'course': ACTIVE_COURSE,
        'concept': f'Concept {number}', 'status': 'owned',
        'prediction': 'p', 'actual_output': 'a', 'what_worked': 'w',
        'what_failed': 'f', 'teaching_angle': f'angle {number}',
        'handoff': f'handoff {number}', 'code_review': 'cr',
        'key_exchange': 'none', 'appears_in_future_labs': 'malloc',
        'concept_status': 'owned', 'how_clicked': 'hc',
        'struggled_with': 'sw', 'resolved_by': 'rb', 'connects_to': 'ct',
        'why_designed': 'why', 'gap_closed': 'g',
        'response_revealed': 'r', 'lab_connection': 'lc',
        'breaks_without': 'b', 'next_must': 'n',
        'position_reasoning': 'pr', 'sub_projects_generated': 'no',
        'coding_pattern': 'none',
    }
    fields.update(overrides)
    return ''.join(f'{k}: {v}\n' for k, v in fields.items()) + 'END\n'


FINAL_CODE = lines('int main(void) { return 0; }', 'END')


def full_detail_input(number, replace=None, questions=('Q one', 'Q two')):
    s = lines(number)
    if replace is not None:
        s += lines(replace)
    for block in ('spec', 'micro', 'qs', 'answers', 'fails',
                  'wins', 'memory'):
        s += lines(block, 'END')
    for q in questions:
        s += lines(q, 'ans', 'correct', 'pass', 'no')
    return s + lines('')
