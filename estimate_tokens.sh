#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TOKEN ESTIMATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

estimate() {
    if [ -f "$1" ]; then
        chars=$(wc -c < "$1")
        tokens=$((chars / 4))
        echo "  $1: ~$tokens tokens"
    else
        echo "  $1: (not found)"
    fi
}

echo ""
echo "CORE FILES (pasted every session):"
estimate ~/projects/malloc-training/PROMPT.md
estimate ~/projects/malloc-training/SESSION.md
estimate ~/projects/malloc-training/MIND_MODEL.md

echo ""
echo "CURRICULUM FILES (pasted on account switch):"
estimate ~/projects/malloc-training/CURRICULUM.md
estimate ~/projects/malloc-training/CURRICULUM_REASONING.md

echo ""
echo "TOTALS:"

CORE=$(cat ~/projects/malloc-training/PROMPT.md \
           ~/projects/malloc-training/SESSION.md \
           ~/projects/malloc-training/MIND_MODEL.md \
           2>/dev/null | wc -c)
CORE_TOKENS=$((CORE / 4))
echo "  Core (every session)     : ~$CORE_TOKENS tokens"

CURR=$(cat ~/projects/malloc-training/CURRICULUM.md \
           ~/projects/malloc-training/CURRICULUM_REASONING.md \
           2>/dev/null | wc -c)
CURR_TOKENS=$((CURR / 4))
echo "  Curriculum (on switch)   : ~$CURR_TOKENS tokens"

SWITCH_TOTAL=$(( CORE_TOKENS + CURR_TOKENS ))
echo "  Switch session total     : ~$SWITCH_TOTAL tokens"
echo "  Normal session total     : ~$CORE_TOKENS tokens"

echo ""
echo "BUDGET:"
echo "  Safe limit               : ~150000 tokens"
echo "  Normal session remaining : ~$((150000 - CORE_TOKENS)) tokens"
echo "  Switch session remaining : ~$((150000 - SWITCH_TOTAL)) tokens"

echo ""

# Warnings
if [ $CORE_TOKENS -gt 20000 ]; then
    echo "  WARNING: Core files exceed 20k tokens."
    echo "  MIND_MODEL.md may be getting large."
    echo "  Consider summarizing older micro-updates."
fi

if [ $CURR_TOKENS -gt 10000 ]; then
    echo "  WARNING: Curriculum files exceed 10k tokens."
    echo "  Trim CURRICULUM_REASONING.md to next 5 projects only."
    echo "  Move older reasoning to summary lines."
fi

if [ $SWITCH_TOTAL -gt 40000 ]; then
    echo "  WARNING: Switch session overhead exceeds 40k tokens."
    echo "  Reduce file sizes before switching accounts."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
