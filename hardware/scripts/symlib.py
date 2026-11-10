"""Load KiCad library symbols and their pins."""
import os, copy
from sexp import parse, find, find1, Sym

KICAD = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/SharedSupport")
SYMDIR = os.path.join(KICAD, "symbols")
_libs = {}
PROJECT = os.path.basename(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))


def _lib(name):
    if name not in _libs:
        path = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", PROJECT + ".kicad_sym")
                if name == PROJECT else os.path.join(SYMDIR, name + ".kicad_sym"))
        with open(path) as f:
            tree = parse(f.read())
        _libs[name] = {s[1]: s for s in find(tree, "symbol")}
    return _libs[name]


def load(lib_id):
    """Return a flattened symbol s-expr named 'Lib:Name' (extends resolved)."""
    lib, name = lib_id.split(":")
    sym = copy.deepcopy(_lib(lib)[name])
    ext = find1(sym, "extends")
    if ext:
        parent = copy.deepcopy(_lib(lib)[ext[1]])
        # keep child's properties, parent's graphics/units renamed
        props = {p[1]: p for p in find(sym, "property")}
        new = [Sym("symbol"), name]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == "property":
                new.append(props.pop(e[1], e))
            elif isinstance(e, list) and e[0] == "symbol":
                e[1] = e[1].replace(ext[1] + "_", name + "_", 1)
                new.append(e)
            else:
                new.append(e)
        for p in props.values():
            new.append(p)
        sym = new
    sym[1] = lib_id
    return sym


def pins(lib_id):
    """{(unit, number): (x, y, angle, name, etype)} ; unit 0 = common."""
    sym = load(lib_id)
    base = lib_id.split(":")[1]
    out = {}
    for sub in find(sym, "symbol"):
        tail = sub[1][len(base) + 1:]
        unit, style = [int(v) for v in tail.split("_")]
        if style not in (0, 1):
            continue
        for p in find(sub, "pin"):
            at = find1(p, "at")
            num = find1(p, "number")[1]
            name = find1(p, "name")[1]
            out[(unit, num)] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, name, str(p[1]))
    return out


def unit_count(lib_id):
    sym = load(lib_id)
    base = lib_id.split(":")[1]
    units = set()
    for sub in find(sym, "symbol"):
        units.add(int(sub[1][len(base) + 1:].split("_")[0]))
    return max(units) if units else 1


if __name__ == "__main__":
    import sys
    for lid in sys.argv[1:]:
        print(lid, unit_count(lid))
        for k, v in sorted(pins(lid).items()):
            print("  ", k, v)
