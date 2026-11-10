"""Minimal S-expression reader/writer for KiCad files (py3.9 compatible)."""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


class Sym(str):
    """Bare (unquoted) atom."""


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("parse error at %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            s = m.group(3)[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            cur.append(s)
        else:
            cur.append(Sym(m.group(4)))
    return cur[0] if len(cur) == 1 else cur


def dump(x, indent=0):
    if isinstance(x, list):
        if not x:
            return "()"
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + dump(x[0])
        for e in x[1:]:
            if isinstance(e, list):
                out += "\n" + "\t" * (indent + 1) + dump(e, indent + 1)
            else:
                out += " " + dump(e)
        return out + "\n" + "\t" * indent + ")"
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        r = ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)
        return "0" if r == "-0" else r
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"') + '"'


def find(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None
