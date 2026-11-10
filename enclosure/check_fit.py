"""Interference check: PCB STEP (KiCad 3D models) + envelopes of the parts without a model, vs printed parts."""
import os
from build123d import import_step, Pos
import enclosure as E

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.basename(os.path.dirname(HERE))
pcb = import_step(os.path.join(HERE, "..", "hardware", "fab", PROJECT + "-pcb.step"))
solids = pcb.solids()
board = [s for s in solids if abs(s.bounding_box().size.X - E.PCB_W) < 0.5
         and abs(s.bounding_box().size.Z - E.PCB_T) < 0.2]
bbb = board[0].bounding_box()
dx, dy, dz = 0 - bbb.min.X, 0 - bbb.max.Y, E.Z_PCB_BOT - bbb.min.Z
moved = [("step solid #%d" % i, Pos(dx, dy, dz) * s) for i, s in enumerate(solids)]
print("pcb step: %d solids, top of the tallest part %.2f mm above the board (ceiling at %.2f)" % (
    len(solids), max(s.bounding_box().max.Z for _, s in moved) - E.Z_PCB_TOP, E.TOP_CLEAR))
env = E.envelopes()
print("envelopes (no KiCad 3D model):", ", ".join(n for n, _ in env))
bad = 0
for name, part in E.parts().items():
    pb = part.bounding_box()
    for label, s in moved + env:
        sb = s.bounding_box()
        if (sb.max.X < pb.min.X or sb.min.X > pb.max.X or sb.max.Y < pb.min.Y or sb.min.Y > pb.max.Y
                or sb.max.Z < pb.min.Z or sb.min.Z > pb.max.Z):
            continue
        inter = part & s
        v = inter.volume if inter else 0
        if v > 0.05:
            bad += 1
            c = sb.center()
            print("INTERFERENCE %-12s %-18s at (%.1f, %.1f, %.1f) vol %.2f mm3" % (name, label, c.X, -c.Y, c.Z, v))
# envelopes against each other and against the modelled parts (placement sanity)
for i, (na, a) in enumerate(env):
    for nb, b in env[i + 1:]:
        if na.split()[0] == nb.split()[0] and na.split()[-1] == nb.split()[-1]:
            continue        # body + nose / bushing of the same part
        inter = a & b
        if inter and inter.volume > 0.05:
            bad += 1
            print("INTERFERENCE %s / %s vol %.2f mm3" % (na, nb, inter.volume))
print("interferences:", bad)
