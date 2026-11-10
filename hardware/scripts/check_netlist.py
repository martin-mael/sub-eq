"""Compare a KiCad-exported netlist with circuit.py nets."""
import sys
from sexp import parse, find, find1
import circuit

tree = parse(open(sys.argv[1]).read())
got = {}
for net in find(find1(tree, "nets"), "net"):
    nodes = frozenset((find1(n, "ref")[1], find1(n, "pin")[1]) for n in find(net, "node"))
    got[nodes] = find1(net, "name")[1]
want = {frozenset((r, p) for r, p in conns if not r.startswith("#")): name
        for name, conns in circuit.nets().items()}
ok = True
for nodes, name in want.items():
    if nodes not in got:
        ok = False
        print("MISMATCH", name, sorted(nodes))
for nodes, name in got.items():
    if nodes not in want and len(nodes) > 1:
        ok = False
        print("EXTRA", name, sorted(nodes))
print("NETLIST OK" if ok else "NETLIST DIFFERS")
