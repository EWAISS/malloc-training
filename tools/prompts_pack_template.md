# PROMPTS PACK — malloc-training

<!-- WRITTEN-FOR 0b65c05 -->
Generated @@DATE@@ by `tools/build_pack.py`, read-only, at commit `@@HEAD@@` (@@HEADTIME@@).

**Who this is for:** a Claude in a claude.ai chat that cannot open the repo and is helping plan the move from web Claude (copy/paste, account switching) to Claude Code in the terminal. The pack covers only what is Claude-facing, plus the workflow. Full script source is in `CONTEXT_PACK.md` (see D4).

**How to read it:** Every statement cites `file:line`. Anything marked **INFERENCE** is interpretation and is not stated in the files. Verbatim blocks are fenced with four backticks and were filled in by a script from the files at this commit. They were then checked against their sources (see section 6). Rebuild both packs with `python3 -I tools/build_pack.py` and `python3 -I tools/build_context_pack.py`.

## Decisions made for this pack (defaults I took without asking)

- **D1 — What "Claude-facing file" means.** A file that a repo file says to upload to the Claude Project or paste into Claude: `MULTI_TOOL_PROTOCOL.md:21-28`, `start_session.py:427-432`, `switch_account.sh:132-133`, `PROMPT.md:440-449`. Also included: `EXTRACTION_PROMPT.txt`, which is an instruction addressed to a model; `MULTI_TOOL_PROTOCOL.md`, which tells the user what to paste where; and `estimate_tokens.sh`, which budgets the pasted files. All of these appear in full in 1A. `README.md` holds only the line `# malloc-training` with no trailing newline, so it is not repeated.
- **D2 — Left out of section 1.** `handout_urls.txt` (PDF download URLs, not addressed to Claude), `schema.sql`, `tests/`, `maintain.sh` (a health check with no Claude-facing text), `CONTEXT_PACK.md`, and `write_curriculum.py`. `write_curriculum.py` is disabled (`write_curriculum.py:1-11`) and its body is an older copy of the curriculum text. No `CLAUDE.md` exists in the repo.
- **D3 — How script strings were collected.** I grepped every `*.py` and `*.sh` in the repo root (`tests/` and `tools/` excluded) for `claude|paste|copy|session|account|token`, case-insensitive. Every hit that is addressed to Claude, or tells the user what to paste or say to Claude, appears in 1B inside its whole surrounding print block, with its line range. Each excerpt starts at a line boundary. The raw grep output is in 1C, so nothing is silently dropped. Hits that are not Claude-facing (variable names, `Session 1` in a comment) appear only in 1C.
- **D4 — Script source.** Not repeated here. `CONTEXT_PACK.md` holds every script verbatim. @@CTXPACK@@ The reader can only see `CONTEXT_PACK.md` if the user pastes it as well.
- **D5 — Where the fake data came from.** I made it up; none of it is the user's real progress. Five projects went in through the real write path, `update.py --auto`, with a pasted auto block. Project 2 carries a weakness pattern (`sub_projects_generated: yes`), project 3 a coding pattern, and project 5 triggers the mind-model prompt. A transfer exam without an adversarial report went in by direct SQL, the way `tests/conftest.py` `add_transfer_exam` does it. Separately, every project was aged 10 days by SQL to trigger the gap gate.
- **D6 — Interactive scripts.** They got canned stdin, shown next to each output. Because stdin is piped, the typed answers are not echoed, so the prompts run together on one line. `lab_transition.py` was stopped with EOF at its paste step, so it saved nothing. `switch_account.sh` got "no" at `Ready to push?`, so it never reached `git add`, commit or push.
- **D7 — One edit to output.** In the `estimate_tokens.sh` sample, the absolute sandbox path to the copied repo was replaced with `~/projects/malloc-training`, which is what the script prints on the real machine. Nothing else in any output was changed.
- **D8 — Where sources disagree.** Each source is quoted as written and not reconciled. The disagreements are listed in 3.8.
- **D9 — Claude Project.** The claude.ai Project assumptions have their own section, 4, as requested. Section 5 (INFERENCE) lists the other web-Claude assumptions.

## Contents

1. Every prompt for Claude — verbatim
2. What each script outputs for Claude (sandbox samples)
3. The workflow, end to end (including account switch)
4. claude.ai Project assumptions
5. Web-Claude assumptions (INFERENCE)
6. Verification and size

---

## 1. EVERY PROMPT FOR CLAUDE — VERBATIM

### 1A. Files meant to be pasted to, uploaded to, or read by Claude — full contents

@@FILE:PROMPT.md@@

@@FILE:SESSION.md@@

@@FILE:MIND_MODEL.md@@

@@FILE:LAB_HISTORY.md@@

@@FILE:CURRICULUM.md@@

@@FILE:CURRICULUM_REASONING.md@@

@@FILE:EXTRACTION_PROMPT.txt@@

@@FILE:MULTI_TOOL_PROTOCOL.md@@

@@FILE:estimate_tokens.sh@@

`switch_account.sh` appears in full in section 3.7.

### 1B. Strings in scripts addressed to Claude, or telling the user what to paste or say

Each block is the exact source text of the named line range. Line numbers are at commit `@@HEAD@@`.

#### context.py — the verification block printed at the end of every context, full and mini

@@LINES:context.py:78:119@@

#### context.py — the gap-gate clear (`--clear-gap-gate`) and the missing-reasoning hint

@@LINES:context.py:53:58@@

@@LINES:context.py:640:645@@

#### gates.py — the adversarial-exam block and the gap gate (printed by context.py and start_session.py)

@@LINES:gates.py:57:68@@

@@LINES:gates.py:97:116@@

#### start_session.py — the mood step, the validation-debt gate, and the step-5 "Now paste into Claude" block (also written to verification.txt)

@@LINES:start_session.py:83:130@@

@@LINES:start_session.py:182:195@@

@@LINES:start_session.py:375:438@@

#### update.py — the auto-block keys (the format Claude's "auto update block" must use), mind-model prompt, handoff prompt, paste prompts

The auto-block format is defined only by this key list. `PROMPT.md` asks for "update.py prompt answers for all fields" (`PROMPT.md:524`) and `switch_account.sh:92` asks for an "auto update block", but neither spells out the keys.

@@LINES:update.py:12:26@@

@@LINES:update.py:66:91@@

`post_project_handoff_prompt` (below) is defined at `update.py:215`, but nothing in the repo calls it. A grep for `post_project_handoff_prompt` finds only the definition.

@@LINES:update.py:215:229@@

@@LINES:update.py:296:310@@

@@LINES:update.py:356:358@@

@@LINES:update.py:410:415@@

#### adversary.py — the adversarial examiner prompt

@@LINES:adversary.py:66:93@@

#### lab_transition.py — the lab transition prompt and next steps

@@LINES:lab_transition.py:118:156@@

@@LINES:lab_transition.py:210:217@@

#### curriculum_status.py

@@LINES:curriculum_status.py:101:104@@

@@LINES:curriculum_status.py:177:179@@

@@LINES:curriculum_status.py:192:196@@

#### validate_concept.py — the external validation (explicitly without Claude)

@@LINES:validate_concept.py:57:62@@

@@LINES:validate_concept.py:92:97@@

@@LINES:validate_concept.py:123:126@@

#### update_exam.py — the transfer exam (pastes back "Claude evaluation")

@@LINES:update_exam.py:12:20@@

#### update_full_detail.py — the project spec "as given by Claude" and the quiz record paste-back

@@LINES:update_full_detail.py:62:83@@

#### store_handout.py — fields the handout extraction is pasted into

@@LINES:store_handout.py:6:21@@

#### mood_check.py — the standalone pre-session check

@@LINES:mood_check.py:59:91@@

#### verify_system.py — the setup checklist

@@LINES:verify_system.py:35:60@@

@@LINES:verify_system.py:87:104@@

@@LINES:verify_system.py:278:286@@

### 1C. Raw grep output (scripts only, tests excluded)

Command: `grep -nI -i -E "claude|paste|copy|session|account|token" *.py *.sh`

@@GREP@@

---

## 2. WHAT EACH SCRIPT OUTPUTS FOR CLAUDE

### 2.1 Scripts whose output goes to Claude (as the files say)

| Script | What it prints | Where the files say it goes |
|---|---|---|
| `start_session.py` | 5 steps: mood, db check, validation gate, context, verification answers. Writes `verification.txt` | Step-5 text: "Now paste into Claude: 1. PROMPT.md … 2. The context output above (Step 4) 3. SESSION.md …" (`start_session.py:427-432`). `MULTI_TOOL_PROTOCOL.md:66-73` says paste context.py output + SESSION.md into the Project |
| `context.py` | Full context plus a 4-question verification block | `PROMPT.md:440-449`: paste after PROMPT.md; `MULTI_TOOL_PROTOCOL.md:28-30` |
| `context.py --mini` | Short context plus the same verification block | `mood_check.py:88-90` says run it after the mood check; no file says where to paste it |
| `adversary.py` | Adversarial examiner prompt | "Open a NEW Claude conversation" (`adversary.py:69`); `MULTI_TOOL_PROTOCOL.md:117` says GPT-4 instead |
| `lab_transition.py` | Lab transition prompt | "PASTE THIS INTO CLAUDE PROJECT NOW" (`lab_transition.py:126`) |
| `update.py` (5th, 10th, … project) | Mind-model prompt | "Paste this prompt into Claude RIGHT NOW" (`update.py:74`) |
| `curriculum_status.py` | Curriculum progress, a "Tell Claude" line | `curriculum_status.py:194-195` |
| `switch_account.sh` | Gates plus "Ask Claude / Tell Claude" lines | section 3.7 |
| `get_handout.py` | Stored handout fields | No file says where this goes. **INFERENCE:** for pasting to Claude; context.py already includes an "ACTIVE LAB HANDOUT" section |
| `estimate_tokens.sh` | Token estimate of the pasted files | Read by the user |

### 2.2 How the samples were made

- **Sandbox:** this follows the approach in `tests/conftest.py`. `tools/run_samples.py` made a fake `HOME` in a fresh temp directory and copied `*.py *.sh *.md *.sql *.txt` (minus both packs) into `$HOME/projects/malloc-training`. I ran `init_db.py` to build a fresh `brain.db` from `schema.sql`, then ran every script with `HOME=<fake home>`, `GIT_CEILING_DIRECTORIES=<sandbox>` and the system `python3`. All the scripts hardcode `~/projects/malloc-training` (for example `db.py:14`, `context.py:22`, `start_session.py:35`, `switch_account.sh:6`), so `expanduser` resolves to the sandbox.
- **Fake data:** see D5.
- **Untouched-repo check:**

@@CHECK@@

### 2.3 Sample outputs

@@RUNS@@

---

## 3. THE WORKFLOW, END TO END

The repo files describe the session flow in several versions that don't fully agree. Each step below names its source. Disagreements are collected in 3.8. **INFERENCE:** the versions look like layers written at different times. `PROMPT.md` is the original, a pure-paste flow. `start_session.py` and `switch_account.sh` came later. `MULTI_TOOL_PROTOCOL.md` moved the fixed files into a claude.ai Project.

### 3.1 One-time setup

1. `python3 verify_system.py` checks that the files exist (`verify_system.py:35-60`) and that `PROMPT.md` is filled in (`verify_system.py:87-104`). It ends: "1. Write your personal rule in SESSION.md / 2. Run: python3 start_session.py / Then open Claude and begin Project 1." (`verify_system.py:282-285`).
2. Claude Project setup: create the Project on claude.ai and upload `PROMPT.md`, `MIND_MODEL.md`, `CURRICULUM.md`, `CURRICULUM_REASONING.md` and `LAB_HISTORY.md` (`MULTI_TOOL_PROTOCOL.md:18-30`, `269-282`). Details in section 4.
3. Other tools: NotebookLM notebooks for the lab PDFs and books, Gemini, GPT-4 (`MULTI_TOOL_PROTOCOL.md:32-61`).

### 3.2 Opening a session

| Step | Script / action | What the user copies | Where it's pasted | Source |
|---|---|---|---|---|
| 1 | `git pull` | — | — | `PROMPT.md:441`, `mood_check.py:89`, `switch_account.sh:130` |
| 2 | `python3 start_session.py` (step 1 asks sleep, ate, days since rest; DEGRADED asks "Proceed anyway?"; CRITICAL exits) | — | — | `start_session.py:83-130` |
| 3 | start_session step 2, `db_check`; step 3, the validation-debt gate. Debt hides the next project number and points to `validate_concept.py` | — | — | `start_session.py:182-195` |
| 4 | start_session step 4 prints the context (sample 2.3) | The step 4 output | Claude | `start_session.py:429` |
| 5 | start_session step 5 prints the correct verification answers and writes `verification.txt` | Nothing; the user keeps it visible to grade Claude | — | `start_session.py:383-386`, `446-449` |
| 6 | Paste into Claude: `PROMPT.md`, step 4 output, `SESSION.md`, `CURRICULUM.md`, `CURRICULUM_REASONING.md` | those 5 | a chat | `start_session.py:427-432` |
| 6′ | Project variant: paste ONLY context.py output + SESSION.md; PROMPT.md is already loaded | 2 items | the Claude Project | `MULTI_TOOL_PROTOCOL.md:69-73` |
| 6″ | Original variant: `python3 context.py`, then paste PROMPT.md + context.py output + SESSION.md | 3 items | a new session | `PROMPT.md:440-447` |

**What Claude is expected to do at session start:**
- Answer the verification questions before teaching. context.py prints Q1–Q4 (`context.py:98-119`); start_session.py's answer key adds Q5, "Why does Project N come next", which must reference `CURRICULUM_REASONING.md` (`start_session.py:407-423`). The user compares Claude's answers with `verification.txt`. If any answer is wrong or vague: "stop, repaste, reverify" (`start_session.py:434-437`; `context.py:102-105`).
- Write one paragraph covering where the student is, what they own, recent struggles, what the next project must do, and what the handoff requires. The student confirms it (`PROMPT.md:449-456`).
- RULE 25: "check: cat ~/projects/malloc-training/CURRICULUM.md / cat …CURRICULUM_REASONING.md", then run the next unstarted project from CURRICULUM.md (`PROMPT.md:552-564`).
- RULE 26: before running a project, state its number and name, why it comes here, the targeted weakness, the teaching angle, and the analogy. If they can't be answered from the files: "Ask previous Claude to regenerate it." (`PROMPT.md:571-584`).

**Gates that can stop the session before teaching:**
- **Adversarial gate:** a transfer exam with no adversarial report blocks context.py and start_session.py. The fix is `python3 adversary.py` (`gates.py:57-68`; sample 2.3).
- **Gap gate:** more than 7 days since the last activity (`gates.py:28`) locks new material. It prints "Tell Claude: 'Run spaced repetition quiz now.'" After the user passes, `python3 context.py --clear-gap-gate` asks "Did you pass all 5 …? (yes/no)" and records the clear (`gates.py:97-116`; `context.py:53-71`).
- **Validation debt:** 2 external validations are required per 10 projects. The fix is `validate_concept.py`, which uses an external source with "No Claude. No book." (`start_session.py:165-195`; `validate_concept.py:57-62`, `92-97`).

### 3.3 During a project

- Claude produces the project in the fixed "OUTPUT FORMAT — EVERY PROJECT" (`PROMPT.md:483-520`).
- `./new_project.sh <phase> <number>` creates `phase<P>/project<NN>.c` from a template and opens it with `code` (`new_project.sh:1-38`).
- The student contract: predict before running and "PASTE REAL OUTPUT … Never describe output. Always paste it directly." (`PROMPT.md:45-51`). The user hand-copies program output into the chat.
- Lookups go to other tools, and the answers are pasted back to Claude. NotebookLM handles book sections and lab constraints; Gemini handles tangents, "Don't waste Claude session tokens on tangents." (`MULTI_TOOL_PROTOCOL.md:81-108`).
- After every project, Claude generates: "1. SESSION.md replacement content 2. update.py prompt answers for all fields 3. Handoff instruction for next Claude instance 4. One line for DECISIONS.md 5. Code review paragraph" (`PROMPT.md:522-527`). No `DECISIONS.md` exists in the repo.

### 3.4 Closing a project — what is pasted back and which script stores it

| Script | What the user pastes in | Where that text comes from | Where it's stored |
|---|---|---|---|
| `update.py --auto` | "Paste auto update block." with the keys from `update.py:12-26`, ended by `END`; then "Paste final code."; then, if `sub_projects_generated: yes`, 7 weakness fields | Claude, asked "Generate auto update block now." (`switch_account.sh:92`) | `brain.db` (projects, concepts, narrative, weakness, patterns, decisions) — **INFERENCE** from the context.py sections that read them |
| `update.py` (interactive) | about 25 one-line answers, including "Handoff (generate this in Claude NOW while sharp):" (`update.py:340-378`) | the user plus Claude | `brain.db` |
| `update.py` on project 5, 10, … | "Paste Claude's response below." for the mind-model prompt (`update.py:66-91`) | Claude | the `mind_model` table and appended to `MIND_MODEL.md` (`update.py:191-207`) |
| `update_full_detail.py` (run after update.py, per its docstring) | full spec "as given by Claude", micro-projects, all quiz Qs/As, failure/success moments, memory-model evolution, then per-question records | a Claude transcript plus the user | `project_full_detail`, `quiz_records` (`update_full_detail.py:1-8`) |
| `git add . && git commit … && git push` | — | printed by update.py | GitHub (`PROMPT.md:458-462`) |
| `SESSION.md` (edited by hand) | Claude's "SESSION.md replacement content" | Claude (`PROMPT.md:523`) | `SESSION.md` |

### 3.5 Periodic flows

- **Transfer exam (end of phase):** Claude runs it in the main conversation. `update_exam.py` takes the scenario, the user's implementation, "Claude evaluation:", gaps, an "Adversarial gap report:" and the status (`update_exam.py:12-20`).
- **Adversarial exam:** `adversary.py` prints the examiner prompt, waits for ENTER, then takes "the adversary's final gap report (one sentence)" and stores it in `transfer_exams` + `adversarial_exams` (`adversary.py:66-113`). The gap goes back to the main conversation for repair (`MULTI_TOOL_PROTOCOL.md:126-128`; `PROMPT.md:352-354`). Once repaired, `resolve_gap.py` marks it resolved (`resolve_gap.py:1-6`).
- **Mind model every 5 projects:** update.py prints the prompt; Claude answers; the paragraph lands in `MIND_MODEL.md`; the user re-uploads `MIND_MODEL.md` to the Project and commits (`MULTI_TOOL_PROTOCOL.md:180-198`).
- **Lab transition:** `lab_transition.py` reads ACTIVE LAB from SESSION.md, asks for the next lab and prints the prompt "PASTE THIS INTO CLAUDE PROJECT NOW". It then takes "Paste Claude's transition summary:", parses OWNED/CARRIED FORWARD/WATCH FOR/KEY ANALOGY, stores it in `lab_transitions` and appends it to `LAB_HISTORY.md`. Next steps: "1. Re-upload LAB_HISTORY.md to Claude Project 2. Update SESSION.md … 3. Run start_session.py" (`lab_transition.py:118-217`).
- **New lab curriculum:** run Gemini Deep Research and save `lab_research_<lab>.md`. Then `store_handout.py`, filled from a NotebookLM extraction of the PDF. Then paste context.py output + SESSION.md + the research into the Project with "Generate the curriculum for [LAB NAME]…". Save the output to `CURRICULUM.md` and `CURRICULUM_REASONING.md` by hand, re-upload both and commit (`MULTI_TOOL_PROTOCOL.md:140-178`). `EXTRACTION_PROMPT.txt` begins "You are a lab handout extractor. Read this PDF carefully." and its headings match `store_handout.py`'s fields. **INFERENCE:** it's meant to be pasted with the PDF into Claude or NotebookLM, with the output pasted into `store_handout.py`. No file says where it is pasted; it is referenced only in `verify_system.py:55`.
- **Curriculum status:** `curriculum_status.py` ends with "Tell Claude: 'Update CURRICULUM_REASONING.md for the next 5 projects based on current state.'" (`curriculum_status.py:192-196`).

### 3.6 Running out of tokens (as PROMPT.md describes it)

- "WHEN TOKENS RUN LOW: Student types: 'Generate SESSION.md update and handoff instruction now.' Claude generates both in one response. Student updates SESSION.md. Student runs update.py with handoff instruction. Student commits and pushes. Then switches account." (`PROMPT.md:464-471`)
- "ACCOUNT SWITCHING: Accounts are interchangeable. brain.db on GitHub is the single source of truth. … context.py always generates fixed size output … Token budget is always the same." (`PROMPT.md:473-480`)
- RULE 27: when the student mentions switching accounts or running out of tokens, Claude generates 1. CURRICULUM.md entries, 2. CURRICULUM_REASONING.md for the next 5 projects, 3. a partial mind model, 4. a SESSION.md update, 5. an auto update block — "Do not wait to be asked." (`PROMPT.md:586-599`)

### 3.7 Account switch — `switch_account.sh`

**Where it's referenced:** nothing calls or names `switch_account.sh` except the script itself (`switch_account.sh:30,48,116,140`), `verify_system.py:52` (required file, "Run step 12 from setup") and `verify_system.py:225` (a list of scripts), and a test comment, `tests/test_audit_bugs.py:491` ("Bug 18 — switch_account.sh `git add .` sweeps up untracked files"). `PROMPT.md` and `MULTI_TOOL_PROTOCOL.md` describe the switch but don't name the script.

**Flow:**
1. GATE 1 prints `MAX(number)` from projects and asks "Does SESSION.md CURRENT PROJECT match the database? (yes/no)". Anything but `yes` blocks and says to run `update.py --auto`.
2. GATE 2 checks that `CURRICULUM.md` and `CURRICULUM_REASONING.md` exist. If either is missing it prints "Tell Claude: 'Generate full curriculum list now.'" and/or "'Generate CURRICULUM_REASONING.md now.'"
3. GATE 3: projects exist but `mind_model` has no rows → "Tell Claude: 'Generate partial mind model now.'" (warning only).
4. SWITCH STEPS: "1. Ask Claude: 'Generate auto update block now.' 2. Run: python3 update.py --auto 3. Ask Claude: 'Generate SESSION.md update now.' 4. Update SESSION.md". Then it asks "Ready to push? (yes/no)".
5. GATE 4: `git add .`, commit "Checkpoint before account switch — <date>", `git push`. On success it prints "ON NEW ACCOUNT: git pull / python3 start_session.py / Paste PROMPT.md + session output + SESSION.md / Paste CURRICULUM.md + CURRICULUM_REASONING.md / Verify Claude answers all 5 questions correctly".

Sample output (stopped before push): see 2.3.

@@FILE:switch_account.sh@@

### 3.8 Where the sources disagree (facts; not reconciled)

1. **What gets pasted at session start.** `PROMPT.md:445-447` lists PROMPT.md + context.py output + SESSION.md. `start_session.py:428-432` lists those three plus CURRICULUM.md and CURRICULUM_REASONING.md, and uses start_session's step-4 output rather than context.py. `MULTI_TOOL_PROTOCOL.md:70-73` says "Paste ONLY: context.py output, SESSION.md … PROMPT.md is already loaded." `switch_account.sh:132-133` (new account) gives PROMPT.md + session output + SESSION.md, plus the two curriculum files. `mood_check.py:88-90` says run `context.py --mini`.
2. **Which context.** start_session.py step 4 prints its own context, a different layout from `context.py` (compare the samples in 2.3), and no verification question block. Instead it prints the answer key.
3. **How many verification questions.** context.py prints "answer all four" (`context.py:102`). start_session.py's key has Q1–Q5 (`start_session.py:391-423`). `switch_account.sh:134` says "all 5 questions".
4. **Q2's expected answer differs between scripts.** context.py uses `projects.what_failed` (`context.py:84-112`). start_session.py uses `concepts.struggled_with` (`start_session.py:357-393`). In the sample, context.py expects "Assumed p+1 always adds 1 byte" and verification.txt expects "scaling by element size".
5. **Who the adversary is.** `adversary.py:69` says "Open a NEW Claude conversation". `PROMPT.md:341-342` says "opens a second Claude conversation". `MULTI_TOOL_PROTOCOL.md:117` says "Open GPT-4 (NOT a second Claude conversation)". The prompt texts also differ: `PROMPT.md:345-350` versus `adversary.py:75-87`.
6. **Lab transition format.** `LAB_HISTORY.md:9-15` has no SUMMARY line and no "Next lab". `MULTI_TOOL_PROTOCOL.md:203-211` uses "LAB: [name]" with no COURSE. `lab_transition.py:141-147` adds COURSE and SUMMARY.
7. **Mind model timing.** `MULTI_TOOL_PROTOCOL.md:279` says re-upload every 5 projects, while RULE 27 asks for a "Partial mind model if fewer than 5 projects done" at an account switch (`PROMPT.md:593`).
8. **Token budgets.** `estimate_tokens.sh:49` uses a "Safe limit ~150000 tokens" and labels PROMPT.md+SESSION.md+MIND_MODEL.md as "pasted every session" (`estimate_tokens.sh:17`). `MULTI_TOOL_PROTOCOL.md:233-248` says those files load automatically and "~187,000 tokens every session" are available.
9. **Things referenced that don't exist or don't run.** `DECISIONS.md` (`PROMPT.md:526`) is not in the repo. `post_project_handoff_prompt` (`update.py:215`) is never called. `PROMPT.md:389` still reads "[STUDENT PASTES ALL LAB NAMES HERE]", and `PROMPT.md:20-22`, `75` hold "[STUDENT DECLARES THIS EACH SESSION]" / "[STUDENT WRITES ONE SENTENCE HERE]". SESSION.md holds the actual values.

---

## 4. CLAUDE.AI PROJECT ASSUMPTIONS

Facts, from the files:

- **The Project:** "Go to claude.ai / Create a new Project called: malloc-training" (`MULTI_TOOL_PROTOCOL.md:19-20`). "Every session: open THIS project, not a regular chat" (`MULTI_TOOL_PROTOCOL.md:27`).
- **Uploaded as Project knowledge (upload order):** 1. PROMPT.md, 2. MIND_MODEL.md, 3. CURRICULUM.md, 4. CURRICULUM_REASONING.md, 5. LAB_HISTORY.md (`MULTI_TOOL_PROTOCOL.md:21-26`, `272-276`). `LAB_HISTORY.md:4`: "Loaded automatically via Claude Project."
- **Not uploaded; pasted every session:** context.py output and SESSION.md (`MULTI_TOOL_PROTOCOL.md:28-30`, `240-242`).
- **Re-upload schedule:** MIND_MODEL.md every 5 projects; CURRICULUM.md when projects are added; CURRICULUM_REASONING.md every 5 projects; LAB_HISTORY.md after each lab (`MULTI_TOOL_PROTOCOL.md:278-282`).
- **Re-upload triggers in the flows:** after the mind-model update (`MULTI_TOOL_PROTOCOL.md:193-194`), after a new-lab curriculum (`MULTI_TOOL_PROTOCOL.md:176`), and after a lab transition (`MULTI_TOOL_PROTOCOL.md:218-220`; `lab_transition.py:212`).
- **Scripts that name the Project:** `lab_transition.py:126` ("PASTE THIS INTO CLAUDE PROJECT NOW") and `lab_transition.py:212` ("Re-upload LAB_HISTORY.md to Claude Project").
- **Token reasoning built on the Project:** "WHAT LOADS AUTOMATICALLY (Claude Project files)" with per-file estimates; "Compare to the old system where PROMPT.md alone was pasted every session eating 6,400 tokens" (`MULTI_TOOL_PROTOCOL.md:233-255`).
- **Other tools sit beside the Project:** the "Quick reference" sends teaching, projects, quizzes and "everything else" to the Claude Project, books and labs to NotebookLM, tangents to Gemini, the adversarial exam to GPT-4, and curriculum research to Gemini Deep Research (`MULTI_TOOL_PROTOCOL.md:257-266`).

**INFERENCE:**
- Project knowledge is a copy, so every edit to these five files on disk must be re-uploaded by hand. If a re-upload is missed, Claude reads stale files with no sign of it; no script checks the uploaded copy.
- The scripts that tell the user to paste PROMPT.md and the curriculum files (`start_session.py:428-432`, `switch_account.sh:132-133`) predate the Project setup, or ignore it. Following both would load those files twice.
- Projects are per account. The account switch implies the Project has to exist, with current uploads, on every account. No file says this explicitly; `switch_account.sh:129-134` says only to pull, run start_session and paste.

---

## 5. WEB-CLAUDE ASSUMPTIONS (INFERENCE)

Each point is my interpretation of the cited lines.

**Manual copy/paste as the only channel to Claude**
- Every context script prints to the terminal for the user to copy: `start_session.py:427-432`, `context.py` (whole output), `adversary.py:74`, `lab_transition.py:126`, `update.py:74`.
- `PROMPT.md:49-51` ("PASTE REAL OUTPUT … Always paste it directly") assumes Claude can't run the program or see the terminal.
- The external lookups (NotebookLM, Gemini) get pasted back by hand (`MULTI_TOOL_PROTOCOL.md:84-96`).
- The real-world output is pasted as a GitHub link (`PROMPT.md:378`).

**Claude has no file access**
- start_session.py tells the user to paste `CURRICULUM.md` and `CURRICULUM_REASONING.md` (`start_session.py:431-432`). Yet RULE 25 tells Claude to `cat` them (`PROMPT.md:555-557`), which web Claude can't do, so in practice it reads the pasted or Project copy.
- `SESSION.md` is pasted every session (`PROMPT.md:447`; `MULTI_TOOL_PROTOCOL.md:30`). Claude never writes it: Claude generates "SESSION.md replacement content" and the user edits the file (`PROMPT.md:523`; `switch_account.sh:94-95`).
- Claude can't query brain.db, so `context.py` exists to flatten the database into pasteable text (`PROMPT.md:426-433`).
- The curriculum files are saved by hand from Claude's output (`MULTI_TOOL_PROTOCOL.md:173-176`; `switch_account.sh:44-47`).

**Running out of tokens**
- "WHEN TOKENS RUN LOW" (`PROMPT.md:464-471`), RULE 27 (`PROMPT.md:586-599`), and the whole of `switch_account.sh`.
- `estimate_tokens.sh` budgets pasted context against "~150000 tokens" and warns when files grow (`estimate_tokens.sh:49-71`).
- "context.py always generates fixed size output … Token budget is always the same" (`PROMPT.md:478-480`). The mini context, "last 5" and "last 10" limits in the context output also look like size control.
- "Don't waste Claude session tokens on tangents" (`MULTI_TOOL_PROTOCOL.md:101`).
- "Handoff collected here — mid-session, not at token limit" (`update.py:356`) and "generate this in Claude NOW while sharp" (`update.py:357`): this assumes the conversation can end without warning.

**Losing memory between sessions and accounts**
- "You have no memory between sessions." (`PROMPT.md:425`).
- The handoff instruction is written "for next Claude instance" (`PROMPT.md:525`), and verification Q3 asks Claude to restate it verbatim (`context.py:113`).
- The verification questions exist to prove the new Claude actually read the pasted context. "Vague answer = Claude has not read the reasoning file" (`start_session.py:422-423`); "repaste, re-verify" (`context.py:105`).
- "Ask previous Claude to regenerate it." (`PROMPT.md:583`) assumes an earlier conversation the new one can't reach.
- GitHub serves as the sync between accounts: "brain.db on GitHub is the single source of truth" (`PROMPT.md:474-476`). switch_account's GATE 4 refuses to bless a switch until the push succeeds (`switch_account.sh:105-142`).
- `MIND_MODEL.md` and `LAB_HISTORY.md` are hand-maintained summaries that carry the student model across conversations (`MIND_MODEL.md:3-7`; `LAB_HISTORY.md:5`).

**Answers pasted back in by hand**
- Every store script takes multi-line pasted text ended by `END` (`prompts.py:91-106`): the auto block and final code (`update.py:298`, `414`), the mind model (`update.py:86-87`), the transition summary (`lab_transition.py:155-156`), the gap report (`adversary.py:92-93`), "Claude evaluation" (`update_exam.py:16`), the full spec "as given by Claude" (`update_full_detail.py:64-65`), and the handout extraction (`store_handout.py:13-21`).
- The parsers depend on Claude's text using exact line prefixes: `OWNED:`/`CARRIED FORWARD:`… (`lab_transition.py:169-177`) and the auto-block keys at line starts (`update.py:33-46`). A Claude that formats its answer differently breaks the stored fields without any error.
- The user grades Claude's verification answers by eye against `verification.txt` (`MULTI_TOOL_PROTOCOL.md:75-76`; `start_session.py:383-386`).

**Separate conversations as separate instances**
- The adversarial exam is meant to be a different conversation (or a different model) because "The teaching instance cannot see its own blind spots" (`PROMPT.md:360-361`; `MULTI_TOOL_PROTOCOL.md:133-137`).

---

## 6. VERIFICATION AND SIZE

@@VERIFY@@
