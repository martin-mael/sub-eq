"""Autoroute sub-eq.kicad_pcb with Freerouting, then add GND planes and fill zones.

Run with KiCad's bundled Python:
  FREEROUTING_JAR=/path/to/freerouting-2.5.0.jar JAVA=/opt/homebrew/opt/openjdk/bin/java \
  ~/Applications/KiCad/.../python3 route_pcb.py
"""
import os, subprocess, tempfile
import sys
import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pcb  # noqa: E402  (ORG)

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, "..", "sub-eq.kicad_pcb"))
JAR = os.environ["FREEROUTING_JAR"]
JAVA = os.environ.get("JAVA", "java")


def mm(v):
    return pcbnew.FromMM(v)


def add_zone(board, net, layer, priority=0, poly=None):
    bb = board.GetBoardEdgesBoundingBox()
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD pads solid, THT pads with reliefs
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    if poly is None:
        pts = ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()),
               (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom()))
    else:   # board mm coordinates -> internal units
        pts = [(mm(gen_pcb.ORG[0] + x), mm(gen_pcb.ORG[1] + y)) for x, y in poly]
    for x, y in pts:
        o.Append(int(x), int(y))
    board.Add(z)
    return z


ISOLATED_NETS = ("/VJ", "/VIN", "/GNDPWR")     # adapter side of the isolated DC-DC converter
ISOLATION_MM = 2.0


def add_isolation_keepout(board):
    """Rule area (no zone fill) around every pad and track of the adapter-side nets, on both layers:
    the audio ground pour stays ISOLATION_MM away from them."""
    xs, ys = [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() in ISOLATED_NETS:
                bb = pad.GetBoundingBox()
                xs += [bb.GetLeft(), bb.GetRight()]
                ys += [bb.GetTop(), bb.GetBottom()]
    for t in board.GetTracks():
        if t.GetNetname() in ISOLATED_NETS:
            bb = t.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        return
    m = mm(ISOLATION_MM)
    edge = board.GetBoardEdgesBoundingBox()
    x0, x1 = max(min(xs) - m, edge.GetLeft()), min(max(xs) + m, edge.GetRight())
    y0, y1 = max(min(ys) - m, edge.GetTop()), min(max(ys) + m, edge.GetBottom())
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    for name in ("SetDoNotAllowZoneFills", "SetDoNotAllowCopperPour"):      # API name changed across KiCad versions
        if hasattr(z, name):
            getattr(z, name)(True)
            break
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetZoneName("isolation GND / GNDPWR")
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(int(x), int(y))
    board.Add(z)


def remove_dangling_vias(board):
    """Drop router vias that only connect tracks on one layer (or none): KiCad flags them as dangling."""
    layers_at = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            for p in (t.GetStart(), t.GetEnd()):
                layers_at.setdefault((round(p.x / 1000.0), round(p.y / 1000.0)), set()).add(t.GetLayer())
    n = 0
    for v in [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        p = v.GetPosition()
        if len(layers_at.get((round(p.x / 1000.0), round(p.y / 1000.0)), ())) < 2:
            board.Delete(v)
            n += 1
    return n


def _holes(board):
    out = [(v.GetPosition(), v.GetDrill()) for v in board.Tracks() if v.GetClass() == "PCB_VIA"]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetDrillSize().x > 0:
                out.append((pad.GetPosition(), max(pad.GetDrillSize().x, pad.GetDrillSize().y)))
    return out


def _free(pt, holes, drill):
    for hp, hd in holes:
        if (hp.x - pt.x) ** 2 + (hp.y - pt.y) ** 2 < (hd / 2 + drill / 2 + mm(0.5)) ** 2:
            return False
    return True


def stitch(board, net, step):
    """Vias wherever both copper layers are filled with `net`: a regular grid, plus at least one via in
    every top-layer island the grid missed (ties F.Cu islands to the B.Cu plane)."""
    zones = [z for z in board.Zones() if z.GetNetname() == net]
    fills = {}
    for z in zones:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(layer):
                poly = z.GetFilledPolysList(layer).CloneDropTriangulation()
                fills.setdefault(layer, pcbnew.SHAPE_POLY_SET()).BooleanAdd(poly)
    if pcbnew.F_Cu not in fills or pcbnew.B_Cu not in fills:
        return 0
    both = fills[pcbnew.F_Cu].CloneDropTriangulation()
    both.BooleanIntersection(fills[pcbnew.B_Cu])
    both.Deflate(mm(0.45), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.01))
    netinfo = board.FindNet(net)
    holes = _holes(board)
    placed = []

    def add(x, y):
        pt = pcbnew.VECTOR2I(int(x), int(y))
        if not both.Contains(pt) or not _free(pt, holes, mm(0.3)):
            return False
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt)
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(netinfo)
        board.Add(v)
        holes.append((pt, mm(0.3)))
        placed.append(pt)
        return True

    bb = board.GetBoardEdgesBoundingBox()
    y = bb.GetTop() + mm(1.5)
    while y < bb.GetBottom():
        x = bb.GetLeft() + mm(1.5)
        while x < bb.GetRight():
            add(x, y)
            x += mm(step)
        y += mm(step)
    # islands of the top-layer fill without a via yet
    top = fills[pcbnew.F_Cu]
    for i in range(top.OutlineCount()):
        isl = pcbnew.SHAPE_POLY_SET()
        isl.AddOutline(top.Outline(i))
        if any(isl.Contains(p) for p in placed):
            continue
        ib = isl.BBox()
        done = False
        yy = ib.GetTop()
        while yy < ib.GetBottom() and not done:
            xx = ib.GetLeft()
            while xx < ib.GetRight() and not done:
                if isl.Contains(pcbnew.VECTOR2I(int(xx), int(yy))):
                    done = add(xx, yy)
                xx += mm(0.25)
            yy += mm(0.25)
    return len(placed)


def main():
    board = pcbnew.LoadBoard(PCB)
    # start from a clean slate: drop previous tracks / vias / zones
    for t in list(board.GetTracks()):
        if not t.IsLocked():          # keep the hand-placed (locked) stubs from gen_pcb.py
            board.Remove(t)
    for z in list(board.Zones()):
        board.Remove(z)

    work = tempfile.mkdtemp()
    dsn, ses = os.path.join(work, "board.dsn"), os.path.join(work, "board.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    subprocess.run([JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-mp", "120", "-l", "en"],
                   check=True, timeout=1800)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("SES import failed")

    pcbnew.SaveBoard(PCB, board)
    # post-processing in a fresh interpreter: the SWIG track list is unusable after the SES import
    subprocess.run([sys.executable, os.path.abspath(__file__), "--post"], check=True)


def post():
    board = pcbnew.LoadBoard(PCB)
    # Freerouting necks tracks down to 0.125 mm near fine-pitch pads: bring them back to >= 0.15 mm
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < mm(0.15):
            t.SetWidth(mm(0.15))
    print("dangling vias removed:", remove_dangling_vias(board))

    add_isolation_keepout(board)
    add_zone(board, "/GND", pcbnew.B_Cu)
    add_zone(board, "/GND", pcbnew.F_Cu)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    n = stitch(board, "/GND", step=4.0)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("stitching vias added:", n)
    pcbnew.SaveBoard(PCB, board)
    print("routed and saved", PCB)


if __name__ == "__main__":
    post() if "--post" in sys.argv else main()
