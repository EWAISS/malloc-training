"""
build_pack.py — builds PROMPTS_PACK.md: every Claude-facing prompt,
sample script output and the web-Claude workflow, for a Claude that
cannot open this repo.

Usage (from anywhere):
  python3 -I tools/build_pack.py [--out PATH] [--repo PATH]

It runs tools/run_samples.py in a fresh temp directory (a fake HOME, so
the real brain.db is never touched), expands tools/prompts_pack_template.md,
then parses every verbatim block back out of the finished pack and
compares it byte for byte with its source. Any mismatch, or any change
to the real repo during the runs, stops the build.

The template's prose (citations, decisions, workflow) was written by
hand for the commit in its WRITTEN-FOR line. When HEAD is newer the
verbatim blocks are still exact, but line ranges and prose may point
at the wrong code: the build says so, and they need a review.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# -I leaves the script's own directory off sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packlib import (extra_block, fence, file_block, git, head_commit,
                     lines_block, verify_blocks)

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
OUT_PATH = Path(opt('--out', REPO / 'PROMPTS_PACK.md')).resolve()
tmpl = (HERE / 'prompts_pack_template.md').read_text()

written_for = re.search(r'<!-- WRITTEN-FOR (\w+) -->\n', tmpl)
tmpl = tmpl.replace(written_for.group(0), '')
HEAD = head_commit(REPO)
if not HEAD.startswith(written_for.group(1)):
    print(f"WARNING: the template prose was written for {written_for.group(1)}; HEAD is {HEAD}.\n"
          f"  Verbatim blocks are re-read and exact, but review the line ranges and prose.")

# ── sample runs in a sandbox ──
SANDBOX = Path(tempfile.mkdtemp(prefix='prompts-pack-'))
r = subprocess.run([sys.executable, '-I', str(HERE / 'run_samples.py'), str(SANDBOX), '--repo', str(REPO)],
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit(f"run_samples.py failed:\n{r.stdout}{r.stderr}")
OUTS = SANDBOX / 'outputs'


def repo_state():
    import hashlib
    state = {}
    for name in ('brain.db', 'SESSION.md', 'verification.txt'):
        p = REPO / name
        state[name] = ({'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                        'mtime_ns': p.stat().st_mtime_ns} if p.exists() else None)
    state['git_status'] = git(REPO, 'status', '--porcelain')
    return state


before = json.loads((OUTS / 'state_before.json').read_text())
after = repo_state()
if before != after:
    sys.exit(f"The real repo changed during the sample runs!\nbefore={before}\nafter={after}")


def fmt_mtime(ns):
    return subprocess.run(['date', '-d', f'@{ns / 1e9:.9f}', '+%Y-%m-%d %H:%M:%S.%N %z'],
                          capture_output=True, text=True).stdout.strip()


check = ["| File | mtime before | mtime after | sha256 (first 16) before | after |", "|---|---|---|---|---|"]
for name in ('brain.db', 'SESSION.md', 'verification.txt'):
    b, a = before[name], after[name]
    cell = lambda s, k: ('does not exist' if s is None else
                         (fmt_mtime(s['mtime_ns']) if k == 'm' else s['sha256'][:16]))
    check.append(f"| `{name}` | {cell(b, 'm')} | {cell(a, 'm')} | {cell(b, 's')} | {cell(a, 's')} |")
gs = before['git_status']
check.append("")
check.append(f"`git status --porcelain` before the runs: {('`' + gs.strip() + '`') if gs.strip() else 'empty'}. "
             f"After the runs (checked before the pack was written): identical. The real repo was not touched.")
CHECK = '\n'.join(check)

runs = {r['label']: r for r in json.loads((OUTS / 'runs.json').read_text())}
order = [
    'start_session.py',
    '@verification.txt',
    'context.py (full)',
    'context.py --mini',
    'update.py --auto (project 1)',
    'update.py --auto (project 5, 5th project — mind model prompt)',
    'context.py while a transfer exam has no adversarial report (gate)',
    'adversary.py',
    'lab_transition.py (cancelled with EOF at the paste step — nothing saved)',
    'context.py --mini with the gap gate active (projects aged 10 days)',
    'curriculum_status.py',
    'mood_check.py',
    'estimate_tokens.sh',
    'switch_account.sh (stopped at "Ready to push?" — answered no)',
]
assert set(order) - {'@verification.txt'} == set(runs), set(runs) ^ set(order)
home = str(SANDBOX / 'home')
parts = []
for i, label in enumerate(order, 1):
    if label == '@verification.txt':
        v = (OUTS / 'verification.txt').read_text()
        assert v in runs['start_session.py']['out']
        parts.append(f"#### 2.3.{i} `verification.txt` as written by the start_session.py run above\n\n"
                     f"Shortened for size: the file is byte-identical to the STEP 5 block in 2.3.1, from "
                     f"`CONTEXT VERIFICATION — CORRECT ANSWERS` through the closing `====` line "
                     f"({len(v.encode())} bytes), so it is not repeated.")
        continue
    r = runs[label]
    cmd = r['cmd'].replace(home + '/projects/malloc-training/', '')
    out = r['out']
    note = ''
    if label == 'estimate_tokens.sh':
        out = out.replace(home, '~')
        note = '\n\nPath shortened per D7.'
    if label == 'curriculum_status.py':
        ol = out.split('\n')
        keep_from = next(k for k, l in enumerate(ol) if l.startswith('NEXT UP:')) - 2
        omitted = keep_from - 22
        out = '\n'.join(ol[:22] + [f'    [… {omitted} lines omitted for size: Projects 6–30 of the pending list, '
                                    f'two lines each, same layout …]'] + ol[keep_from:])
        note = ('\n\nShortened for size. The omitted lines list Projects 6–30 from CURRICULUM.md '
                '(full text in 1A).')
    stdin = r['stdin']
    sin = fence(stdin) if stdin else '(none — stdin empty)'
    parts.append(f"#### 2.3.{i} {label}\n\nCommand: `{cmd}` · exit code {r['rc']}\n\n"
                 f"Canned stdin:\n\n{sin}\n\nOutput:{note}\n\n{fence(out)}")
RUNS = '\n\n'.join(parts)


def grep_output():
    files = sorted(p.name for p in REPO.glob('*.py')) + sorted(p.name for p in REPO.glob('*.sh'))
    return subprocess.run(['grep', '-nI', '-i', '-E', 'claude|paste|copy|session|account|token', *files],
                          cwd=REPO, capture_output=True, text=True).stdout


def grep_block():
    out = grep_output()
    return f"{out.count(chr(10))} matching lines.\n\n{extra_block('grep output', out)}"


def context_pack_note():
    p = REPO / 'CONTEXT_PACK.md'
    if not p.exists():
        return "`CONTEXT_PACK.md` does not exist yet: build it with `python3 -I tools/build_context_pack.py`."
    m = re.search(r'at commit `(\w+)`', p.read_text()[:2000])
    if not m:
        return "`CONTEXT_PACK.md` exists, but its header names no commit, so it may be stale; rebuild it."
    if HEAD.startswith(m.group(1)):
        return (f"`CONTEXT_PACK.md` was built from the same commit (`{m.group(1)}`), so its script source "
                f"matches the line numbers here.")
    return (f"`CONTEXT_PACK.md` was built from commit `{m.group(1)}`, but this pack is at `{HEAD[:7]}`, so its "
            f"script source may differ. Rebuild it with `python3 -I tools/build_context_pack.py`.")


text = tmpl
text = text.replace('@@HEAD@@', HEAD[:7]).replace('@@DATE@@', date.today().isoformat())
text = text.replace('@@HEADTIME@@', git(REPO, 'log', '-1', '--format=%ci', 'HEAD').strip())
text = text.replace('@@CTXPACK@@', context_pack_note())
text = re.sub(r'@@FILE:([^@]+)@@', lambda m: file_block(REPO, m.group(1), level=4), text)
text = re.sub(r'@@LINES:([^:]+):(\d+):(\d+)@@',
              lambda m: lines_block(REPO, m.group(1), int(m.group(2)), int(m.group(3))), text)
text = text.replace('@@GREP@@', grep_block()).replace('@@CHECK@@', CHECK).replace('@@RUNS@@', RUNS)
assert '@@' not in text.replace('@@VERIFY@@', ''), re.findall(r'@@[^@]*@@', text)

extra = {'grep output': grep_output()}
res = verify_blocks(REPO, text, extra)
assert all(ok for _, ok in res), [n for n, ok in res if not ok]


def span(a, b):
    return len(text[text.index(a):text.index(b)].encode())


S1 = span('## 1. EVERY PROMPT', '## 2. WHAT EACH')
S2 = span('## 2. WHAT EACH', '## 3. THE WORKFLOW')
S3 = span('## 3. THE WORKFLOW', '## 4. CLAUDE.AI')
S1C = span('### 1C. Raw grep', '## 2. WHAT EACH')
size = 0
for _ in range(5):
    under = size <= 150 * 1024
    v = [f"**Verbatim check:** after the pack was written, every block marked as verbatim was parsed back "
         f"out of the pack and compared byte-for-byte with its source file at `{HEAD[:7]}`. "
         f"{len(res)} blocks were checked; {sum(ok for _, ok in res)} matched, and none differed.", "",
         "Blocks checked: " + ', '.join(f'`{n}`' for n, _ in res) + '.', "",
         "Sample outputs (2.3) are program output, not file content. The checks above don't cover them; they "
         "are pasted unchanged from the sandbox runs, except for the one path edit in D7.", "",
         f"**Size:** {size:,} bytes ({size / 1024:.1f} KB). That is "
         f"{'under' if under else 'over'} the ~150 KB target. As instructed, sections 1 and 3 are "
         f"complete: section 1 is {S1 / 1024:.1f} KB and section 3 is {S3 / 1024:.1f} KB. Without section 2 the "
         f"pack would still be {(size - S2) / 1024:.1f} KB. Section 2 was shortened ({S2 / 1024:.1f} KB): 2.3.2 "
         f"points to 2.3.1 rather than repeating it, and 2.3.11 leaves out 25 pending projects."
         + ('' if under else f" To get under 150 KB, the easiest cut is 1C, the raw grep ({S1C / 1024:.1f} KB). "
                             f"Every Claude-facing hit in it is already quoted in 1B.")]
    final = text.replace('@@VERIFY@@', '\n'.join(v)) + '\n'
    new = len(final.encode())
    if new == size:
        break
    size = new
OUT_PATH.write_text(final)
res2 = verify_blocks(REPO, OUT_PATH.read_text(), extra)
assert all(ok for _, ok in res2) and len(res2) == len(res)
shutil.rmtree(SANDBOX)
print(f"Wrote {OUT_PATH} — {len(res)} verbatim blocks verified, {size:,} bytes.")
