#!/bin/bash
# install_fixes.sh
# Run from anywhere. Deploys all 8 fixes into ~/projects/malloc-training.
# Safe to re-run — overwrites scripts, never touches brain.db directly.

set -e
PROJ=~/projects/malloc-training
FIXES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================================="
echo "MALLOC-TRAINING — INSTALLING 8 FAILURE MODE FIXES"
echo "=================================================="

# ── 1. Verify project directory exists ──────────────
if [ ! -d "$PROJ" ]; then
    echo "ERROR: $PROJ not found."
    echo "Clone the repo first: git clone <your-repo-url> $PROJ"
    exit 1
fi

# ── 2. Copy all new/updated scripts ─────────────────
echo ""
echo "Copying scripts..."
for f in db_check.py update.py context.py adversary.py \
          mood_check.py validate_concept.py init_db.py; do
    cp "$FIXES_DIR/$f" "$PROJ/$f"
    echo "  OK: $f"
done

# ── 3. Install pre-commit hook ───────────────────────
echo ""
echo "Installing pre-commit hook..."
cp "$FIXES_DIR/pre-commit" "$PROJ/.git/hooks/pre-commit"
chmod +x "$PROJ/.git/hooks/pre-commit"
echo "  OK: .git/hooks/pre-commit"

# ── 4. Run database migration ────────────────────────
echo ""
echo "Running database migration..."
cd "$PROJ"
python3 init_db.py

# ── 5. Run integrity check ───────────────────────────
echo ""
echo "Running database integrity check..."
python3 db_check.py && echo "  Database is clean." \
    || echo "  Warnings above — review before continuing."

# ── 6. Print updated session protocol ───────────────
echo ""
echo "=================================================="
echo "INSTALL COMPLETE"
echo "=================================================="
echo ""
echo "UPDATED SESSION PROTOCOL:"
echo ""
echo "  START OF EVERY SESSION:"
echo "    python3 mood_check.py"
echo "    git pull"
echo "    python3 context.py --mini   (quick)"
echo "    python3 context.py          (full)"
echo "    Paste PROMPT.md + context output + SESSION.md"
echo "    Verify Claude's 4-question context check"
echo ""
echo "  AFTER EVERY PROJECT:"
echo "    python3 update.py"
echo "    python3 db_check.py"
echo "    git add . && git commit -m 'Project N complete' && git push"
echo ""
echo "  AFTER EVERY 5 PROJECTS:"
echo "    update.py triggers mind model prompt automatically"
echo ""
echo "  AFTER EVERY PHASE TRANSFER EXAM:"
echo "    python3 adversary.py"
echo "    python3 validate_concept.py   (3x — one per key concept)"
echo "    python3 db_check.py"
echo "    git add . && git commit -m 'Phase N complete' && git push"
echo ""
echo "  IF GAP > 7 DAYS:"
echo "    context.py will gate you — quiz before proceeding"
echo ""
echo "=================================================="
