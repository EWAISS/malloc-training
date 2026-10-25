"""
prompts.py — shared input helpers for every interactive script.

Ctrl+D or Ctrl+C at any prompt cancels the whole script: it prints
"Cancelled, nothing saved." and exits 1. Scripts collect every answer
before they write, so a cancel never leaves half a record behind.
Bad input re-asks instead of crashing.
"""
import sys

CANCELLED = "Cancelled, nothing saved."


def _read(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(f"\n{CANCELLED}")
        sys.exit(1)


def ask_text(prompt, default=None, required=False):
    """One line, stripped. Empty answer gives default (or '')."""
    while True:
        value = _read(prompt).strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ''
        print("  An answer is required.")


def ask_int(prompt, lo=None, hi=None):
    """Whole number in [lo, hi]. Re-asks until valid."""
    if lo is not None and hi is not None:
        hint = f"a whole number from {lo} to {hi}"
    elif lo is not None:
        hint = f"a whole number, {lo} or more"
    else:
        hint = "a whole number"
    while True:
        raw = _read(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            value = None
        if value is not None \
                and (lo is None or value >= lo) \
                and (hi is None or value <= hi):
            return value
        print(f"  Please enter {hint}.")


def ask_float(prompt, lo, hi):
    """Number in [lo, hi]. Re-asks until valid."""
    while True:
        raw = _read(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            value = None
        if value is not None and lo <= value <= hi:
            return value
        print(f"  Please enter a number from {lo:g} to {hi:g}.")


def ask_yes_no(prompt):
    """True for yes/y, False for no/n (any case, any spacing)."""
    while True:
        value = _read(prompt).strip().lower()
        if value in ('yes', 'y'):
            return True
        if value in ('no', 'n'):
            return False
        print("  Please answer yes or no.")


def ask_choice(prompt, choices, default=None):
    """One of choices (case-insensitive). Returns the canonical value."""
    while True:
        value = _read(prompt).strip().lower()
        if not value and default is not None:
            return default
        if value in choices:
            return value
        print(f"  Please answer one of: {', '.join(choices)}.")


def ask_multiline(prompt, required=False):
    """Lines until END. Returns the text with outer blank lines removed."""
    while True:
        if prompt:
            print(prompt)
        print("Type END on a new line when done:")
        lines = []
        while True:
            line = _read('')
            if line.strip() == "END":
                break
            lines.append(line)
        text = "\n".join(lines).strip('\n')
        if text.strip() or not required:
            return text
        print("  An answer is required.")
