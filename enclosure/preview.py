"""Exploded isometric line drawing of the enclosure + PCB -> out/preview.svg / .png"""
import os
import cairosvg
from build123d import ExportSVG, LineType, Pos, Compound, import_step, Unit
import enclosure as E

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.basename(os.path.dirname(HERE))
pcb = import_step(os.path.join(HERE, "..", "hardware", "fab", PROJECT + "-pcb.step"))
solids = pcb.solids()
bb = [s for s in solids if abs(s.bounding_box().size.X - E.PCB_W) < 0.5
      and abs(s.bounding_box().size.Z - E.PCB_T) < 0.2][0].bounding_box()
lift = 22
pcb_m = Compound(children=[Pos(-bb.min.X, -bb.max.Y, E.Z_PCB_BOT - bb.min.Z + lift) * s for s in solids]
                 + [Pos(0, 0, lift) * s for _, s in E.envelopes()])   # envelopes: parts without a 3D model

scene = Compound(children=[
    E.tray(),
    pcb_m,
    Pos(0, 0, 2.6 * lift) * E.lid(),
    Pos(0, 28, lift) * E.back_panel(),
    Pos(0, -28, lift) * E.front_panel(),
])
view = (-220, -260, 200)
visible, hidden = scene.project_to_viewport(view, viewport_up=(0, 0, 1))
mx = max(*[abs(v) for v in Compound(children=visible).bounding_box().size])
svg = ExportSVG(unit=Unit.MM, scale=200 / mx, line_weight=0.1)
svg.add_layer("visible", line_weight=0.12)
svg.add_layer("hidden", line_color=(190, 190, 190), line_type=LineType.ISO_DOT, line_weight=0.05)
svg.add_shape(hidden, layer="hidden")
svg.add_shape(visible, layer="visible")
out = os.path.join(HERE, "out", "preview.svg")
svg.write(out)
cairosvg.svg2png(url=out, write_to=out[:-3] + "png", output_width=1600, background_color="white")
print("wrote", out)
