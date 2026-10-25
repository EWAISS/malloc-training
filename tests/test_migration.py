"""
init_db.py migration from schema version 0 (the pre-constraints schema,
frozen in tests/fixtures/schema_v0.sql) to version 1.
"""
import shutil
import sqlite3

import pytest

from conftest import ACTIVE_COURSE, ACTIVE_LAB, REPO

pytestmark = pytest.mark.step3

V0_SCHEMA = (REPO / 'tests' / 'fixtures' / 'schema_v0.sql').read_text()


def make_v0(env, rows):
    """Replace the test brain.db with a version-0 database."""
    env.db_path.unlink()
    conn = sqlite3.connect(env.db_path)
    conn.executescript(V0_SCHEMA)
    for sql, params in rows:
        conn.execute(sql, params)
    conn.commit()
    conn.close()


def project(n, lab=ACTIVE_LAB):
    return [
        ("INSERT INTO projects (number, name, lab, course, concept, "
         "status, handoff) VALUES (?, ?, ?, ?, ?, 'owned', 'h')",
         (n, f'P{n}', lab, ACTIVE_COURSE, f'C{n}')),
        ("INSERT INTO concepts (name, status, project_number) "
         "VALUES (?, 'owned', ?)", (f'C{n}', n)),
    ]


TYPICAL = (
    project(1) + project(2, lab='  l0 c programming LAB ') + [
        ("INSERT INTO project_full_detail (project_number) VALUES (1)", ()),
        ("INSERT INTO quiz_records (project_number, question_number, "
         "lab) VALUES (1, 1, ?)", (ACTIVE_LAB,)),
        ("INSERT INTO external_validation (concept, project_number, "
         "result) VALUES ('C1', 1, ' PASS ')", ()),
        ("INSERT INTO transfer_exams (phase, lab, adversarial_gap_report)"
         " VALUES (1, ?, 'none' || char(10))", (ACTIVE_LAB,)),
        ("INSERT INTO adversarial_exams (phase, lab, gap_found, resolved)"
         " VALUES (1, ?, 'No', 'pending')", (ACTIVE_LAB,)),
        ("INSERT INTO adversarial_exams (phase, lab, gap_found, resolved)"
         " VALUES (1, ?, 'yes', 'pending')", (ACTIVE_LAB,)),
    ])


def test_migrates_v0_and_keeps_every_row(env):
    make_v0(env, TYPICAL)
    before = {t: env.q(f'SELECT COUNT(*) FROM {t}')[0][0]
              for t in ('projects', 'concepts', 'quiz_records',
                        'external_validation', 'transfer_exams',
                        'adversarial_exams')}

    r = env.run('init_db.py')
    assert r.returncode == 0, r.out
    assert 'Backup:' in r.out
    assert list(env.proj.glob('brain.db.bak-*'))

    assert env.q('PRAGMA user_version') == [(1,)]
    for t, n in before.items():
        assert env.q(f'SELECT COUNT(*) FROM {t}')[0][0] == n, t
    assert env.q('SELECT name, course FROM labs') == \
        [(ACTIVE_LAB, ACTIVE_COURSE)]
    # Lab spellings merged onto the canonical name
    assert env.q('SELECT DISTINCT lab FROM projects') == [(ACTIVE_LAB,)]
    # Values the new CHECKs reject were normalised, not dropped
    assert env.q('SELECT adversarial_gap_report FROM transfer_exams') \
        == [(None,)]
    assert env.q('SELECT gap_found, resolved FROM adversarial_exams '
                 'ORDER BY id') == [('no', 'n/a'), ('yes', 'pending')]
    assert env.q('SELECT result FROM external_validation') == [('pass',)]
    assert env.q('PRAGMA foreign_key_check') == []


def test_migrated_db_enforces_constraints(env):
    make_v0(env, TYPICAL)
    assert env.run('init_db.py').returncode == 0
    conn = sqlite3.connect(env.db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO concepts (name, project_number) "
                     "VALUES ('x', 42)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projects (number, lab) VALUES (9, 'L0')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projects (number) VALUES (1)")
    # Replacing full detail takes its quiz records with it
    conn.execute('DELETE FROM project_full_detail WHERE project_number = 1')
    assert conn.execute('SELECT COUNT(*) FROM quiz_records').fetchone() \
        == (0,)
    conn.close()


def test_migration_refuses_bad_data_and_changes_nothing(env):
    rows = project(1) + [
        ("INSERT INTO projects (number, name, lab) VALUES (1, 'dup', ?)",
         (ACTIVE_LAB,)),
        ("INSERT INTO concepts (name, project_number) VALUES ('x', 1)", ()),
    ]
    make_v0(env, rows)
    original = env.db_path.read_bytes()

    r = env.run('init_db.py')
    assert r.returncode == 1
    assert 'MIGRATION FAILED' in r.out and 'brain.db is unchanged' in r.out
    assert env.db_path.read_bytes() == original
    assert env.q('PRAGMA user_version') == [(0,)]


def test_db_check_refuses_an_unmigrated_db(env):
    make_v0(env, project(1))
    r = env.run('db_check.py')
    assert r.returncode == 1
    assert 'init_db.py' in r.out


def test_init_db_is_idempotent(env):
    assert env.run('init_db.py').returncode == 0
    assert env.run('init_db.py').returncode == 0
    assert env.q('PRAGMA user_version') == [(1,)]
    assert env.q('SELECT COUNT(*) FROM labs') == [(1,)]


def test_migrates_a_copy_of_the_real_brain_db(env):
    """The actual brain.db in the repo, migrated on a copy."""
    real = REPO / 'brain.db'
    if not real.exists():
        pytest.skip('no brain.db in the repo')
    env.db_path.unlink()
    shutil.copy(real, env.db_path)
    r = env.run('init_db.py')
    assert r.returncode == 0, r.out
    assert env.q('PRAGMA user_version') == [(1,)]
    r = env.run('db_check.py')
    assert r.returncode == 0, r.out
