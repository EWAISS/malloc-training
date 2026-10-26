"""Run repo scripts in a fake HOME (the tests/conftest.py approach) and
save each output with the stdin that produced it. Never touches the repo.

Usage: python3 -I tools/run_samples.py <empty sandbox dir> [--repo PATH]
build_pack.py calls this itself; you rarely need to run it by hand.
Before anything runs, the state of the real brain.db, SESSION.md,
verification.txt and git status is saved to outputs/state_before.json,
so build_pack.py can prove the repo was not touched."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
REPO = Path(__file__).resolve().parent.parent
if '--repo' in args:
    i = args.index('--repo')
    REPO = Path(args[i + 1]).resolve()
    del args[i:i + 2]
S = Path(args[0]).resolve()
OUT = S / 'outputs'
PYTHON = '/usr/bin/python3' if os.path.exists('/usr/bin/python3') else sys.executable
LAB = 'L0 C Programming Lab'
COURSE = 'CMU 15-213'

if S.exists() and any(S.iterdir()):
    sys.exit(f'{S} is not empty; give an empty or new directory')


def repo_state():
    """sha256, mtime and git status of the files the scripts would write."""
    import hashlib
    state = {}
    for name in ('brain.db', 'SESSION.md', 'verification.txt'):
        p = REPO / name
        if p.exists():
            state[name] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                           'mtime_ns': p.stat().st_mtime_ns}
        else:
            state[name] = None
    state['git_status'] = subprocess.run(['git', 'status', '--porcelain'], cwd=REPO,
                                         capture_output=True, text=True).stdout
    return state


home = S / 'home'
proj = home / 'projects' / 'malloc-training'
proj.mkdir(parents=True)
OUT.mkdir()
(OUT / 'state_before.json').write_text(json.dumps(repo_state(), indent=1))
for pattern in ['*.py', '*.sh', '*.md', '*.sql', '*.txt']:
    for f in REPO.glob(pattern):
        if f.name in ('CONTEXT_PACK.md', 'PROMPTS_PACK.md'):
            continue
        shutil.copy(f, proj / f.name)
binp = S / 'bin'
binp.mkdir()
(binp / 'code').write_text('#!/bin/sh\nexit 0\n')
(binp / 'code').chmod(0o755)

ENV = {'HOME': str(home), 'PATH': f"{binp}:{os.environ['PATH']}",
       'LANG': 'C.UTF-8', 'GIT_CEILING_DIRECTORIES': str(S)}
runs = []


def run(label, cmd, stdin='', save=True):
    r = subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                       cwd=home, env=ENV, timeout=60)
    out = r.stdout + r.stderr
    if save:
        runs.append({'label': label, 'cmd': ' '.join(cmd[1:]) if cmd[0] == PYTHON
                     else ' '.join(cmd), 'stdin': stdin, 'out': out,
                     'rc': r.returncode})
    return r, out


def py(script, *args):
    return [PYTHON, str(proj / script), *args]


def sh(script, *args):
    return ['bash', str(proj / script), *args]


r, out = run('init_db', py('init_db.py'), save=False)
assert r.returncode == 0, out

PROJECTS = [
    dict(number=1, name='Bytes at an address', concept='A variable is a named region of bytes at a real address',
         status='owned', what_failed='Predicted &x and x print the same value',
         teaching_angle='Print every address and sizeof before reasoning',
         handoff='Project 2 must make the student draw the stack frame before writing any pointer code.',
         struggled_with='address vs value', how_clicked='Mailbox analogy', sub='no', pattern='none'),
    dict(number=2, name='Pointers are integers', concept='A pointer is an integer holding an address',
         status='owned', what_failed='Dereferenced an uninitialised pointer',
         teaching_angle='Hex dump of the pointer variable itself',
         handoff='Project 3 must force pointer arithmetic on int* vs char* with predicted addresses.',
         struggled_with='pointer value vs pointee', how_clicked='Hex dump of the 8 pointer bytes', sub='yes',
         pattern='none'),
    dict(number=3, name='Pointer arithmetic scales', concept='p+1 moves by sizeof(*p) bytes',
         status='owned', what_failed='Assumed p+1 always adds 1 byte',
         teaching_angle='Print p and p+1 for char*, int*, double*',
         handoff='Project 4 must have the student predict sizeof for arrays vs pointers passed to functions.',
         struggled_with='scaling by element size', how_clicked='Ruler with different tick widths', sub='no',
         pattern='casts away const without comment'),
]

for p in PROJECTS:
    block = (f"number: {p['number']}\nname: {p['name']}\nphase: 1\nlab: {LAB}\ncourse: {COURSE}\n"
             f"concept: {p['concept']}\nstatus: {p['status']}\nprediction: wrote line-by-line prediction\n"
             f"actual_output: matched except one line\nwhat_worked: predicting addresses first\n"
             f"what_failed: {p['what_failed']}\nteaching_angle: {p['teaching_angle']}\n"
             f"handoff: {p['handoff']}\ncode_review: consistent naming, no NULL checks yet\n"
             f"key_exchange: none\nappears_in_future_labs: Malloc Lab block headers\n"
             f"concept_status: owned\nhow_clicked: {p['how_clicked']}\n"
             f"struggled_with: {p['struggled_with']}\nresolved_by: second analogy\n"
             f"connects_to: project {p['number'] - 1 or 1}\nwhy_designed: builds byte-level view\n"
             f"gap_closed: {p['struggled_with']}\nresponse_revealed: thinks in variables not bytes\n"
             f"lab_connection: queue nodes hold pointers\nbreaks_without: malloc headers make no sense\n"
             f"next_must: {p['handoff']}\nposition_reasoning: prerequisite for next\n"
             f"sub_projects_generated: {p['sub']}\ncoding_pattern: {p['pattern']}\n"
             f"pattern_severity: minor\nanalogy_used: {p['how_clicked']}\ndecision_result: worked\nEND\n")
    stdin = block + 'int main(void) { return 0; }\nEND\n'
    if p['sub'] == 'yes':
        stdin += ('Treats the pointer value as the pointee\nTwo printf-only drills\nHex dump drill\n'
                  'Mailbox number vs mail inside\nThe pointer is just 8 bytes holding a number\n'
                  'Confusing *p with p when passing to functions\nSub-project 2a: print &p, p, *p\nEND\n')
    r, out = run(f"update.py --auto (project {p['number']})", py('update.py', '--auto'), stdin,
                 save=(p['number'] == 1))
    assert r.returncode == 0, out

# Normal outputs
run('context.py (full)', py('context.py'))
run('context.py --mini', py('context.py', '--mini'))
run('start_session.py', py('start_session.py'), '8\nyes\n1\n')
shutil.copy(proj / 'verification.txt', OUT / 'verification.txt')
run('mood_check.py', py('mood_check.py'), '8\nyes\n1\n')
run('curriculum_status.py', py('curriculum_status.py'))
run('estimate_tokens.sh', sh('estimate_tokens.sh'))
run('switch_account.sh (stopped at "Ready to push?" — answered no)', sh('switch_account.sh'), 'yes\nno\n')

# Projects 4 and 5 so the 5th triggers the mind-model prompt
for n in (4, 5):
    block = (f"number: {n}\nname: Proj {n}\nphase: 1\nlab: {LAB}\ncourse: {COURSE}\nconcept: Concept {n}\n"
             f"status: owned\nteaching_angle: angle {n}\nhandoff: handoff {n}\nconcept_status: owned\n"
             f"struggled_with: sw {n}\nsub_projects_generated: no\ncoding_pattern: none\nEND\n")
    stdin = block + 'int main(void) { return 0; }\nEND\n'
    if n == 5:
        stdin += 'MICRO UPDATE — After Project 5: (fake paragraph for this sample)\nEND\n'
    r, out = run(f'update.py --auto (project {n}{", 5th project — mind model prompt" if n == 5 else ""})',
                 py('update.py', '--auto'), stdin, save=(n == 5))
    assert r.returncode == 0, out

# Transfer exam (fake, via SQL as conftest.add_transfer_exam does) with no
# adversarial report, so the context gate and adversary.py show their text
import sqlite3
conn = sqlite3.connect(proj / 'brain.db')
conn.execute("INSERT INTO transfer_exams (phase, lab, course, status) VALUES (1, ?, ?, 'passed')", (LAB, COURSE))
conn.commit()
conn.close()
run('context.py while a transfer exam has no adversarial report (gate)', py('context.py'))
run('adversary.py', py('adversary.py'), '\nYou cannot explain why p+1 on an int* skips 4 bytes without recalling it.\nEND\n')

# lab_transition: prompt printed, then cancelled at the paste step (EOF)
run('lab_transition.py (cancelled with EOF at the paste step — nothing saved)',
    py('lab_transition.py'), 'L1 Data Lab\n\n')

# Gap gate: age every project 10 days
conn = sqlite3.connect(proj / 'brain.db')
conn.execute("UPDATE projects SET completed_at = datetime('now', '-10 days')")
for t in ('project_full_detail', 'quiz_records', 'mood_logs'):
    try:
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t})')]
        for col in cols:
            if col.endswith('_at') or col in ('logged_at', 'created_at', 'date'):
                conn.execute(f"UPDATE {t} SET {col} = datetime('now', '-10 days')")
    except sqlite3.Error:
        pass
conn.commit()
conn.close()
run('context.py --mini with the gap gate active (projects aged 10 days)', py('context.py', '--mini'))

(OUT / 'runs.json').write_text(json.dumps(runs, indent=1, ensure_ascii=False))
print(f'{len(runs)} runs saved')
for r in runs:
    print(r['label'], 'rc=', r['rc'], len(r['out']))
