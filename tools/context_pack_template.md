<!-- WRITTEN-FOR 0b65c05 -->
# CONTEXT PACK — malloc-training
Generated @@DATE@@ by `tools/build_context_pack.py`, as a read-only snapshot at commit `@@HEAD@@` for a new session. Sections 1–7 and 9 report file contents and command output only. Interpretation appears only in section 8 (INFERENCES). Verbatim blocks use four-backtick fences. After the pack was written, each one was parsed back out and compared byte for byte with its source (section 9).
**Snapshot state:** @@SNAPSHOT@@

## 1. LOCATION & TREE
@@LOCATION@@

### Tree — `tree -a -I '.git|node_modules|__pycache__|CONTEXT_PACK.md|PROMPTS_PACK.md'`
@@TREE@@
`CONTEXT_PACK.md` (this file) and `PROMPTS_PACK.md` are generated, listed in .gitignore, and excluded from the tree and the size list.

### File sizes in bytes (excluding .git and __pycache__)
@@SIZES@@

## 2. GIT STATE
@@GIT@@

## 3. CORE FILES — VERBATIM
@@CORE@@

## 4. SCRIPTS — VERBATIM
@@SCRIPTS_INTRO@@

@@SCRIPT:adversary.py@@
Reads: brain.db — the latest transfer_exams row (by completed_at) and the owned concepts in that lab.
Writes: in one transaction, transfer_exams.adversarial_gap_report and a new adversarial_exams row (gap_found='yes', resolved='pending').
Run: `python3 adversary.py`. It exits 1 first if adversarial_exams is missing. If the latest exam already has a report, it asks "Replace it?". It prints a prompt to paste into a new Claude conversation, waits for ENTER, then reads the gap report from stdin.

@@SCRIPT:context.py@@
Reads: brain.db, SESSION.md, CURRICULUM.md, CURRICULUM_REASONING.md.
Writes: nothing, except `--clear-gap-gate`, which asks a yes/no question and inserts a row into gap_gate_clears (exits 1 with "run init_db.py" if that table is missing).
Run: `python3 context.py [--mini | --clear-gap-gate]`. Prints session context, the gates from gates.py (adversarial report missing: exits 1; 7-day gap gate) and verification questions Q1–Q4. Times are Cairo time when pytz is installed, otherwise local time.

@@SCRIPT:curriculum_status.py@@
Reads: brain.db projects, CURRICULUM.md, CURRICULUM_REASONING.md.
Writes: nothing.
Run: `python3 curriculum_status.py`. Prints done/pending projects and the next project's reasoning.

@@SCRIPT:db.py@@
Reads: SESSION.md (`session_field`), brain.db labs (`find_lab`, `ask_lab`).
Writes: nothing.
Run: not run directly; a shared module. Defines `PROJ`, `DB_PATH`, `connect()` (turns foreign keys on), lab-name matching that ignores case and spacing, `ask_lab` (re-asks until the lab is in the labs table; Enter picks the active lab), and `clean_report` ('', whitespace or 'none' mean no report).

@@SCRIPT:db_check.py@@
Reads: brain.db, SESSION.md, gates.py.
Writes: nothing. Exits 1 on errors, or when brain.db's schema version is below 1 (it tells you to run init_db.py).
Run: `python3 db_check.py`. Also invoked by start_session.py, verify_system.py and the pre-commit hook.

@@SCRIPT:estimate_tokens.sh@@
Reads: sizes of PROMPT.md, SESSION.md, MIND_MODEL.md, CURRICULUM*.md.
Writes: nothing.
Run: `bash estimate_tokens.sh`. Estimates tokens as bytes/4.

@@SCRIPT:gates.py@@
Reads: brain.db (read-only queries).
Writes: nothing.
Run: not run directly; a shared module used by context.py, start_session.py and db_check.py. Holds the adversarial-report gate, the gap gate (GAP_DAYS = 7; a cleared spaced-repetition quiz counts as activity), validation debt (2 per 10 projects), next-project hiding, and missing lab transitions.

@@SCRIPT:get_handout.py@@
Reads: brain.db lab_handouts (newest row for the lab).
Writes: nothing.
Run: `python3 get_handout.py <lab name>`, or with no argument, which asks for the lab.

@@SCRIPT:init_db.py@@
Reads: schema.sql, SESSION.md (ACTIVE LAB / ACTIVE COURSE), brain.db.
Writes: brain.db. On a fresh database it creates every table and sets `PRAGMA user_version = 1`. On version 0 it first copies brain.db to `brain.db.bak-<timestamp>`, then migrates (rebuilds each table from schema.sql and copies the rows across) and runs VACUUM; if the migration fails it rolls back and exits 1, leaving brain.db unchanged. On version 1 it creates only missing tables. Every run makes sure the active lab is in the labs table.
Run: `python3 init_db.py`. Safe to run repeatedly.

@@SCRIPT:lab_transition.py@@
Reads: SESSION.md, brain.db (labs, owned concepts, weakness patterns, project count for the lab).
Writes: in one transaction, a labs row for the next lab if it is new, plus the lab_transitions row (it replaces an existing one after asking). Then it appends the summary to LAB_HISTORY.md.
Run: `python3 lab_transition.py`. It exits 1 if lab_transitions is missing or the ACTIVE LAB is not in the labs table. It prints a prompt for Claude and reads Claude's summary from stdin.

@@SCRIPT:maintain.sh@@
Reads: brain.db row counts (15 tables; labs and gap_gate_clears are not listed), pending gaps, git status.
Writes: nothing.
Run: `bash maintain.sh`.

@@SCRIPT:mood_check.py@@
Reads: stdin (sleep, ate, days since rest).
Writes: a mood_logs row.
Run: `python3 mood_check.py`. Exits early on a CRITICAL state, or on DEGRADED if you decline to proceed. Exits 1 before any question if mood_logs is missing. Ends by suggesting `git pull` and `python3 context.py --mini`.

@@SCRIPT:new_project.sh@@
Reads: arguments (the project number must be digits; it is read as base 10, so 08 and 09 work).
Writes: `phase<P>/project<NN>.c` from a C template (refuses to overwrite), then opens it with `code`.
Run: `./new_project.sh <phase> <number>`.

@@SCRIPT:prompts.py@@
Reads: stdin.
Writes: nothing.
Run: not run directly; a shared module. Every interactive prompt goes through it. Ctrl+D or Ctrl+C cancels the whole script with "Cancelled, nothing saved." and exit 1; bad input re-asks; multi-line answers end with a line containing only `END`.

@@SCRIPT:query_project.py@@
Reads: brain.db projects, project_full_detail, project_narrative.
Writes: nothing.
Run: `python3 query_project.py <number>`, or with no argument, which asks.

@@SCRIPT:resolve_gap.py@@
Reads: pending adversarial_exams rows; stdin.
Writes: in one transaction, resolved='yes' and the resolution text, plus an optional weakness_patterns row (its project number must exist).
Run: `python3 resolve_gap.py`. Re-asks until the gap ID is a pending one.

@@SCRIPT:start_session.py@@
Reads: stdin, brain.db, SESSION.md, CURRICULUM_REASONING.md.
Writes: a mood_logs row; `verification.txt` in the project root (overwritten each run; listed in .gitignore).
Run: `python3 start_session.py`. Fixed sequence: mood → db_check.py (subprocess) → validation gate → context → verification answers. Exits 1 before the first question if mood_logs is missing.

@@SCRIPT:store_handout.py@@
Reads: stdin: a lab from the labs table plus 9 multi-line fields, the last being the full raw extraction. It does not read a PDF itself.
Writes: a lab_handouts row.
Run: `python3 store_handout.py`.

@@SCRIPT:switch_account.sh@@
Reads: brain.db, file existence, yes/no prompts.
Writes: git: `git add .`, then a checkpoint commit if anything is staged, then `git push`.
Run: `./switch_account.sh` before switching Claude accounts.

@@SCRIPT:update.py@@
Reads: stdin (interactive), or an auto block via `--auto` (from the arguments, or pasted and ended with END). Only the keys in `AUTO_KEYS` start a field.
Writes: in one transaction, projects, concepts, project_narrative, and optionally weakness_patterns, patterns (count bumped or row inserted) and decisions. On every 5th project it also writes mind_model and then appends to MIND_MODEL.md. A duplicate project number exits 1 before anything is written.
Run: `python3 update.py` or `python3 update.py --auto`.

@@SCRIPT:update_exam.py@@
Reads: stdin.
Writes: a transfer_exams row (menu 1) or an adversarial_exams row (menu 2).
Run: `python3 update_exam.py`.

@@SCRIPT:update_full_detail.py@@
Reads: stdin; checks the project exists. If full detail already exists, it asks before replacing it.
Writes: in one transaction, project_full_detail and quiz_records rows.
Run: `python3 update_full_detail.py`, after update.py.

@@SCRIPT:validate_concept.py@@
Reads: stdin, brain.db concepts (the concept must exist; it re-asks).
Writes: an external_validation row; on 'fail', it also sets the concept's status to 'cracked'.
Run: `python3 validate_concept.py`. Exits 1 before any question if external_validation is missing.

@@SCRIPT:verify_system.py@@
Reads: file/dir existence, brain.db tables, installed tools, git config.
Writes: nothing directly; it runs context.py --mini, db_check.py, maintain.sh and estimate_tokens.sh.
Run: `python3 verify_system.py`.

@@SCRIPT:tests/conftest.py@@
Reads: the repo's `*.py *.sh *.md *.sql *.txt`, copied into a per-test fake HOME.
Writes: only pytest temp directories. Each test gets its own brain.db, built by init_db.py.
Run: by pytest. Scripts run as subprocesses under `/usr/bin/python3` (override with `MALLOC_PYTHON`). @@PYTEST@@

@@SCRIPT:tests/test_audit_bugs.py@@
Reads: through conftest's sandbox.
Writes: only temp directories.
Run: `pytest tests/`. There is one test or group per phase-1 audit bug, marked `step1`–`step5`.

@@SCRIPT:tests/test_migration.py@@
Reads: tests/fixtures/schema_v0.sql (section 3).
Writes: only temp directories.
Run: `pytest tests/test_migration.py` (marked `step3`). Tests init_db.py's migration from schema version 0 to 1.

@@SCRIPT:tools/build_context_pack.py@@
Builds CONTEXT_PACK.md (this file) from context_pack_template.md, the working tree, git and brain.db (read-only).

@@SCRIPT:tools/build_pack.py@@
Builds PROMPTS_PACK.md from prompts_pack_template.md, repo files and run_samples.py output.

@@SCRIPT:tools/context_pack_template.md@@
Template and per-script notes for CONTEXT_PACK.md.

@@SCRIPT:tools/packlib.py@@
Shared by both builders: writes verbatim blocks with source markers and verifies them byte for byte.

@@SCRIPT:tools/prompts_pack_template.md@@
Template for PROMPTS_PACK.md.

@@SCRIPT:tools/run_samples.py@@
Runs repo scripts in a fake HOME and saves each output with its stdin; called by build_pack.py.

@@WRITE_CURRICULUM@@

@@HOOK@@
Reads: brain.db, via db_check.py.
Writes: nothing; blocks the commit if db_check.py exits non-zero.
Run: automatically by `git commit`. Note: it `cd`s to `~/projects/malloc-training` regardless of which repo is committing.

## 5. STORED HANDOUTS / EXTRACTIONS
@@HANDOUTS@@

Handout URLs listed in handout_urls.txt, with the semester as it appears in each URL:

| Course | Item | Semester (from URL) | Type (from URL/label) | Extraction? |
|---|---|---|---|---|
| CMU 15-213 | L0 C Programming Lab | none in URL (`~213/labs/`) | lab handout PDF | No |
| CMU 15-213 | L1 Data Lab | none in URL (`~213/labs/`) | lab handout PDF | No |
| CMU 15-213 | L5 Malloc Lab | m25 | recitation slides (`recitations/Malloclab-Extended.pdf`) | No |
| CMU 15-213 | L7 Proxy Lab | m25 | recitation slides (`recitations/Proxylab-Extended.pdf`) | No |
| CMU 15-213 | Recitations directory | m25 | directory listing | No |
| CMU 15-418 | Assignments 1–2 | s23 | assignment PDFs | No |
| Stanford CS144 | check0–check7 | none in URL | assignment PDFs | No |
| MIT 6.828 | 10 labs (util … mmap) | 2021 | HTML lab pages | No |
| MIT 6.5840 | 5 labs (mr … shard) | none in URL (path `6.824`) | HTML lab pages | No |
| CMU 15-445 | project0–4 | spring2026 | HTML project pages | No |

15-213 labs L2–L4 and L6: NOT FOUND in handout_urls.txt.

## 6. CODE / EXERCISE WORK
@@CODE@@

## 7. CURRICULUM STATUS
@@CURRICULUM@@

## 8. INFERENCES (interpretation, not file content)

**INFERENCE — Workflow, end to end:**
1. Extract a lab handout with EXTRACTION_PROMPT.txt in a Claude chat (or NotebookLM, per MULTI_TOOL_PROTOCOL.md), then paste the result into `store_handout.py` (brain.db `lab_handouts`).
2. Have Claude generate CURRICULUM.md and CURRICULUM_REASONING.md, and save them by hand (`write_curriculum.py`, now disabled, appears to be how the first version was saved).
3. Each session: `start_session.py` (or `mood_check.py` + `context.py --mini`), then paste PROMPT.md, the context output, SESSION.md and the curriculum files into Claude, or just the context and SESSION.md into the claude.ai Project. Claude must answer the verification questions before teaching.
4. Per project: `new_project.sh`, then work under PROMPT.md's rules (predict before running, paste real output). Afterwards `update.py` (`--auto`) and `update_full_detail.py`, then a git commit (the pre-commit hook runs `db_check.py`).
5. Periodically: `validate_concept.py` (external-validation debt gate: 2 per 10 projects) and a mind-model update every 5 projects (triggered by `update.py`). After 7 days away, the gap gate requires a spaced-repetition quiz and `context.py --clear-gap-gate`.
6. End of phase: transfer exam (`update_exam.py`), then `adversary.py`, then `resolve_gap.py`.
7. End of lab: `lab_transition.py` → LAB_HISTORY.md, re-uploaded to the Project.
8. Switching Claude accounts: `switch_account.sh`, which commits and pushes so another account can `git pull`. MULTI_TOOL_PROTOCOL.md divides work across Claude, NotebookLM, Gemini and GPT-4. PROMPTS_PACK.md covers the Claude-facing side in detail.

**INFERENCE — Gaps and inconsistencies:**
- **The curriculum was built without a stored handout.** `lab_handouts` has never had a row. A PDF named like the L0 handout now sits in `handouts/`, but it is git-ignored, unextracted and unstored. So CURRICULUM.md's L0 content (e.g. "seven queue functions", "list_ele_t", "1M elements" in the reasoning) has not been checked against it, and no project has a Source field.
- **Mixed semesters and source types** in handout_urls.txt: L0/L1 point to current, unversioned `~213/labs/` handouts, while L5/L7 point to `m25` *recitation slides*, not lab handouts. The other courses use s23, 2021, spring2026 or unversioned URLs.
- **EXTRACTION_PROMPT.txt pressures invention:** "Miss nothing", every field mandatory, no "NOT IN HANDOUT" option, and no page or section quotes required. Fields such as "line count", "edge cases the autograder hits" and "exact CS:APP chapters by section number" are often absent from a handout.
- **The curriculum reasoning presumes Project 1 performance** ("Project 1 confirmed student thinks in variable names…"), but progress was reset in `3a69061` and brain.db has no projects. Entries for early projects may need regenerating after Project 1 is redone.
- **Schema changes now need a version bump.** schema.sql is the only place tables are defined, and init_db.py tracks `PRAGMA user_version`. Only version 0 → 1 has a migration; at version 1 it only adds missing tables. A future column change needs a version 2 and a new migration, or it will not reach an existing brain.db.
- **Hard-coded path:** every script, and the pre-commit hook, use `~/projects/malloc-training`. A copy elsewhere still reads and writes that path. The tests and pack tools get around this by overriding HOME.
- **Personal rule duplication:** PROMPT.md contains a placeholder `PERSONAL RULE: [STUDENT WRITES ONE SENTENCE HERE]`; the actual rule is in SESSION.md.
- **Phases 3–5** have directories (`phase3/`–`phase5/`) but no curriculum entries.
- The old deleted `project1.c` is matched to curriculum Project 1 by content and name only.

## 9. ANYTHING I COULDN'T READ
@@UNREADABLE@@
