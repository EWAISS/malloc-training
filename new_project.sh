#!/bin/bash
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./new_project.sh <phase> <project number>"
    exit 1
fi
PHASE=$1
NUMBER=$(printf "%02d" "$2")
FILE=~/projects/malloc-training/phase${PHASE}/project${NUMBER}.c
if [ -e "$FILE" ]; then
    echo "ERROR: $FILE already exists — not overwriting your code."
    exit 1
fi
mkdir -p "$(dirname "$FILE")"
cat > "$FILE" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/*
 * Project : [NAME]
 * Course  : [COURSE]
 * Lab     : [LAB]
 * Phase   : [PHASE]
 * Concept : [CONCEPT]
 * Status  : in progress
 */

int main() {
    return 0;
}
CEOF
echo "Created: $FILE"
code "$FILE"
