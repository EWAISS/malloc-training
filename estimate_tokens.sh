#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TOKEN ESTIMATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
estimate() {
    if [ -f "$1" ]; then
        chars=$(wc -c < "$1")
        tokens=$((chars / 4))
        echo "  $1: ~$tokens tokens"
    fi
}
estimate ~/projects/malloc-training/PROMPT.md
estimate ~/projects/malloc-training/SESSION.md
estimate ~/projects/malloc-training/MIND_MODEL.md
TOTAL=$(cat ~/projects/malloc-training/PROMPT.md \
            ~/projects/malloc-training/SESSION.md \
            ~/projects/malloc-training/MIND_MODEL.md \
            2>/dev/null | wc -c)
TOTAL_TOKENS=$((TOTAL / 4))
echo ""
echo "Total: ~$TOTAL_TOKENS tokens"
echo "Safe budget remaining: ~$((150000 - TOTAL_TOKENS)) tokens"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
