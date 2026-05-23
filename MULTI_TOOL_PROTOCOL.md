# MULTI-TOOL PROTOCOL
# malloc-training system — tool division of labor
# Each tool has one job. Never use the wrong tool for a job.
# ═══════════════════════════════════════════════════════════

## THE FIVE TOOLS

### 1. CLAUDE PROJECTS — Primary Teacher
### 2. GEMINI — Book and Document Lookup  
### 3. NOTEBOOKLM — Lab Reference
### 4. GPT-4 — Adversarial Examiner
### 5. GEMINI DEEP RESEARCH — Curriculum Design

# ═══════════════════════════════════════════════════════════
## SETUP — DO ONCE
# ═══════════════════════════════════════════════════════════

### CLAUDE PROJECT SETUP
1. Go to claude.ai
2. Create a new Project called: malloc-training
3. Upload these files to the Project:
   - PROMPT.md
   - MIND_MODEL.md
   - CURRICULUM.md
   - CURRICULUM_REASONING.md
4. Create and upload LAB_HISTORY.md (empty for now)
5. Every session: open THIS project, not a regular chat
6. Only paste two things per session:
   - context.py output
   - SESSION.md contents

### NOTEBOOKLM SETUP
1. Go to notebooklm.google.com
2. Create a notebook called: malloc-training-labs
3. Upload ALL lab PDFs:
   - L0 C Programming Lab PDF
   - L1 Data Lab PDF
   - L5 Malloc Lab PDF
   - L7 Proxy Lab PDF
   - CMU 15-418 Assignment 1 and 2 PDFs
   - Stanford CS144 Check 0-7 PDFs
   - MIT 6.828 all lab PDFs
   - MIT 6.5840 all lab PDFs
   - CMU 15-445 all project PDFs
4. Create a second notebook called: malloc-training-books
5. Upload book PDFs you have:
   - CS:APP
   - OSTEP
   - K&R
   - Effective C

### GEMINI SETUP
1. Go to gemini.google.com
2. No setup needed — use for on-demand queries
3. For Deep Research: use Gemini Advanced

### GPT-4 SETUP
1. Go to chatgpt.com
2. No setup needed — used only for adversarial exams
3. Keep the adversary prompt from adversary.py saved somewhere accessible

# ═══════════════════════════════════════════════════════════
## SESSION PROTOCOL — EVERY SESSION
# ═══════════════════════════════════════════════════════════

STEP 1 — Run start_session.py on your machine
  python3 start_session.py

STEP 2 — Open Claude Project (malloc-training)
  Paste ONLY:
  - context.py output
  - SESSION.md contents
  PROMPT.md is already loaded. Do not paste it again.

STEP 3 — Claude answers verification questions
  Check against verification.txt on your machine.

STEP 4 — Work begins.

# ═══════════════════════════════════════════════════════════
## DURING A PROJECT — WHICH TOOL FOR WHAT
# ═══════════════════════════════════════════════════════════

SITUATION: Claude says "read CS:APP section 9.9"
→ USE: NotebookLM (malloc-training-books notebook)
→ ASK: "What does CS:APP section 9.9 say about [topic]?"
→ PASTE: The relevant excerpt back to Claude
→ WHY: NotebookLM reads from the actual PDF. Claude reads
        from training data memory of the book. NotebookLM
        is more precise for exact content.

SITUATION: Claude says "check the lab constraints"
→ USE: NotebookLM (malloc-training-labs notebook)
→ ASK: "What are the exact constraints in [lab name]?"
→ PASTE: The answer back to Claude
→ WHY: Lab requirements come from the PDF not from memory.

SITUATION: You want to understand something outside the project
→ USE: Gemini
→ ASK: Whatever you want to know
→ WHY: Don't waste Claude session tokens on tangents.
        Gemini handles exploration. Claude handles curriculum.

SITUATION: You need to look up a specific concept in a book
→ USE: Gemini (upload the PDF or use its training data)
→ ASK: "Explain [concept] from a systems programming perspective"
→ WHY: Save Claude tokens for teaching your specific gap.

# ═══════════════════════════════════════════════════════════
## AFTER EVERY PHASE — ADVERSARIAL EXAM PROTOCOL
# ═══════════════════════════════════════════════════════════

STEP 1 — Run adversary.py on your machine
  python3 adversary.py
  Copy the adversary prompt it generates.

STEP 2 — Open GPT-4 (NOT a second Claude conversation)
  Paste the adversary prompt exactly.
  Answer every question from first principles.
  Do not look anything up.
  Do not ask for hints.

STEP 3 — GPT-4 reports the gap in one sentence.
  Copy that sentence.

STEP 4 — Return to Claude Project.
  Paste the gap report.
  Claude repairs the gap before phase progression.

STEP 5 — Run adversary.py again to record the gap.
  Paste the one-sentence gap report when prompted.

WHY GPT-4 INSTEAD OF SECOND CLAUDE:
  Claude trained on the same data as your teaching Claude.
  It may unconsciously use the same analogies and miss
  the same gaps. GPT-4 has different training, different
  blind spots, finds genuinely different gaps.

# ═══════════════════════════════════════════════════════════
## BEFORE STARTING A NEW LAB — CURRICULUM DESIGN PROTOCOL
# ═══════════════════════════════════════════════════════════

STEP 1 — Run Gemini Deep Research
  Open Gemini Advanced
  Ask exactly:
  "Deep research: What are the hardest concepts in
  [LAB NAME] for students with no systems programming
  background? What misconceptions appear most often in
  student implementations? What order should concepts
  be taught to build the correct mental model?
  Include references to course materials and student
  writeups where available."

STEP 2 — Save the research output to a file
  Save as: lab_research_[labname].md
  Store in: ~/projects/malloc-training/

STEP 3 — Store the lab handout
  python3 store_handout.py
  Use NotebookLM to extract the structured data from the PDF.
  Paste the extraction into store_handout.py fields.

STEP 4 — Open Claude Project
  Paste:
  - context.py output
  - SESSION.md
  - Contents of lab_research_[labname].md
  Tell Claude:
  "Generate the curriculum for [LAB NAME].
   Use the research above and CURRICULUM_REASONING format.
   Be specific to my weakness patterns from the database."

STEP 5 — Save outputs
  Save CURRICULUM.md update
  Save CURRICULUM_REASONING.md update
  Re-upload both to Claude Project
  git add . && git commit -m "New lab curriculum: [LAB]" && git push

# ═══════════════════════════════════════════════════════════
## AFTER EVERY 5 PROJECTS — MIND MODEL UPDATE PROTOCOL
# ═══════════════════════════════════════════════════════════

STEP 1 — update.py triggers mind model prompt automatically
  Copy the prompt it prints.

STEP 2 — Ask Claude Project to generate the update
  Claude has full session context — it knows exactly
  what happened in the last 5 projects.

STEP 3 — Save the paragraph to MIND_MODEL.md
  Append it as update.py instructs.

STEP 4 — Re-upload MIND_MODEL.md to Claude Project
  The updated mind model is now loaded for all future sessions.

STEP 5 — Commit to git
  git add . && git commit -m "Mind model update after Project N" && git push

# ═══════════════════════════════════════════════════════════
## AFTER COMPLETING A LAB — LAB TRANSITION PROTOCOL
# ═══════════════════════════════════════════════════════════

STEP 1 — Ask Claude Project:
  "Generate a lab transition summary for [LAB NAME].
   Format:
   LAB: [name]
   OWNED: [top 5 concepts, one line each]
   CARRIED FORWARD: [what transfers to future labs]
   WATCH FOR: [weakness patterns to remember]
   KEY ANALOGY: [the one analogy that worked best]
   One paragraph total. Be specific to my performance."

STEP 2 — Append to LAB_HISTORY.md
  Keep all lab summaries in this file.
  One paragraph per lab. Never delete old ones.
  After 30 labs this is ~3,000 tokens — acceptable.

STEP 3 — Re-upload LAB_HISTORY.md to Claude Project
  Every future session now has your full lab history
  loaded automatically with zero paste cost.

STEP 4 — Update SESSION.md
  Change ACTIVE LAB and ACTIVE COURSE.
  Run start_session.py to verify.

STEP 5 — Commit everything
  git add . && git commit -m "Lab complete: [LAB NAME]" && git push

# ═══════════════════════════════════════════════════════════
## TOKEN BUDGET WITH THIS SYSTEM
# ═══════════════════════════════════════════════════════════

WHAT LOADS AUTOMATICALLY (Claude Project files):
  PROMPT.md              ~6,400 tokens
  MIND_MODEL.md          ~200 tokens (grows slowly)
  CURRICULUM.md          ~500 tokens
  CURRICULUM_REASONING.md ~800 tokens
  LAB_HISTORY.md         ~100 tokens per lab completed

WHAT YOU PASTE PER SESSION:
  context.py output      ~2,000 tokens
  SESSION.md             ~60 tokens

TOTAL EARLY (lab 1):     ~10,000 tokens overhead
TOTAL LATE (lab 10):     ~11,000 tokens overhead
TOTAL LATE (lab 30):     ~13,000 tokens overhead

AVAILABLE FOR TEACHING:  ~187,000 tokens every session
GROWS BY:                ~100 tokens per lab completed

This budget is essentially fixed forever.
Compare to the old system where PROMPT.md alone
was pasted every session eating 6,400 tokens before
a single word of teaching happened.

# ═══════════════════════════════════════════════════════════
## QUICK REFERENCE — WHICH TOOL
# ═══════════════════════════════════════════════════════════

Teaching, projects, quizzes          → Claude Project
Book chapter lookup                  → NotebookLM (books)
Lab constraint lookup                → NotebookLM (labs)
General exploration / tangents       → Gemini
Adversarial exam                     → GPT-4
New lab curriculum research          → Gemini Deep Research
Everything else                      → Claude Project

# ═══════════════════════════════════════════════════════════
## FILES TO ADD TO CLAUDE PROJECT (upload order)
# ═══════════════════════════════════════════════════════════

1. PROMPT.md             — upload now
2. MIND_MODEL.md         — upload now (empty template)
3. CURRICULUM.md         — upload now (empty template)
4. CURRICULUM_REASONING.md — upload now (empty template)
5. LAB_HISTORY.md        — create and upload now (empty)

UPDATE SCHEDULE:
  MIND_MODEL.md          — re-upload every 5 projects
  CURRICULUM.md          — re-upload when new projects added
  CURRICULUM_REASONING.md — re-upload every 5 projects
  LAB_HISTORY.md         — re-upload after each lab completes
