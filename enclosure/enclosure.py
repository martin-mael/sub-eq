"""Sub EQ enclosure (build123d). Outputs STEP + STL for the 4 printed parts.

    cd enclosure && ../.venv/bin/python enclosure.py

Construction (same as audio-box)
  tray (bottom) + lid (top) form a U-channel each; the front and back panels are flat plates that
  slide into grooves of both. Four M3x14 countersunk screws go up through the tray standoffs,
  through the PCB mounting holes and into heat-set inserts in the lid columns.
  The inside is lined with conductive-adhesive copper tape wired to the SHIELD pad (TP1).

Coordinates: X = PCB x, Y = -PCB y (back panel at Y > 0, front panel at Y < -PCB_D), Z up from the
bottom face of the tray. All connector positions are taken from hardware/scripts/gen_pcb.py
(keep both files in sync).
"""
import os
from build123d import (Box, Cylinder, Cone, Pos, Rot, Plane, Text, Align, FontStyle,
                       extrude, export_step, export_stl, Compound)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# ------------------------------------------------------------------ PCB / connector data (mm)
PCB_W, PCB_D, PCB_T = 90.0, 62.0, 1.6
HOLES = [(4.0, 4.0), (86.0, 4.0), (3.8, 45.5), (86.2, 45.5)]      # PCB x, y
POT_X = [15.0, 30.0, 45.0, 60.0, 75.0]
POT_LABELS = ["31", "40", "50", "63", "80"]
JACKS = {"IN": 19.0, "OUT": 40.0}                                  # back panel, PCB x
DC_X = 57.5
LED_X = 86.0
DCDC_BOX = (65.5, 71.8, 2.8, 22.5)                                 # TMA 1212D body on the PCB: x0, x1, y0, y1

# ------------------------------------------------------------------ part dimensions (manufacturer drawings)
JACK_H, JACK_HOLE = 3.53, 11.8      # Neutrik NMJ4HCD2: axis above the PCB; panel cut-out 11.4 + FDM margin
JACK_BODY = (18.2, 23.53, 11.67)    # width, depth behind the panel, height above the PCB
POT_H, POT_HOLE = 3.5, 9.5          # Alps RK09L: axis above the PCB; M9 x 0.75 bushing + FDM margin
POT_BODY = (12.1, 7.45, 8.35)       # width over the lugs, depth behind the bushing shoulder, top above the PCB
POT_LUG_R = 6.0                     # anti-rotation lug: 2 x 0.8 mm, 6 mm from the axis
DC_BODY = (9.0, 14.4, 11.0)         # CUI PJ-102AH: width, depth, height. Front face flush with the panel outside
LED_H = 6.0
DCDC_H = 10.2

PANEL_GAP = 0.3            # panel inner face to PCB edge
WALL, FLOOR, ROOF = 3.0, 3.0, 3.0
SIDE_CLEAR = 0.5           # PCB edge to side wall
STANDOFF = 4.5             # PCB bottom above the floor (DC jack pins stick out 3.5 mm below the board)
TOP_CLEAR = 13.0           # PCB top to ceiling (jack body reaches 11.67)
PANEL_T, GROOVE_D, GROOVE_W = 2.5, 1.5, 2.75
REVEAL = 1.5               # tray/lid overhang in front of the panels
SPLIT_H = 13.0             # tray/lid parting line height (Z)
LIP_H, LIP_T = 2.0, 1.2    # alignment lip on the tray walls

Z_FLOOR = FLOOR
Z_PCB_BOT = Z_FLOOR + STANDOFF
Z_PCB_TOP = Z_PCB_BOT + PCB_T
Z_CEIL = Z_PCB_TOP + TOP_CLEAR
H = Z_CEIL + ROOF

X_IN0, X_IN1 = -SIDE_CLEAR, PCB_W + SIDE_CLEAR
X0, X1 = X_IN0 - WALL, X_IN1 + WALL
Y_BACK_IN = PANEL_GAP                       # back panel inner face (Y)
Y_BACK_OUT = Y_BACK_IN + PANEL_T
Y_FRONT_IN = -(PCB_D + PANEL_GAP)
Y_FRONT_OUT = Y_FRONT_IN - PANEL_T
Y0, Y1 = Y_FRONT_OUT - REVEAL, Y_BACK_OUT + REVEAL
LABEL_Z_LOW, LABEL_Z_HIGH = Z_FLOOR + 1.9, Z_CEIL - 1.6


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def ycyl(x, y, z, d, length):
    """Cylinder along Y centred at (x, y, z)."""
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(d / 2, length)


def groove_cut(y_in, outward):
    """Panel groove: floor/ceiling + both side walls, centred on the panel thickness."""
    yc = y_in + outward * PANEL_T / 2
    return box(X_IN0 - GROOVE_D, X_IN1 + GROOVE_D, yc - GROOVE_W / 2, yc + GROOVE_W / 2,
               Z_FLOOR - GROOVE_D, Z_CEIL + GROOVE_D)


GROOVES = groove_cut(Y_BACK_IN, +1) + groove_cut(Y_FRONT_IN, -1)


def tray():
    t = box(X0, X1, Y0, Y1, 0, SPLIT_H) - box(X_IN0, X_IN1, Y0 - 1, Y1 + 1, Z_FLOOR, SPLIT_H + 1)
    for xa, xb in ((X_IN0 - LIP_T, X_IN0), (X_IN1, X_IN1 + LIP_T)):      # alignment lips
        t += box(xa, xb, Y_FRONT_IN, Y_BACK_IN, SPLIT_H, SPLIT_H + LIP_H)
    t -= GROOVES
    for hx, hy in HOLES:
        t += Pos(hx, -hy, Z_FLOOR + STANDOFF / 2) * Cylinder(4.0, STANDOFF)
        t -= Pos(hx, -hy, H / 2) * Cylinder(1.7, H + 2)                       # M3 clearance
        t -= Pos(hx, -hy, 0.9) * Cone(3.4, 1.7, 1.8 + 0.01)                    # countersink (ISO 10642)
    for fx, fy in ((X0 + 9, Y0 + 9), (X1 - 9, Y0 + 9), (X0 + 9, Y1 - 9), (X1 - 9, Y1 - 9)):
        t -= Pos(fx, fy, 0.25) * Cylinder(5.5, 0.5)                            # recess for a dia 10 rubber foot
    return t


def lid():
    l = box(X0, X1, Y0, Y1, SPLIT_H, H) - box(X_IN0, X_IN1, Y0 - 1, Y1 + 1, SPLIT_H - 1, Z_CEIL)
    for xa, xb in ((X_IN0 - LIP_T - 0.2, X_IN0), (X_IN1, X_IN1 + LIP_T + 0.2)):   # room for the tray lips
        l -= box(xa, xb, Y_FRONT_IN - 0.2, Y_BACK_IN + 0.2, SPLIT_H - 1, SPLIT_H + LIP_H + 0.3)
    l -= GROOVES
    for hx, hy in HOLES:
        col_h = Z_CEIL - Z_PCB_TOP
        l += Pos(hx, -hy, Z_PCB_TOP + col_h / 2) * Cylinder(4.0, col_h)
        l -= Pos(hx, -hy, Z_PCB_TOP + 3.0) * Cylinder(2.0, 6.0)               # heat-set insert M3 x 5.7
    return l


def panel_blank(y_in, outward):
    yo = y_in + outward * PANEL_T
    c = 0.15
    return box(X_IN0 - GROOVE_D + c, X_IN1 + GROOVE_D - c, min(y_in, yo), max(y_in, yo),
               Z_FLOOR - GROOVE_D + c, Z_CEIL + GROOVE_D - c)


def engrave(face_y, outward, x, z, msg, size=2.6, depth=0.6):
    """Engraved text on a panel outer face, readable from outside."""
    pl = Plane(origin=(x, face_y, z), x_dir=(-outward, 0, 0), z_dir=(0, outward, 0))
    t = Text(msg, font_size=size, font="Arial", font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
    return extrude(pl * t, amount=-depth)


def back_panel():
    p = panel_blank(Y_BACK_IN, +1)
    yc = (Y_BACK_IN + Y_BACK_OUT) / 2
    for name, x in JACKS.items():
        p -= ycyl(x, yc, Z_PCB_TOP + JACK_H, JACK_HOLE, 10)
        p -= engrave(Y_BACK_OUT, +1, x, LABEL_Z_HIGH, name, size=2.4)
    w, _, h = DC_BODY           # the DC jack body goes through the panel
    p -= box(DC_X - w / 2 - 0.3, DC_X + w / 2 + 0.3, Y_BACK_IN - 1, Y_BACK_OUT + 1,
             Z_PCB_TOP - 0.2, Z_PCB_TOP + h + 0.3)
    p -= engrave(Y_BACK_OUT, +1, DC_X, Z_FLOOR + 3.0, "12V DC", size=2.4)
    return p


def pot_hole(p, x):
    z = Z_PCB_TOP + POT_H
    yc = (Y_FRONT_IN + Y_FRONT_OUT) / 2
    p -= ycyl(x, yc, z, POT_HOLE, 10)
    for dx, dz in ((POT_LUG_R, 0), (-POT_LUG_R, 0), (0, POT_LUG_R), (0, -POT_LUG_R)):
        # pockets for the anti-rotation lug (2 x 0.8 mm), whichever side it is on
        hw, hh = (0.7, 1.4) if dz == 0 else (1.4, 0.7)
        p -= box(x + dx - hw, x + dx + hw, Y_FRONT_IN - 1.1, Y_FRONT_IN + 0.1, z + dz - hh, z + dz + hh)
    return p


def front_panel():
    p = panel_blank(Y_FRONT_IN, -1)
    yc = (Y_FRONT_IN + Y_FRONT_OUT) / 2
    for x, label in zip(POT_X, POT_LABELS):
        p = pot_hole(p, x)
        p -= engrave(Y_FRONT_OUT, -1, x, LABEL_Z_HIGH, label, size=2.4)
    p -= ycyl(LED_X, yc, Z_PCB_TOP + LED_H, 3.2, 10)
    p -= engrave(Y_FRONT_OUT, -1, (POT_X[0] + POT_X[-1]) / 2, LABEL_Z_LOW, "SUB EQ   Hz   -12 . 0 . +12 dB", size=2.2)
    return p


def envelopes():
    """Keep-out solids of the parts that have no KiCad 3D model (name, solid), enclosure coordinates."""
    out = []
    zt = Z_PCB_TOP
    w, d, h = JACK_BODY
    for name, x in JACKS.items():
        out.append(("jack " + name, box(x - w / 2, x + w / 2, Y_BACK_IN - d, Y_BACK_IN, zt, zt + h)))
        out.append(("jack nose " + name, ycyl(x, Y_BACK_IN + 2.9, zt + JACK_H, 11.0, 5.8)))
    w, d, h = POT_BODY
    for i, x in enumerate(POT_X):
        out.append(("pot %d" % (i + 1), box(x - w / 2, x + w / 2, Y_FRONT_IN, Y_FRONT_IN + d, zt, zt + h)))
        out.append(("pot bushing %d" % (i + 1), ycyl(x, Y_FRONT_IN - 2.5, zt + POT_H, 9.0, 5.0)))
    w, d, h = DC_BODY
    out.append(("dc jack", box(DC_X - w / 2, DC_X + w / 2, Y_BACK_OUT - d, Y_BACK_OUT, zt, zt + h)))
    x0, x1, y0, y1 = DCDC_BOX
    out.append(("dc-dc", box(x0, x1, -y1, -y0, zt, zt + DCDC_H)))
    return out


def parts():
    return {"tray": tray(), "lid": lid(), "back_panel": back_panel(), "front_panel": front_panel()}


def main():
    os.makedirs(OUT, exist_ok=True)
    ps = parts()
    for name, solid in ps.items():
        export_step(solid, os.path.join(OUT, name + ".step"))
        export_stl(solid, os.path.join(OUT, name + ".stl"), tolerance=0.02, angular_tolerance=0.1)
        bb = solid.bounding_box()
        print("%-12s %6.1f x %5.1f x %5.1f mm  vol %6.1f cm3" % (name, bb.size.X, bb.size.Y, bb.size.Z,
                                                                  solid.volume / 1000))
    export_step(Compound(children=list(ps.values())), os.path.join(OUT, "assembly.step"))
    print("exterior: %.1f x %.1f x %.1f mm (W x D x H)" % (X1 - X0, Y1 - Y0, H))


if __name__ == "__main__":
    main()
