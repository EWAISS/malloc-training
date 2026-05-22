import os
import sys
import sqlite3
import subprocess

BASE = os.path.expanduser('~/projects/malloc-training')
DB_PATH = os.path.join(BASE, 'brain.db')

passed = []
failed = []

def check(name, condition, fix):
    if condition:
        passed.append(name)
        print(f"  PASS: {name}")
    else:
        failed.append(name)
        print(f"  FAIL: {name}")
        print(f"    FIX: {fix}")

def section(title):
    print()
    print(f"{'━'*50}")
    print(f"  {title}")
    print(f"{'━'*50}")

print("=" * 50)
print("COMPLETE SYSTEM VERIFICATION")
print("=" * 50)

# ─── FILES ───────────────────────────────────────
section("1. REQUIRED FILES")

required_files = [
    ('PROMPT.md',           'Paste complete prompt into it'),
    ('SESSION.md',          'Run step 13 from setup'),
    ('MIND_MODEL.md',       'Run step 13 from setup'),
    ('brain.db',            'Run step 5 from setup'),
    ('context.py',          'Run step 6 from setup'),
    ('update.py',           'Run step 7 from setup'),
    ('query_project.py',    'Run step 8 from setup'),
    ('store_handout.py',    'Run step 9 from setup'),
    ('get_handout.py',      'Run step 10 from setup'),
    ('update_exam.py',      'Run step 11 from setup'),
    ('start_session.py',    'Run start_session setup'),
    ('autograde.py',        'Run autograder setup'),
    ('db_check.py',         'Run fix 1 from failure modes'),
    ('adversary.py',        'Run fix 4 from failure modes'),
    ('mood_check.py',       'Run fix 7 from failure modes'),
    ('validate_concept.py', 'Run fix 8 from failure modes'),
    ('new_project.sh',      'Run step 12 from setup'),
    ('switch_account.sh',   'Run step 12 from setup'),
    ('maintain.sh',         'Run step 12 from setup'),
    ('estimate_tokens.sh',  'Run step 12 from setup'),
    ('EXTRACTION_PROMPT.txt','Run step 13 from setup'),
    ('handout_urls.txt',    'Run step 13 from setup'),
]

for filename, fix in required_files:
    path = os.path.join(BASE, filename)
    check(filename, os.path.exists(path), fix)

# ─── DIRECTORIES ─────────────────────────────────
section("2. REQUIRED DIRECTORIES")

required_dirs = [
    'phase1', 'phase2', 'phase3',
    'phase4', 'phase5', 'tests'
]

for d in required_dirs:
    path = os.path.join(BASE, d)
    check(f"dir: {d}", os.path.isdir(path),
          f"mkdir -p {path}")

# ─── PROMPT.MD CONTENT ───────────────────────────
section("3. PROMPT.MD CONTENT")

prompt_path = os.path.join(BASE, 'PROMPT.md')
if os.path.exists(prompt_path):
    size = os.path.getsize(prompt_path)
    check("PROMPT.md not empty",
          size > 1000,
          "Paste complete prompt into PROMPT.md")
    check("PROMPT.md has personal rule",
          'PERSONAL RULE' in open(prompt_path).read(),
          "Add PERSONAL RULE section to prompt")
    check("PROMPT.md has lab list",
          'CMU 15-213' in open(prompt_path).read(),
          "Add lab list to prompt")
    check("PROMPT.md has rules",
          'RULE 1' in open(prompt_path).read(),
          "Paste complete prompt — rules are missing")
else:
    check("PROMPT.md exists", False,
          "Create PROMPT.md and paste complete prompt")

# ─── SESSION.MD CONTENT ──────────────────────────
section("4. SESSION.MD CONTENT")

session_path = os.path.join(BASE, 'SESSION.md')
if os.path.exists(session_path):
    content = open(session_path).read()
    check("ACTIVE COURSE declared",
          'ACTIVE COURSE:' in content,
          "Add ACTIVE COURSE: CMU 15-213 to SESSION.md")
    check("ACTIVE LAB declared",
          'ACTIVE LAB:' in content,
          "Add ACTIVE LAB: L0 C Programming Lab to SESSION.md")
    check("PERSONAL RULE filled in",
          '[write your one sentence here]' not in content,
          "Write your personal rule in SESSION.md")
else:
    check("SESSION.md exists", False,
          "Run step 13 from setup")

# ─── DATABASE TABLES ─────────────────────────────
section("5. DATABASE TABLES")

required_tables = [
    'projects',
    'concepts',
    'patterns',
    'decisions',
    'weakness_patterns',
    'project_narrative',
    'project_full_detail',
    'mind_model',
    'transfer_exams',
    'adversarial_exams',
    'quiz_records',
    'lab_handouts',
    'autograde_results',
    'external_validation',
    'mood_logs',
]

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in c.fetchall()]
    conn.close()

    for table in required_tables:
        check(f"table: {table}",
              table in existing_tables,
              f"Run database setup — table {table} missing")
except Exception as e:
    check("database accessible", False, str(e))

# ─── PYTHON IMPORTS ───────────────────────────────
section("6. PYTHON DEPENDENCIES")

deps = [
    ('sqlite3',   'Built into Python — should always work'),
    ('subprocess','Built into Python — should always work'),
    ('pytz',      'pip install pytz --break-system-packages'),
    ('datetime',  'Built into Python — should always work'),
]

for mod, fix in deps:
    try:
        __import__(mod)
        check(f"import {mod}", True, fix)
    except ImportError:
        check(f"import {mod}", False, fix)

# ─── SYSTEM TOOLS ────────────────────────────────
section("7. SYSTEM TOOLS")

tools = [
    ('gcc',      'sudo apt install -y gcc'),
    ('git',      'sudo apt install -y git'),
    ('sqlite3',  'sudo apt install -y sqlite3'),
    ('valgrind', 'sudo apt install -y valgrind'),
    ('code',     'sudo snap install code --classic'),
]

for tool, fix in tools:
    result = subprocess.run(
        ['which', tool],
        capture_output=True)
    check(f"tool: {tool}",
          result.returncode == 0, fix)

# ─── GIT SETUP ───────────────────────────────────
section("8. GIT SETUP")

git_dir = os.path.join(BASE, '.git')
check("git initialized",
      os.path.isdir(git_dir),
      "cd ~/projects/malloc-training && git init")

hook_path = os.path.join(
    BASE, '.git', 'hooks', 'pre-commit')
check("pre-commit hook exists",
      os.path.exists(hook_path),
      "Run fix 1 to add pre-commit hook")

result = subprocess.run(
    ['git', 'remote', '-v'],
    cwd=BASE, capture_output=True, text=True)
check("git remote configured",
      'github.com' in result.stdout,
      "git remote add origin https://github.com/YOU/malloc-training")

# ─── SCRIPTS EXECUTABLE ──────────────────────────
section("9. SCRIPT PERMISSIONS")

scripts = [
    'new_project.sh',
    'switch_account.sh',
    'maintain.sh',
    'estimate_tokens.sh',
]

for script in scripts:
    path = os.path.join(BASE, script)
    if os.path.exists(path):
        check(f"executable: {script}",
              os.access(path, os.X_OK),
              f"chmod +x {path}")
    else:
        check(f"executable: {script}", False,
              f"File missing: {script}")

# ─── CONTEXT.PY RUNS ─────────────────────────────
section("10. SCRIPTS RUN WITHOUT ERROR")

scripts_to_test = [
    (['python3', 'context.py', '--mini'],
     'context.py --mini fails'),
    (['python3', 'db_check.py'],
     'db_check.py fails'),
    (['bash', 'maintain.sh'],
     'maintain.sh fails'),
    (['bash', 'estimate_tokens.sh'],
     'estimate_tokens.sh fails'),
]

for cmd, fix in scripts_to_test:
    result = subprocess.run(
        cmd, cwd=BASE,
        capture_output=True, text=True)
    check(f"runs: {' '.join(cmd)}",
          result.returncode == 0, fix)

# ─── AUTOGRADER TEST ─────────────────────────────
section("11. AUTOGRADER SMOKE TEST")

test_c = '/tmp/verify_autograde_test.c'
test_py = '/tmp/verify_autograde_tests.py'

with open(test_c, 'w') as f:
    f.write('''#include <stdio.h>
int main() {
    printf("hello autograde\\n");
    return 0;
}
''')

with open(test_py, 'w') as f:
    f.write('''TESTS = [
    {
        "name": "basic_output",
        "input": "",
        "expected_output": "hello autograde",
        "expected_exit": 0
    }
]
''')

result = subprocess.run(
    ['python3', 'autograde.py', '0',
     test_c, test_py],
    cwd=BASE,
    capture_output=True, text=True)
check("autograder runs correctly",
      result.returncode == 0,
      "Check autograde.py — smoke test failed")

# ─── SUMMARY ─────────────────────────────────────
print()
print("=" * 50)
print("VERIFICATION SUMMARY")
print("=" * 50)
print(f"  PASSED: {len(passed)}")
print(f"  FAILED: {len(failed)}")
print()

if failed:
    print("FAILED CHECKS:")
    for f in failed:
        print(f"  - {f}")
    print()
    print("Fix all failures before starting Project 1.")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED.")
    print("System is complete and working.")
    print()
    print("Two things remain:")
    print("1. Write your personal rule in SESSION.md")
    print("2. Run: python3 start_session.py")
    print("   Then open Claude and begin Project 1.")
    sys.exit(0)
