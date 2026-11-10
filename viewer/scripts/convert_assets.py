"""Convertit les sources CAO du dépôt en assets pour le viewer web.

    .venv/bin/python viewer/scripts/convert_assets.py      (depuis la racine du projet)
    cd viewer && npm run assets                            (équivalent)

Entrées (lecture seule) :
  enclosure/out/{tray,lid,back_panel,front_panel}.step   pièces imprimées (repère boîtier)
  enclosure/enclosure.py                                 cotes (importé : PCB, hauteurs, trous) et contrôle de dims.ts
  hardware/fab/<projet>-pcb.step                         PCB + modèles 3D KiCad
  hardware/<projet>.kicad_pcb                            couches F.Cu / F.Mask / F.Silkscreen (texture)

Sorties (viewer/public/models/) :
  tray.glb, lid.glb, back_panel.glb, front_panel.glb
  pcb.glb                  PCB recalé dans le repère boîtier (même logique que enclosure/check_fit.py)
  pcb_top_color.png        texture RGBA de la face composants (cuivre, pastilles, sérigraphie)
  pcb_top_rm.png           carte roughness (G) / metalness (B) correspondante
  assets.json              métadonnées (offset PCB, épaisseur, date)

Les GLB sont de vrais glTF : Y en haut, unités en mètres. Le viewer les remet en mm / Z en haut.
Les couleurs par face des modèles STEP KiCad sont conservées (lecture XCAF).
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image
import cairosvg
from pygltflib import GLTF2, Node

from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label as TDF_LabelSequence
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem
from OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString as TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.IFSelect import IFSelect_RetDone
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PROJECT = os.path.basename(ROOT)
OUT = os.path.join(ROOT, "viewer", "public", "models")
ENC = os.path.join(ROOT, "enclosure", "out")
DIMS_TS = os.path.join(ROOT, "viewer", "src", "scene", "dims.ts")
PCB_STEP = os.path.join(ROOT, "hardware", "fab", PROJECT + "-pcb.step")
PCB_FILE = os.path.join(ROOT, "hardware", PROJECT + ".kicad_pcb")
KICAD_CLI = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")

# the enclosure script is the source of truth for every dimension used here
sys.path.insert(0, os.path.join(ROOT, "enclosure"))
import enclosure as E  # noqa: E402

Z_PCB_BOT = E.Z_PCB_BOT
PCB_W, PCB_D = E.PCB_W, E.PCB_D
TEX_PX_PER_MM = 24
MOUNT_HOLES = E.HOLES          # (x, y PCB)


def expected_dims():
    """Values that viewer/src/scene/dims.ts must carry, read from enclosure.py."""
    d = {
        "PCB_W": E.PCB_W, "PCB_D": E.PCB_D, "PCB_T": E.PCB_T,
        "Z_FLOOR": E.Z_FLOOR, "Z_PCB_BOT": E.Z_PCB_BOT, "Z_PCB_TOP": E.Z_PCB_TOP, "Z_CEIL": E.Z_CEIL,
        "Z_SPLIT": E.SPLIT_H, "H_TOTAL": E.H,
        "X0": E.X0, "X1": E.X1, "Y0": E.Y0, "Y1": E.Y1,
        "Y_BACK_IN": E.Y_BACK_IN, "Y_BACK_OUT": E.Y_BACK_OUT, "Y_FRONT_IN": E.Y_FRONT_IN, "Y_FRONT_OUT": E.Y_FRONT_OUT,
        "PANEL_T": E.PANEL_T,
        "HOLES": [list(h) for h in E.HOLES],
        "JACK_IN_X": E.JACKS["IN"], "JACK_OUT_X": E.JACKS["OUT"], "DC_X": E.DC_X, "LED_X": E.LED_X,
        "JACK_H": E.JACK_H, "JACK_BODY": list(E.JACK_BODY), "POT_H": E.POT_H, "POT_BODY": list(E.POT_BODY),
        "DC_BODY": list(E.DC_BODY), "LED_H": E.LED_H, "DCDC_H": E.DCDC_H, "DCDC_BOX": list(E.DCDC_BOX),
    }
    for name in ("POT_X", "FILTER_X", "RES_X", "POT2_DEPTH"):        # project-specific front panel
        if hasattr(E, name):
            v = getattr(E, name)
            d[name] = list(v) if isinstance(v, (list, tuple)) else v
    return d


def check_dims():
    """Fail if dims.ts drifted from enclosure.py (each constant is a one-line literal in dims.ts)."""
    src = open(DIMS_TS, encoding="utf-8").read()
    bad = []
    for name, want in expected_dims().items():
        m = re.search(r"^export const %s(?::[^=]+)? = (.+?)\s*(?://.*)?$" % name, src, re.M)
        if not m:
            bad.append("%s absent" % name)
            continue
        try:
            got = json.loads(m.group(1))
        except ValueError:
            bad.append("%s : littéral illisible (%s)" % (name, m.group(1)))
            continue
        flat_w = np.ravel(np.array(want, dtype=float))
        flat_g = np.ravel(np.array(got, dtype=float))
        if flat_w.shape != flat_g.shape or np.abs(flat_w - flat_g).max() > 1e-6:
            bad.append("%s = %s dans dims.ts, %s dans enclosure.py" % (name, got, want))
    if bad:
        raise SystemExit("dims.ts n'est plus synchronisé avec enclosure/enclosure.py :\n  " + "\n  ".join(bad))
    print("  dims.ts      : %d cotes conformes à enclosure.py" % len(expected_dims()))


def read_step(path):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    r.SetLayerMode(True)
    if r.ReadFile(path) != IFSelect_RetDone or not r.Transfer(doc):
        raise SystemExit("lecture STEP impossible : " + path)
    return doc


def free_shapes(doc):
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = TDF_LabelSequence()
    st.GetFreeShapes(labels)
    return [st.GetShape_s(labels.Value(i + 1)) for i in range(labels.Length())]


def mesh(doc, lin=0.02, ang=0.25):
    for s in free_shapes(doc):
        BRepMesh_IncrementalMesh(s, lin, False, ang, True)


def write_glb(doc, path):
    w = RWGltf_CafWriter(TCollection_AsciiString(path), True)
    cs = w.ChangeCoordinateSystemConverter()
    cs.SetInputLengthUnit(0.001)                                   # mm -> m
    cs.SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
    cs.SetOutputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_glTF)
    w.SetParallel(True)
    w.SetMergeFaces(True)          # une primitive par matériau (moins de draw calls)
    if not w.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange()):
        raise SystemExit("écriture glTF impossible : " + path)


def bbox(shape):
    b = Bnd_Box()
    BRepBndLib.Add_s(shape, b, False)
    lo, hi = b.CornerMin(), b.CornerMax()
    return lo.X(), lo.Y(), lo.Z(), hi.X(), hi.Y(), hi.Z()


def wrap_translate(path, t_zup_mm):
    """Ajoute un noeud racine avec une translation (donnée en mm, repère Z-up) au GLB."""
    g = GLTF2().load_binary(path)
    dx, dy, dz = t_zup_mm
    root = Node(name="pcb_offset", translation=[dx / 1000.0, dz / 1000.0, -dy / 1000.0],
                children=list(g.scenes[g.scene or 0].nodes))
    g.nodes.append(root)
    g.scenes[g.scene or 0].nodes = [len(g.nodes) - 1]
    g.save_binary(path)


def convert_enclosure():
    for name in ("tray", "lid", "back_panel", "front_panel"):
        src = os.path.join(ENC, name + ".step")
        doc = read_step(src)
        mesh(doc, lin=0.015, ang=0.2)
        dst = os.path.join(OUT, name + ".glb")
        write_glb(doc, dst)
        print("  %-12s -> %s (%d ko)" % (name, os.path.relpath(dst, ROOT), os.path.getsize(dst) // 1024))


def convert_pcb():
    doc = read_step(PCB_STEP)
    # carte nue = le solide dont la bbox fait PCB_W x PCB_D x 1.6 (cf. enclosure/check_fit.py)
    board = None
    for s in free_shapes(doc):
        ex = TopExp_Explorer(s, TopAbs_SOLID)
        while ex.More():
            x0, y0, z0, x1, y1, z1 = bbox(ex.Current())
            if abs((x1 - x0) - PCB_W) < 0.5 and abs((y1 - y0) - PCB_D) < 0.5 and abs((z1 - z0) - 1.6) < 0.2:
                board = (x0, y0, z0, x1, y1, z1)
            ex.Next()
    if board is None:
        raise SystemExit("solide carte introuvable dans " + PCB_STEP)
    x0, y0, z0, x1, y1, z1 = board
    off = (0.0 - x0, 0.0 - y1, Z_PCB_BOT - z0)
    mesh(doc, lin=0.01, ang=0.2)
    dst = os.path.join(OUT, "pcb.glb")
    write_glb(doc, dst)
    wrap_translate(dst, off)
    print("  pcb          -> %s (%d ko), offset %s mm, carte %.2f mm" % (
        os.path.relpath(dst, ROOT), os.path.getsize(dst) // 1024, tuple(round(v, 3) for v in off), z1 - z0))
    return off, z1 - z0


def layer_mask(layer, tmp, w, h):
    """Rend une couche KiCad (noir & blanc) -> (encre, trou) en float 0..1."""
    svg = os.path.join(tmp, layer + ".svg")
    subprocess.run([KICAD_CLI, "pcb", "export", "svg", "--mode-single", "--layers", layer, "--black-and-white",
                    "--page-size-mode", "2", "--exclude-drawing-sheet", "--drill-shape-opt", "2",
                    "-o", svg, PCB_FILE], check=True, capture_output=True)
    png = cairosvg.svg2png(url=svg, output_width=w, output_height=h)
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA")).astype(np.float32) / 255.0
    lum = a[..., :3].mean(axis=2)
    ink = a[..., 3] * (1.0 - lum)              # tracé noir
    hole = a[..., 3] * lum                     # perçages dessinés en blanc
    return ink, hole


def pcb_texture():
    if not os.path.exists(KICAD_CLI):
        print("  kicad-cli introuvable : texture PCB non régénérée")
        return
    w, h = int(PCB_W * TEX_PX_PER_MM), int(PCB_D * TEX_PX_PER_MM)
    with tempfile.TemporaryDirectory() as tmp:
        cu, cu_hole = layer_mask("F.Cu", tmp, w, h)
        mk, _ = layer_mask("F.Mask", tmp, w, h)
        sk, _ = layer_mask("F.Silkscreen", tmp, w, h)
    hole = np.clip(cu_hole * 1.5, 0, 1)
    exposed = cu * mk                          # pastilles (HASL)
    covered = cu * (1 - mk)                    # pistes sous vernis
    silk = sk * (1 - mk)
    rgb = np.zeros((h, w, 3), np.float32)
    alpha = np.zeros((h, w), np.float32)

    def paint(m, col):
        nonlocal rgb, alpha
        c = np.array(col, np.float32) / 255.0
        rgb = rgb * (1 - m[..., None]) + c * m[..., None]
        alpha = alpha * (1 - m) + m

    paint(covered, (34, 36, 38))       # cuivre sous vernis noir : léger relief plus clair
    paint(exposed, (200, 201, 198))    # étain-plomb HASL (docs/COMMANDE.md)
    paint(silk, (238, 238, 232))       # sérigraphie blanche
    # trous de fixation M3 (dessinés pleins par KiCad) : on les perce dans la texture
    yy, xx = np.mgrid[0:h, 0:w]
    for hx, hy in MOUNT_HOLES:
        hole = np.maximum(hole, ((xx - hx * TEX_PX_PER_MM) ** 2 + (yy - hy * TEX_PX_PER_MM) ** 2
                                 < (1.65 * TEX_PX_PER_MM) ** 2).astype(np.float32))
    alpha *= (1 - hole)
    img = np.dstack([rgb, alpha])
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "pcb_top_color.png"),
                                                                      optimize=True)
    # roughness (G) / metalness (B)
    rough = 0.55 * np.ones((h, w), np.float32)
    rough = rough * (1 - exposed) + 0.35 * exposed
    rough = rough * (1 - silk) + 0.8 * silk
    metal = exposed
    rm = np.dstack([np.zeros_like(rough), rough, metal])
    Image.fromarray((rm * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT, "pcb_top_rm.png"), optimize=True)
    print("  texture PCB  -> pcb_top_color.png / pcb_top_rm.png (%d x %d px)" % (w, h))


def main():
    os.makedirs(OUT, exist_ok=True)
    t = time.time()
    print("Cotes :")
    check_dims()
    print("Boîtier :")
    convert_enclosure()
    print("PCB :")
    off, thick = convert_pcb()
    pcb_texture()
    meta = {"pcbOffsetMm": off, "boardThicknessStep": round(thick, 3), "generated": time.strftime("%Y-%m-%d %H:%M"),
            "sources": ["enclosure/out/*.step", "enclosure/enclosure.py",
                         "hardware/fab/%s-pcb.step" % PROJECT, "hardware/%s.kicad_pcb" % PROJECT]}
    with open(os.path.join(OUT, "assets.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("terminé en %.1f s" % (time.time() - t))


if __name__ == "__main__":
    sys.exit(main())
