"""
curriculum_status.py
Shows completed vs pending projects by comparing
brain.db against CURRICULUM.md.
Run anytime to see where you are in the curriculum.
"""

import sqlite3
import os
import re

PROJ    = os.path.expanduser('~/projects/malloc-training')
DB_PATH = os.path.join(PROJ, 'brain.db')
CURR_PATH = os.path.join(PROJ, 'CURRICULUM.md')
REASON_PATH = os.path.join(PROJ, 'CURRICULUM_REASONING.md')


def get_completed():
    """Get all completed project numbers from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'SELECT number, name, concept, status '
            'FROM projects ORDER BY number')
        rows = c.fetchall()
        conn.close()
        return {row[0]: row for row in rows}
    except Exception as e:
        print(f"Database error: {e}")
        return {}


def get_planned():
    """Parse planned projects from CURRICULUM.md."""
    if not os.path.exists(CURR_PATH):
        return []

    planned = []
    current = {}

    with open(CURR_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line.startswith('PROJECT '):
                if current:
                    planned.append(current)
                try:
                    num = int(line.split()[1])
                    current = {'number': num}
                except (IndexError, ValueError):
                    current = {}
            elif ':' in line and current:
                key, _, value = line.partition(':')
                current[key.strip().lower()] = value.strip()

    if current:
        planned.append(current)

    return planned


def get_next_reasoning():
    """Pull next project reasoning from CURRICULUM_REASONING.md."""
    if not os.path.exists(REASON_PATH):
        return None

    lines = []
    in_next = False
    count = 0

    with open(REASON_PATH) as f:
        for line in f:
            if line.startswith('NEXT PROJECT:') and count < 1:
                in_next = True
                count += 1
                lines.append(line.rstrip())
            elif line.startswith('NEXT PROJECT:') and count >= 1:
                break
            elif in_next and line.strip() and \
                 not line.startswith('#'):
                lines.append(line.rstrip())
            elif in_next and not line.strip():
                if lines:
                    break

    return '\n'.join(lines) if lines else None


def main():
    print("=" * 58)
    print("CURRICULUM STATUS")
    print("=" * 58)

    completed = get_completed()
    planned   = get_planned()

    if not planned:
        print("\nNo CURRICULUM.md found or no projects defined.")
        print("Run: python3 curriculum_status.py after generating")
        print("CURRICULUM.md from Claude.")
        if completed:
            print(f"\nDatabase has {len(completed)} completed projects:")
            for num, row in sorted(completed.items()):
                print(f"  [DONE] Project {num} — {row[1]} ({row[2]})")
        return

    total_planned   = len(planned)
    total_completed = len(completed)
    total_pending   = total_planned - total_completed

    print(f"\nTotal planned  : {total_planned}")
    print(f"Completed      : {total_completed}")
    print(f"Pending        : {total_pending}")

    if total_planned > 0:
        pct = int((total_completed / total_planned) * 100)
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        print(f"Progress       : [{bar}] {pct}%")

    # Find next pending
    next_project = None
    for p in planned:
        num = p.get('number')
        if num and num not in completed:
            next_project = p
            break

    print("\n" + "─" * 58)

    # Print completed
    print("\nCOMPLETED:")
    any_done = False
    for p in planned:
        num = p.get('number')
        if num and num in completed:
            db_row = completed[num]
            print(f"  [✓] Project {num} — "
                  f"{db_row[1]} ({db_row[2]}) "
                  f"[{db_row[3]}]")
            any_done = True
    if not any_done:
        print("  None yet.")

    # Print pending
    print("\nPENDING:")
    any_pending = False
    for p in planned:
        num = p.get('number')
        if num and num not in completed:
            marker = "► NEXT" if p == next_project else "  [ ]"
            name    = p.get('name', '?')
            concept = p.get('concept', '?')
            gap     = p.get('gap', '')
            print(f"  {marker} Project {num} — {name} ({concept})")
            if gap:
                print(f"         Gap: {gap}")
            any_pending = True
    if not any_pending:
        print("  All projects completed.")

    # Next project reasoning
    if next_project:
        print("\n" + "─" * 58)
        print(f"NEXT UP: Project {next_project.get('number')} — "
              f"{next_project.get('name', '?')}")
        reasoning = get_next_reasoning()
        if reasoning:
            print("\nREASONING (from CURRICULUM_REASONING.md):")
            print(reasoning)
        else:
            print("\nNo reasoning file found.")
            print("Generate: ask Claude for CURRICULUM_REASONING.md")

    # Warn if database has projects not in curriculum
    extra = set(completed.keys()) - \
            {p.get('number') for p in planned}
    if extra:
        print("\n" + "─" * 58)
        print("WARNING: Projects in database but not in CURRICULUM.md:")
        for num in sorted(extra):
            row = completed[num]
            print(f"  Project {num} — {row[1]} ({row[2]})")
        print("Update CURRICULUM.md to include these.")

    print("\n" + "=" * 58)
    print("To update reasoning for next 5 projects:")
    print("  Tell Claude: 'Update CURRICULUM_REASONING.md")
    print("  for the next 5 projects based on current state.'")
    print("=" * 58)


main()
