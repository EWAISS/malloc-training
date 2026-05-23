#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "BEFORE SWITCHING ACCOUNTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROJ=~/projects/malloc-training

# ── GATE 1: Check update.py was run ──────────
echo ""
echo "GATE 1 — Checking database is current..."
python3 - << 'EOF'
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser(
    '~/projects/malloc-training/brain.db'))
c = conn.cursor()
c.execute('SELECT MAX(number) FROM projects')
last = c.fetchone()[0] or 0
print(f"  Last project in database : {last}")
print(f"  Check SESSION.md CURRENT PROJECT matches this.")
print(f"  If SESSION.md shows higher number — run update.py first.")
conn.close()
EOF

echo ""
read -p "Does SESSION.md CURRENT PROJECT match the database? (yes/no): " match
if [ "$match" != "yes" ]; then
    echo ""
    echo "BLOCKED — Run update.py before switching."
    echo "  python3 ~/projects/malloc-training/update.py --auto"
    echo "Then re-run switch_account.sh"
    exit 1
fi

# ── GATE 2: Curriculum reasoning saved ───────
echo ""
echo "GATE 2 — Curriculum check..."
if [ ! -f "$PROJ/CURRICULUM.md" ]; then
    echo "  WARNING: No CURRICULUM.md found."
    echo "  If Claude designed future projects this session:"
    read -p "  Did Claude design future projects? (yes/no): " designed
    if [ "$designed" == "yes" ]; then
        echo ""
        echo "  BLOCKED — Save curriculum before switching."
        echo "  Tell Claude: 'Generate full curriculum list now.'"
        echo "  Save output to CURRICULUM.md"
        echo "  Tell Claude: 'Generate CURRICULUM_REASONING.md now.'"
        echo "  Save output to CURRICULUM_REASONING.md"
        echo "  Then re-run switch_account.sh"
        exit 1
    fi
else
    echo "  CURRICULUM.md exists — OK"
fi

if [ ! -f "$PROJ/CURRICULUM_REASONING.md" ]; then
    echo "  WARNING: No CURRICULUM_REASONING.md found."
    read -p "  Continue without it? (yes/no): " cont
    if [ "$cont" != "yes" ]; then
        echo "  Tell Claude: 'Generate CURRICULUM_REASONING.md now.'"
        exit 1
    fi
else
    echo "  CURRICULUM_REASONING.md exists — OK"
fi

# ── GATE 3: Mind model current ────────────────
echo ""
echo "GATE 3 — Mind model check..."
python3 - << 'EOF'
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser(
    '~/projects/malloc-training/brain.db'))
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM projects')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM mind_model')
mm_count = c.fetchone()[0]
conn.close()
if total > 0 and mm_count == 0:
    print(f"  WARNING: {total} projects done but no mind model yet.")
    print("  Tell Claude: 'Generate partial mind model now.'")
    print("  Save to MIND_MODEL.md before switching.")
else:
    print(f"  Mind model entries: {mm_count} — OK")
EOF

# ── STEP 1: Standard switch steps ────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SWITCH STEPS — do these in order"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Ask Claude: 'Generate auto update block now.'"
echo "2. Run: python3 update.py --auto"
echo "3. Ask Claude: 'Generate SESSION.md update now.'"
echo "4. Update SESSION.md"
echo "5. Run the push check below"
echo ""

read -p "Ready to push? (yes/no): " ready
if [ "$ready" != "yes" ]; then
    echo "Complete steps 1-4 first."
    exit 1
fi

# ── GATE 4: Verified push ─────────────────────
echo ""
echo "GATE 4 — Pushing to GitHub..."
cd $PROJ
git add .
git push

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PUSH SUCCESS — safe to switch accounts"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "ON NEW ACCOUNT:"
    echo "  git pull"
    echo "  python3 start_session.py"
    echo "  Paste PROMPT.md + session output + SESSION.md"
    echo "  Paste CURRICULUM.md + CURRICULUM_REASONING.md"
    echo "  Verify Claude answers all 5 questions correctly"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PUSH FAILED — DO NOT SWITCH ACCOUNTS"
    echo "Fix network/auth issue and re-run switch_account.sh"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
