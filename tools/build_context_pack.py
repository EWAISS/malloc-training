"""
build_context_pack.py — builds CONTEXT_PACK.md: a read-only snapshot of
the whole repo (tree, git state, every core file and script verbatim,
handouts, code, curriculum, inferences) for a session that cannot open it.

Usage (from anywhere):
  python3 -I tools/build_context_pack.py [--out PATH] [--repo PATH]

Facts are gathered when it runs. Verbatim blocks are parsed back out of
the finished pack and compared byte for byte with their sources. The
per-script notes and section 8 in tools/context_pack_template.md are
hand-written for the commit in its WRITTEN-FOR line: when HEAD is newer
the build warns, and a script with no note stops it.
"""
import ast
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# -I leaves the script's own directory off sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packlib import (extra_block, file_block, git, head_commit,
                     verify_blocks)

HERE = Path(__file__).resolve().parent
args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name)
        value = args[i + 1]
        del args[i:i + 2]
        return value
    return default


REPO = Path(opt('--repo', HERE.parent)).resolve()
OUT_PATH = Path(opt('--out', REPO / 'CONTEXT_PACK.md')).resolve()
PACKS = ('CONTEXT_PACK.md', 'PROMPTS_PACK.md')
SKIP_DIRS = {'.git', '__pycache__', '.pytest_cache'}
tmpl = (HERE / 'context_pack_template.md').read_text()

written_for = re.search(r'<!-- WRITTEN-FOR (\w+) -->\n', tmpl)
tmpl = tmpl.replace(written_for.group(0), '')
HEAD = head_commit(REPO)
if not HEAD.startswith(written_for.group(1)):
    print(f"WARNING: the template notes were written for {written_for.group(1)}; HEAD is {HEAD}.\n"
          f"  Verbatim blocks are re-read and exact, but review the per-script notes and section 8.")

extra = {}       # command output shown verbatim, checked like files
held = []        # verbatim blocks, kept out of the text until the end


def hold(block):
    """A token for block, so marker replacement never touches file
    content (the tools' own source contains @@ markers)."""
    held.append(block)
    return f'\x00{len(held) - 1}\x00'


def unhold(s):
    return re.sub('\x00(\\d+)\x00', lambda m: held[int(m.group(1))], s)


def cmd(*argv, cwd=REPO):
    r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    return r.stdout + r.stderr


def shown(key, text, lang='text'):
    extra[key] = text
    return hold(extra_block(key, text, lang))


def walk_files():
    """Every file under the repo, as repo-relative paths, packs excluded."""
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), REPO)
            if rel not in PACKS:
                out.append(rel)
    return out


FILES = walk_files()
ignored = set(cmd('git', 'ls-files', '--others', '--ignored', '--exclude-standard').split('\n'))

# ── snapshot ──
status_sb = git(REPO, 'status', '-sb').split('\n')[0]
porcelain = git(REPO, 'status', '--porcelain').strip()
if porcelain:
    changes = '; '.join(f'`{l}`' for l in porcelain.split('\n'))
    SNAPSHOT = (f"`{status_sb}`. The working tree differs from HEAD: {changes}. Everything below is the "
                f"working-tree state; section 2 shows exactly what differs.")
else:
    SNAPSHOT = f"`{status_sb}`. The working tree is clean, so everything below is the committed state."

# ── 1. location ──
expected = Path(os.path.expanduser('~/projects/malloc-training')).resolve()
loc = [f"- `{REPO}` — " + ("**primary copy**. All scripts hard-code this path." if REPO == expected else
                           f"**not** the hard-coded `{expected}`. Scripts run here still use that path.")]
old_copy = Path(os.path.expanduser('~/malloc-training'))
loc.append(f"- `{old_copy}` (an older copy an earlier pack described): "
           + ("exists. It is not described here." if old_copy.exists() else "no longer exists."))
LOCATION = '\n'.join(loc)

if shutil.which('tree'):
    tree_out = cmd('tree', '-a', '-I', '.git|node_modules|__pycache__|CONTEXT_PACK.md|PROMPTS_PACK.md')
else:
    tree_out = '\n'.join(['.'] + [f'./{f}' for f in FILES]) + '\n'
TREE = shown('tree', tree_out)
SIZES = shown('sizes', ''.join(f"{(REPO / f).stat().st_size:>10}  ./{f}\n" for f in FILES))

# ── 2. git ──
git_parts = []
for title, argv in [('git status', ['status']), ('git branch -a', ['branch', '-a']),
                    ('git remote -v', ['remote', '-v']), ('git log --oneline -30', ['log', '--oneline', '-30']),
                    ('git status -sb --ignored', ['status', '-sb', '--ignored'])]:
    git_parts.append(f"### {title}\n{shown(title, git(REPO, *argv))}")
GIT = '\n'.join(git_parts)

# ── 3. core files ──
CORE_ORDER = ['EXTRACTION_PROMPT.txt', 'handout_urls.txt', 'CURRICULUM.md', 'README.md', 'PROMPT.md',
              'SESSION.md', 'MIND_MODEL.md', 'LAB_HISTORY.md', 'CURRICULUM_REASONING.md',
              'MULTI_TOOL_PROTOCOL.md', 'schema.sql', 'tests/fixtures/schema_v0.sql', '.gitignore']
core_found = [f for f in FILES if Path(f).suffix in ('.md', '.txt', '.sql') or f == '.gitignore']
# The pack templates in tools/ are this pack's own source, not repo content
core_found = [f for f in core_found if not f.startswith(('handouts/', 'tools/'))]
core = [f for f in CORE_ORDER if f in core_found] + sorted(set(core_found) - set(CORE_ORDER))
lang_of = lambda f: {'.sql': 'sql', '.py': 'python', '.sh': 'bash'}.get(Path(f).suffix, 'text')
core_parts = [hold(file_block(REPO, f, level=3, lang=lang_of(f), heading=f'`{f}`')) for f in core]
missing_core = [f for f in CORE_ORDER if f not in core_found]
tail = ["", "No other `.md`, `.txt` or `.sql` files exist in the repo (both packs, `.pytest_cache/` and the pack "
        "templates in `tools/` excluded)."]
if missing_core:
    tail.append("Expected but NOT FOUND: " + ', '.join(f'`{f}`' for f in missing_core) + '.')
tail.append("`verification.txt` (written by start_session.py): " +
            ("shown above." if 'verification.txt' in core else "NOT FOUND."))
CORE = '\n\n'.join(core_parts) + '\n' + '\n'.join(tail)

# ── 4. scripts ──
scripts = [f for f in FILES if Path(f).suffix in ('.py', '.sh') and not f.startswith(('handouts/', 'tools/'))]
# tools/ is this pack's own source: listed by name, not copied. A verbatim
# copy of the builder gets its own @@ markers filled in.
tools_files = sorted(f for f in FILES if f.startswith('tools/'))
root_scripts = sorted(f for f in scripts if '/' not in f)
other_scripts = sorted(f for f in scripts if '/' in f)
# Notes are @@SCRIPT:<path>@@ entries, each running up to the next @@ marker
notes = dict(re.findall(r'@@SCRIPT:([^@]+)@@\n(.*?)(?=\n\n@@)', tmpl, re.S))
EXCLUDED = {'write_curriculum.py'}
no_note = [f for f in scripts + tools_files if f not in notes and f not in EXCLUDED]
if no_note:
    sys.exit("No note in tools/context_pack_template.md for: " + ', '.join(no_note)
             + "\nAdd an @@SCRIPT:<path>@@ entry (Reads/Writes/Run) for each, then rebuild.")
for gone in sorted(set(notes) - set(scripts) - set(tools_files)):
    print(f"note: template has a note for {gone}, which does not exist; skipped.")
has_make = any(Path(f).name in ('Makefile', 'makefile') for f in FILES)
SCRIPTS_INTRO = (("A Makefile exists (see section 3)." if has_make else "No Makefile exists.")
                 + " Every `.py` / `.sh` file outside `tools/` follows (root first, then subdirectories)"
                 + (", plus the untracked git hook `.git/hooks/pre-commit`." if (REPO / '.git/hooks/pre-commit').exists() else ".")
                 + " Unless noted otherwise, all paths are hard-coded to `~/projects/malloc-training/`, and multi-line"
                 " inputs end with a line containing only `END`.")
SCRIPT_BLOCKS = '\n\n'.join(
    f"{hold(file_block(REPO, f, level=3, lang=lang_of(f), heading=f'`{f}`'))}\n{notes[f]}"
    for f in root_scripts + other_scripts if f not in EXCLUDED)
SCRIPT_BLOCKS += ("\n\n### `tools/` — listed, not reproduced\n\nThe pack builders and their templates. "
                  "They are this pack's own source, so they are not copied verbatim.\n\n"
                  + '\n'.join(f"- `{f}` ({(REPO / f).stat().st_size:,} bytes): {notes[f]}" for f in tools_files))
# The notes region becomes the scripts in file order
start, end = tmpl.index('@@SCRIPT:'), tmpl.index('@@WRITE_CURRICULUM@@')
tmpl = tmpl[:start] + '@@SCRIPT_BLOCKS@@\n\n' + tmpl[end:]

wc = REPO / 'write_curriculum.py'
if wc.exists():
    src = wc.read_text()
    strings = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    strings[t.id] = node.value.value
    cur = (REPO / 'CURRICULUM.md').read_text()
    rea = (REPO / 'CURRICULUM_REASONING.md').read_text()
    blocks = lambda s: [int(x) for x in re.findall(r'^NEXT PROJECT: (\d+)', s, re.M)]
    guard = 'sys.exit(1)' in src.split('base =')[0]
    parts = [f"### `write_curriculum.py` — NOT REPRODUCED ({len(src.encode())} bytes)",
             "Left out by instruction."
             + (" **Disabled:** the first lines print why and call `sys.exit(1)` before anything else runs." if guard else "")]
    if 'curriculum' in strings:
        same = strings['curriculum'] == cur
        parts.append(f"Its `curriculum` string {'duplicates' if same else 'differs from'} CURRICULUM.md"
                     f"{' byte for byte' if same else ''} (CURRICULUM.md is verbatim in section 3).")
    if 'reasoning' in strings:
        b_old, b_new = blocks(strings['reasoning']), blocks(rea)
        span = lambda b: f"{min(b)}–{max(b)}" if b else "none"
        parts.append(f"Its `reasoning` string has {len(b_old)} `NEXT PROJECT:` blocks ({span(b_old)}); "
                     f"the current CURRICULUM_REASONING.md has {len(b_new)} ({span(b_new)}).")
    WRITE_CURRICULUM = parts[0] + '\n' + ' '.join(parts[1:])
else:
    WRITE_CURRICULUM = ''

hook = REPO / '.git/hooks/pre-commit'
if hook.exists():
    HOOK = hold(file_block(REPO, '.git/hooks/pre-commit', level=3, lang='bash',
                           heading='`.git/hooks/pre-commit` (untracked)'))
else:
    HOOK = '### `.git/hooks/pre-commit` — NOT FOUND'
    tmpl = re.sub(r'@@HOOK@@\n.*?(?=\n\n## )', '@@HOOK@@', tmpl, flags=re.S)

py = '/usr/bin/python3' if os.path.exists('/usr/bin/python3') else sys.executable
has_pytest = subprocess.run([py, '-c', 'import pytest'], capture_output=True).returncode == 0
PYTEST = (f"`{py} -c 'import pytest'` {'succeeds' if has_pytest else 'fails (no module named pytest)'} on this "
          f"machine; the tests were not run for this pack.")

# ── db helpers ──
DB = REPO / 'brain.db'


def db_rows(path):
    conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid")]
        return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}, conn
    except sqlite3.Error:
        conn.close()
        raise


def old_db(commit):
    """brain.db as of a commit, in a temp file (read-only use)."""
    data = subprocess.run(['git', 'show', f'{commit}:brain.db'], cwd=REPO, capture_output=True).stdout
    if not data:
        return None
    fd, p = tempfile.mkstemp(suffix='.db')
    os.write(fd, data)
    os.close(fd)
    return p


counts, conn = db_rows(DB)
conn.close()

# ── 5. handouts ──
pdfs = [f for f in FILES if f.lower().endswith('.pdf')]
h = []
if pdfs:
    for f in pdfs:
        pages = ''
        if shutil.which('pdfinfo'):
            m = re.search(r'^Pages:\s+(\d+)', cmd('pdfinfo', str(REPO / f)), re.M)
            pages = f", {m.group(1)} pages (pdfinfo)" if m else ''
        h.append(f"- Handout PDF in the folder: `{f}` ({(REPO / f).stat().st_size:,} bytes{pages}; "
                 f"{'git-ignored' if f in ignored else 'not ignored'}). Not read as text (section 9).")
else:
    h.append("- Handout PDFs in the folder: **NONE FOUND**.")
extr = [f for f in FILES if re.search(r'extract|lab_research_', f, re.I) and f != 'EXTRACTION_PROMPT.txt']
h.append("- Extraction output files: " + (', '.join(f'`{f}`' for f in extr) if extr else '**NONE FOUND**') + '.')
h.append(f"- brain.db `lab_handouts` table: **{counts.get('lab_handouts', 'table missing')} rows**.")
p = old_db('5216b3f')
if p:
    c0, conn0 = db_rows(p)
    conn0.close()
    h.append(f"- The pre-reset brain.db (`git show 5216b3f:brain.db`) has {c0.get('lab_handouts', 0)} lab_handouts rows.")
if not extr and not counts.get('lab_handouts'):
    h.append("- Therefore no stored extraction exists that could contain page or section quotes. EXTRACTION_PROMPT.txt "
             "(section 3) does not ask for page or section quotes.")
HANDOUTS = '\n'.join(h)

# ── 6. code ──
code_files = [f for f in FILES if Path(f).suffix in ('.c', '.h')]
phase_dirs = sorted(d.name for d in REPO.glob('phase*') if d.is_dir())
empty = [d for d in phase_dirs if not any((REPO / d).iterdir())]
cl = ["- `.c` / `.h` files in the working tree: " + (', '.join(f'`{f}`' for f in code_files) if code_files else "**NONE FOUND**") + "."
      + (f" Directories {', '.join(f'`{d}/`' for d in phase_dirs)} exist; empty: "
         f"{', '.join(f'`{d}/`' for d in empty) or 'none'}." if phase_dirs else '')]
if code_files and shutil.which('gcc'):
    for f in code_files:
        r = subprocess.run(['gcc', '-Wall', '-fsyntax-only', str(REPO / f)], capture_output=True, text=True)
        cl.append(f"  - `gcc -Wall -fsyntax-only {f}` → exit {r.returncode}" + (f": {r.stderr.strip()}" if r.stderr else ", no warnings"))
else:
    cl.append("- `gcc -Wall`: nothing to compile in the working tree.")
old_c = subprocess.run(['git', 'show', 'ccf882c^:project1.c'], cwd=REPO, capture_output=True, text=True)
if old_c.returncode == 0:
    g = subprocess.run(['gcc', '-Wall', '-fsyntax-only', '-x', 'c', '-'], input=old_c.stdout,
                       capture_output=True, text=True) if shutil.which('gcc') else None
    res = ('gcc not installed' if g is None else
           '**compiles with no warnings**' if g.returncode == 0 and not g.stderr else f'gcc says: {g.stderr.strip()}')
    cl.append(f"- Git history only: `project1.c` ({old_c.stdout.count(chr(10))} lines) and a compiled ELF binary "
              f"`project1` were removed in commit `ccf882c`. `git show ccf882c^:project1.c | gcc -Wall -fsyntax-only "
              f"-x c -` → {res} (syntax-only, no file written). Matching it to curriculum Project 1 is an inference "
              f"(section 8).")
if p:
    conn0 = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
    row = conn0.execute("SELECT status, length(final_code), length(handoff) FROM projects WHERE number = 1").fetchone()
    conn0.close()
    if row:
        cl.append(f"- Pre-reset brain.db (`git show 5216b3f:brain.db`): Project 1 has status '{row[0]}', "
                  f"`final_code` length {row[1] or 0}, and a {row[2] or 0}-character handoff.")
    os.unlink(p)
CODE = '\n'.join(cl)

# ── 7. curriculum ──
cur = (REPO / 'CURRICULUM.md').read_text()
projs = re.findall(r'^PROJECT (\d+)\s*$', cur, re.M)
fields = lambda k: re.findall(rf'^\s+{k}\s*:\s*(.+)$', cur, re.M)
from collections import Counter
labs_c, courses_c = Counter(fields('Lab')), Counter(fields('Course'))
phases = re.findall(r'^# PHASE (\d+)\n# Goal: (.+)$', cur, re.M)
rea = (REPO / 'CURRICULUM_REASONING.md').read_text()
nb = [int(x) for x in re.findall(r'^NEXT PROJECT: (\d+)', rea, re.M)]
sess = {k: (re.search(rf'^{k}:\s*(.*)$', (REPO / 'SESSION.md').read_text(), re.M) or [None, '?'])[1]
        for k in ('CURRENT PROJECT', 'ACTIVE LAB')}
last_out = (REPO / 'SESSION.md').read_text().split('LAST OUTPUT:', 1)[-1].strip().split('\n')[0]
nums = [int(x) for x in projs]
cs = [f"- Total projects in CURRICULUM.md: **{len(projs)}**" + (f" (PROJECT {min(nums)}–{max(nums)})." if nums else "."),
      "- Course: " + '; '.join(f"{k} ({v})" for k, v in courses_c.items()) + ". Lab: "
      + '; '.join(f"{k} ({v})" for k, v in labs_c.items()) + ".",
      "- Phases: " + '; '.join(f'Phase {n} (goal: "{g}")' for n, g in phases) + ".",
      f"- `Source` field: {len(fields('Source'))} projects have one (`grep -c Source CURRICULUM.md` → {cur.count('Source')}).",
      f"- CURRICULUM_REASONING.md has {len(nb)} `NEXT PROJECT:` blocks" + (f" ({min(nb)}–{max(nb)})." if nb else "."),
      f"- Progress in brain.db: {counts.get('projects', 0)} projects. SESSION.md says `CURRENT PROJECT: "
      f"{sess['CURRENT PROJECT']}`, `ACTIVE LAB: {sess['ACTIVE LAB']}`, and LAST OUTPUT `{last_out}`."]
CURRICULUM = '\n'.join(cs)

# ── 9. unreadable ──
schema_db = cmd('sqlite3', str(DB), '.schema') if shutil.which('sqlite3') else None
u = []
if schema_db is not None:
    no_comments = ''.join(l for l in (REPO / 'schema.sql').read_text().splitlines(True) if not l.startswith('--'))
    same = schema_db.strip() == no_comments.strip()
    u.append(f"- `brain.db` ({DB.stat().st_size:,} bytes, `PRAGMA user_version` = "
             f"{sqlite3.connect(f'file:{DB}?mode=ro', uri=True).execute('PRAGMA user_version').fetchone()[0]}): "
             f"SQLite binary, not included verbatim. It was read with `sqlite3` in read-only mode. Its schema "
             + ("is identical to schema.sql minus schema.sql's `--` comment lines (compared by the builder), so it is "
                "not repeated." if same else "**differs** from schema.sql; see below.") + " Row counts follow.")
    if not same:
        u.append(shown('brain.db .schema', schema_db, 'sql'))
for f in pdfs:
    u.append(f"- `{f}`: binary PDF, not read as text.")
u.append("- `project1` ELF binary: exists only in git history (`ccf882c^`). Not readable as text.")
if wc.exists():
    u.append("- `write_curriculum.py`: readable, but not reproduced by instruction (see section 4).")
u.append("- No permission errors. No oversized text files.")
u.append("")
u.append("### brain.db row counts (current)")
u.append(shown('row counts', ''.join(f"{t}: {n}\n" for t, n in counts.items())))
UNREADABLE = '\n'.join(u)

# ── assemble ──
text = tmpl
for key, val in [('DATE', date.today().isoformat()), ('HEAD', HEAD[:7]), ('SNAPSHOT', SNAPSHOT),
                 ('LOCATION', LOCATION), ('TREE', TREE), ('SIZES', SIZES), ('GIT', GIT), ('CORE', CORE),
                 ('SCRIPTS_INTRO', SCRIPTS_INTRO), ('SCRIPT_BLOCKS', SCRIPT_BLOCKS), ('WRITE_CURRICULUM', WRITE_CURRICULUM), ('HOOK', HOOK),
                 ('PYTEST', PYTEST), ('HANDOUTS', HANDOUTS), ('CODE', CODE), ('CURRICULUM', CURRICULUM)]:
    text = text.replace(f'@@{key}@@', val)
assert '@@' not in text.replace('@@UNREADABLE@@', ''), re.findall(r'@@[^@\n]*@@', text)[:5]

text, UNREADABLE = unhold(text), unhold(UNREADABLE)
res = verify_blocks(REPO, text + UNREADABLE, extra)
assert all(ok for _, ok in res), [n for n, ok in res if not ok]
UNREADABLE += (f"\n\n**Verbatim check:** after the pack was written, every verbatim block ({len(res)}: files plus "
               f"command output) was parsed back out and compared byte for byte with its source. All matched.")
final = text.replace('@@UNREADABLE@@', UNREADABLE).rstrip('\n') + '\n'
OUT_PATH.write_text(final)
res2 = verify_blocks(REPO, OUT_PATH.read_text(), extra)
assert all(ok for _, ok in res2) and len(res2) == len(res), [n for n, ok in res2 if not ok]
print(f"Wrote {OUT_PATH} — {len(res)} verbatim blocks verified, {len(final.encode()):,} bytes.")
