"""Generate hardware/sub-eq.kicad_pcb from circuit.py (placement, nets, outline, rules).

Run with KiCad's bundled Python:
  ~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 gen_pcb.py

Board coordinates (mm): origin = back-left corner seen from above, +X to the right,
+Y towards the FRONT panel. The back edge (y = 0) carries the jacks and the DC socket,
the front edge (y = DEPTH) the pots and the LED.
"""
import os, sys, uuid, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import circuit  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, "..", "sub-eq.kicad_pcb"))
FPDIR = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
PRJLIB = os.path.normpath(os.path.join(HERE, "..", "sub-eq.pretty"))

WIDTH, DEPTH = 90.0, 62.0
ORG = (50.0, 50.0)            # page offset
PANEL_GAP = 0.3               # panel inner face sits this far beyond the board edge
PANEL_T = 2.5                 # printed panel thickness (same as enclosure.py)

NS = uuid.UUID("6f1c2b1e-6f0e-4f4c-9b1a-2a7d3c0a5e11")


def uid(*k):
    return str(uuid.uuid5(NS, "/".join(str(x) for x in k)))


# ------------------------------------------------------------------ panel connectors
# anchor = axis point on the connector's reference face (footprint coordinates), dir = direction from the
# body towards the panel, gap = distance from the panel inner face back to that face (negative = the face
# goes into / through the panel)
CONNECTOR_GEOM = {
    # Neutrik NMJ4HCD2 (drawing ST-NMJ4HCD2): panel rear face 16.7 mm from the T / TN pins, axis midway (16.23 / 2)
    "JACK": dict(anchor=(16.7, 8.115), dir=(1, 0)),
    # Alps RK09L1120 (catalogue p.324, style 1): bushing shoulder 5 mm in front of the pins, axis on pin 2
    "POT": dict(anchor=(-5.0, 2.5), dir=(-1, 0)),
    # CUI PJ-102AH: body 14.4 long, front face flush with the panel outer face (the plug seats fully)
    "DCJACK": dict(anchor=(0.0, 13.7), dir=(0, 1), gap=-PANEL_T),
    "LED": dict(anchor=(1.27, 3.0), dir=(0, 1)),
}

W = WIDTH
POT_X = [15.0, 30.0, 45.0, 60.0, 75.0]      # 31 / 40 / 50 / 63 / 80 Hz, left to right seen from the front
# role -> (footprint key, panel, axis x on the board)
PANEL_PARTS = {
    # back panel. Seen from behind, left to right: 12V DC, OUT, IN
    "in": ("JACK", "back", 19.0),
    "out": ("JACK", "back", 40.0),
    "dc": ("DCJACK", "back", 57.5),
    # front panel
    "led": ("LED", "front", 86.0),
}
for _i, _x in enumerate(POT_X):
    PANEL_PARTS["pot%d" % (_i + 1)] = ("POT", "front", _x)
FULL_PADS = ("pot",)          # roles (prefix) whose pads connect solidly to the ground pour
POWER_NETS = ("GND", "GNDPWR", "+12V", "-12V", "P12R", "N12R", "VIN", "VJ")
TEXTS = [("SUB EQ r1", 52.0, 26.0, 1.2), ("31", 15.0, 52.0, 1.0), ("40", 30.0, 52.0, 1.0),
         ("50", 45.0, 52.0, 1.0), ("63", 60.0, 52.0, 1.0), ("80", 75.0, 52.0, 1.0),
         ("SHIELD", 86.0, 33.5, 0.8)]

PLACE = {
    # mounting holes (lid columns clamp the PCB here)
    "H1": (4.0, 4.0, 0), "H2": (86.0, 4.0, 0), "H3": (3.8, 45.5, 0), "H4": (86.2, 45.5, 0),
    # input network, left of the IN jack
    "R1": (2.5, 11.5, 90), "R2": (5.3, 11.5, 90), "C1": (2.5, 16.0, 90),
    # subsonic high-pass
    "C2": (1.8, 26.5, 0), "C3": (1.8, 30.5, 0), "R3": (2.5, 35.5, 90), "R4": (5.3, 35.5, 90), "R16": (8.1, 35.5, 90),
    # U1: high-pass buffer, summers A / B, inverter
    "U1": (17.0, 31.8, 90), "C12": (10.5, 31.8, 90), "C13": (23.3, 31.8, 90),
    "R5": (10.5, 26.0, 90), "R6": (13.3, 26.0, 90), "C4": (16.1, 26.0, 90), "R7": (18.9, 26.0, 90),
    "R8": (21.7, 26.0, 90),
    "R9": (10.5, 37.6, 90), "R10": (13.3, 37.6, 90), "C5": (16.1, 37.6, 90), "R11": (18.9, 37.6, 90),
    "R12": (21.7, 37.6, 90),
    "C6": (29.5, 29.0, 0),
    # U2: band-pass cells 1-4, U3: cell 5 (+ spare)
    "U2": (41.0, 31.8, 90), "C14": (35.0, 31.8, 90), "C15": (47.0, 31.8, 90),
    "U3": (75.0, 31.8, 90), "C16": (70.0, 31.8, 90), "C17": (80.0, 31.8, 90),
    # power: behind the DC jack and in the back-right corner
    "D1": (57.5, 15.5, 0), "C7": (57.5, 19.0, 0),
    "PS1": (70.5, 5.0, 0),
    "C8": (75.2, 19.5, 90), "R13": (78.0, 19.5, 90), "C9": (75.2, 11.5, 90), "R14": (78.0, 11.5, 90),
    "C10": (84.5, 19.5, 0), "C11": (84.5, 11.5, 180),
    "R15": (86.2, 51.5, 90), "TP1": (86.0, 30.0, 0),
}
for _i, _x in enumerate(POT_X):     # one cell per band, behind its pot (refs n06 / n07 / n08 only exist for series pairs)
    _n = (_i + 1) * 100
    PLACE.update({
        "C%d" % (_n + 1): (_x - 5.4, 41.3, 0), "C%d" % (_n + 2): (_x - 5.4, 45.0, 0),
        # right of the capacitors, stacked: R1a, R1b, R2a
        "R%d" % (_n + 1): (_x + 4.6, 40.9, 0), "R%d" % (_n + 6): (_x + 4.6, 43.0, 0),
        "R%d" % (_n + 2): (_x + 4.6, 45.1, 0),
        # front row: cut resistor, R2b, R3a, R3b, boost resistor
        "R%d" % (_n + 5): (_x - 5.6, 48.6, 90), "R%d" % (_n + 7): (_x - 2.8, 48.6, 90),
        "R%d" % (_n + 3): (_x, 48.6, 90), "R%d" % (_n + 8): (_x + 2.8, 48.6, 90),
        "R%d" % (_n + 4): (_x + 5.6, 48.6, 90),
    })


def rot(v, deg):
    t = math.radians(deg)
    x, y = v
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))


def panel_place(key, panel, ax):
    g = CONNECTOR_GEOM[key]
    want = (0, -1) if panel == "back" else (0, 1)
    for deg in (0, 90, 180, 270):
        d = rot(g["dir"], deg)
        if abs(d[0] - want[0]) < 1e-6 and abs(d[1] - want[1]) < 1e-6:
            break
    else:
        raise ValueError(key)
    extra = g.get("gap", 0.0)   # connector face set back behind the panel inner face
    py = -PANEL_GAP + extra if panel == "back" else DEPTH + PANEL_GAP - extra
    a = rot(g["anchor"], deg)
    return ax - a[0], py - a[1], deg


def mm(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(mm(ORG[0] + x), mm(ORG[1] + y))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = PRJLIB if lib == circuit.PROJECT else os.path.join(FPDIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def setup_rules(board):
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ns = ds.m_NetSettings
    ns.ClearNetclassPatternAssignments()   # the .kicad_pro keeps old assignments between runs
    dflt = ns.GetDefaultNetclass()
    dflt.SetClearance(mm(0.2))
    dflt.SetTrackWidth(mm(0.25))
    dflt.SetViaDiameter(mm(0.6))
    dflt.SetViaDrill(mm(0.3))
    pw = pcbnew.NETCLASS("Power")
    pw.SetClearance(mm(0.25))
    pw.SetTrackWidth(mm(0.6))
    pw.SetViaDiameter(mm(0.8))
    pw.SetViaDrill(mm(0.4))
    ns.SetNetclass("Power", pw)
    for net in POWER_NETS:
        ns.SetNetclassPatternAssignment("/" + net, "Power")
    ds.m_MinClearance = mm(0.15)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_CopperEdgeClearance = mm(0.25)


def outline(board):
    r = 1.5
    pts = [(0, 0), (WIDTH, 0), (WIDTH, DEPTH), (0, DEPTH)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x1, y1))
        s.SetEnd(V(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)


def text(board, msg, x, y, layer=pcbnew.F_SilkS, size=1.2):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(msg)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.18))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def schematic_netlist():
    """Export the schematic netlist with kicad-cli; return {(ref, pin): net name}."""
    import subprocess, tempfile
    from sexp import parse, find, find1
    cli = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
    sch = os.path.join(os.path.dirname(OUT), "sub-eq.kicad_sch")
    tmp = os.path.join(tempfile.mkdtemp(), "sub-eq.net")
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", tmp, sch],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tree = parse(open(tmp).read())
    out = {}
    for net in find(find1(tree, "nets"), "net"):
        name = find1(net, "name")[1]
        for n in find(net, "node"):
            out[(find1(n, "ref")[1], find1(n, "pin")[1])] = name
    return out


def main():
    board = pcbnew.NewBoard(OUT)
    setup_rules(board)
    outline(board)

    pin_net = schematic_netlist()
    nets = {}
    for name in sorted(set(pin_net.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    by_role = {}
    for ref, p in circuit.merged().items():
        if ref.startswith("#") or not p["fp"]:
            continue
        fpkey = [k for k, v in circuit.FP.items() if v == p["fp"]][0]
        fp = load_fp(p["fp"])
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        u1 = min(u["unit"] or 1 for u in p["units"])
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("sym", ref, u1)))
        role = p.get("role")
        if role in PANEL_PARTS:
            key, panel, ax = PANEL_PARTS[role]
            x, y, deg = panel_place(key, panel, ax)
        elif ref in PLACE:
            x, y, deg = PLACE[ref]
        else:
            raise SystemExit("no placement for " + ref)
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(deg)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() == pcbnew.Edge_Cuts:
                fp.Remove(item)
        board.Add(fp)
        if role and role.startswith(FULL_PADS):   # thin pins: solid connection to the ground plane
            for pad in fp.Pads():
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        for pad in fp.Pads():
            net = pin_net.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
            elif pad.GetNumber() in p["pins"]:
                raise SystemExit("pad %s.%s missing from netlist" % (ref, pad.GetNumber()))
        by_role[ref] = fp

    for msg, x, y, size in TEXTS:   # silkscreen hints (inside, for assembly)
        text(board, msg, x, y, size=size)

    pcbnew.SaveBoard(OUT, board)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
