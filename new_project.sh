#!/bin/bash
PHASE=$1
NUMBER=$(printf "%02d" $2)
FILE=~/projects/malloc-training/phase${PHASE}/project${NUMBER}.c
cat > $FILE << 'CEOF'
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
code $FILE
