"""
packlib.py — shared by build_pack.py and build_context_pack.py.

Every verbatim block is written with a marker comment naming its source,
so verify_blocks() can parse it back out of the finished pack and compare
it byte for byte with the file it claims to copy.
"""
import re
import subprocess
from pathlib import Path

FENCE = '````'
# The closing fence is the same run of backticks as the opening one
_BLOCK = re.compile(r'<!-- VERBATIM (FILE|LINES|EXTRA) ([^>]*?) -->\n(`{4,})\w*\n(.*?)\3(?!`)', re.S)


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True).stdout


def head_commit(repo):
    return git(repo, 'rev-parse', 'HEAD').strip()


def fence(text, lang='text'):
    """At least four backticks, and always longer than any run of
    backticks in text, so the content can never close the fence."""
    longest = max((len(r) for r in re.findall(r'`+', text)), default=0)
    f = '`' * max(len(FENCE), longest + 1)
    nl = '' if text.endswith('\n') or text == '' else '\n'
    return f"{f}{lang}\n{text}{nl}{f}"


def _lines(data):
    return data.count('\n') + (0 if data.endswith('\n') or not data else 1)


def file_block(repo, name, level=3, lang='text', heading=None):
    data = (Path(repo) / name).read_text()
    note = '' if data.endswith('\n') else ' — file has no trailing newline'
    heading = heading or f"`{name}` — full contents"
    n = _lines(data)
    return (f"{'#' * level} {heading} ({len(data.encode())} bytes, {n} line{'' if n == 1 else 's'}{note})\n\n"
            f"<!-- VERBATIM FILE {name} -->\n{fence(data, lang)}")


def lines_block(repo, name, a, b):
    src = (Path(repo) / name).read_text().split('\n')
    text = '\n'.join(src[a - 1:b]) + '\n'
    return f"`{name}:{a}-{b}`\n\n<!-- VERBATIM LINES {name} {a} {b} -->\n{fence(text)}"


def extra_block(key, text, lang='text'):
    """Command output (or other text) that verify_blocks checks against extra[key]."""
    return f"<!-- VERBATIM EXTRA {key} -->\n{fence(text, lang)}"


def verify_blocks(repo, doc, extra=None):
    """[(name, matches)] for every verbatim block in doc."""
    extra = extra or {}
    results = []
    for m in _BLOCK.finditer(doc):
        kind, spec, body = m.group(1), m.group(2), m.group(4)
        if kind == 'FILE':
            src = (Path(repo) / spec).read_text()
            results.append((f'{spec} (full)', body == (src if src.endswith('\n') else src + '\n')))
        elif kind == 'LINES':
            name, a, b = spec.rsplit(' ', 2)
            src = '\n'.join((Path(repo) / name).read_text().split('\n')[int(a) - 1:int(b)]) + '\n'
            results.append((f'{name}:{a}-{b}', body == src))
        else:
            src = extra[spec]
            results.append((spec, body == (src if src.endswith('\n') or not src else src + '\n')))
    return results
