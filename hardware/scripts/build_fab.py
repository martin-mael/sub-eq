"""Produce fabrication files in hardware/fab/ (bare PCB, everything hand-soldered).

  gerbers/ + sub-eq-gerbers.zip   -> JLCPCB "Gerber file" (bare boards, no assembly)
  bom_mouser_smd.csv                 -> SMD parts, upload to mouser.fr > BOM Tool (matched by manufacturer PN)
  bom_hand_solder.csv                -> through-hole parts
  schematic.pdf, pcb-top.pdf         -> for review / soldering map
  sub-eq-pcb.step                 -> 3D model of the board

Run with plain python3 (uses kicad-cli).
"""
import csv, os, subprocess, zipfile, collections, shutil
from sexp import parse, find, find1

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
FAB = os.path.join(HW, "fab")
CLI = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
PCB = os.path.join(HW, "sub-eq.kicad_pcb")
SCH = os.path.join(HW, "sub-eq.kicad_sch")

R0805, C0805 = "R_0805_2012Metric", "C_0805_2012Metric"
# (value, footprint) -> (manufacturer, manufacturer PN, quantity to buy, description)
# Passives are bought by 10 (cheap; spares for parts lost from the tweezers).
MOUSER_SMD = {
    ("1M", R0805): ("Yageo", "RC0805FR-071ML", 10, "Resistor 1M 1% 0805"),
    ("470", R0805): ("Yageo", "RC0805FR-07470RL", 10, "Resistor 470 1% 0805"),
    ("51k", R0805): ("Yageo", "RC0805FR-0751KL", 10, "Resistor 51k 1% 0805"),
    ("20k", R0805): ("Yageo", "RC0805FR-0720KL", 10, "Resistor 20k 1% 0805"),
    ("100", R0805): ("Yageo", "RC0805FR-07100RL", 10, "Resistor 100 1% 0805"),
    ("100k", R0805): ("Yageo", "RC0805FR-07100KL", 10, "Resistor 100k 1% 0805"),
    ("2k", R0805): ("Yageo", "RC0805FR-072KL", 10, "Resistor 2k 1% 0805"),
    ("10", R0805): ("Yageo", "RC0805FR-0710RL", 10, "Resistor 10 1% 0805"),
    ("4.7k", R0805): ("Yageo", "RC0805FR-074K7L", 10, "Resistor 4.7k 1% 0805"),
    ("2.7k", R0805): ("Yageo", "RC0805FR-072K7L", 10, "Resistor 2.7k 1% 0805"),
    ("200k", R0805): ("Yageo", "RC0805FR-07200KL", 10, "Resistor 200k 1% 0805"),
    ("68k", R0805): ("Yageo", "RC0805FR-0768KL", 10, "Resistor 68k 1% 0805"),
    ("8.2k", R0805): ("Yageo", "RC0805FR-078K2L", 10, "Resistor 8.2k 1% 0805"),
    ("2.2k", R0805): ("Yageo", "RC0805FR-072K2L", 10, "Resistor 2.2k 1% 0805"),
    ("150k", R0805): ("Yageo", "RC0805FR-07150KL", 10, "Resistor 150k 1% 0805"),
    ("2.4k", R0805): ("Yageo", "RC0805FR-072K4L", 10, "Resistor 2.4k 1% 0805"),
    ("47k", R0805): ("Yageo", "RC0805FR-0747KL", 10, "Resistor 47k 1% 0805"),
    ("15k", R0805): ("Yageo", "RC0805FR-0715KL", 10, "Resistor 15k 1% 0805"),
    ("1.5k", R0805): ("Yageo", "RC0805FR-071K5L", 10, "Resistor 1.5k 1% 0805"),
    ("24k", R0805): ("Yageo", "RC0805FR-0724KL", 10, "Resistor 24k 1% 0805"),
    ("3k", R0805): ("Yageo", "RC0805FR-073KL", 10, "Resistor 3k 1% 0805"),
    ("680", R0805): ("Yageo", "RC0805FR-07680RL", 10, "Resistor 680 1% 0805"),
    ("27k", R0805): ("Yageo", "RC0805FR-0727KL", 10, "Resistor 27k 1% 0805"),
    ("12k", R0805): ("Yageo", "RC0805FR-0712KL", 10, "Resistor 12k 1% 0805"),
    ("390", R0805): ("Yageo", "RC0805FR-07390RL", 10, "Resistor 390 1% 0805"),
    ("10k", R0805): ("Yageo", "RC0805FR-0710KL", 10, "Resistor 10k 1% 0805"),
    ("220", R0805): ("Panasonic", "ERJ-6ENF2200V", 10, "Resistor 220 1% 0805 (Yageo out of stock)"),
    ("1n", C0805): ("Yageo", "CC0805JRNPO9BN102", 10, "Cap 1nF 50V 0805 (C0G here; X7R is fine too)"),
    ("100n", C0805): ("Yageo", "CC0805KRX7R9BB104", 20, "Cap 100nF 50V X7R 0805"),
    ("10u 25V", C0805): ("Samsung", "CL21A106KAYNNNG", 10, "Cap 10uF 25V X5R 0805"),
    ("22p C0G", C0805): ("Samsung", "CL21C220JBANNNC", 10, "Cap 22pF 50V C0G 0805"),
    ("100u 35V", "CP_Elec_6.3x7.7"): ("Nichicon", "UWT1V101MCL1GS", 4, "Alu electrolytic 100uF 35V 6.3x7.7"),
    ("TL074", "SOIC-14_3.9x8.7mm_P1.27mm"): ("Texas Instruments", "TL074CDR", 2, "Quad JFET op-amp SOIC-14"),
    ("TL072", "SOIC-8_3.9x4.9mm_P1.27mm"): ("Texas Instruments", "TL072CDR", 1, "Dual JFET op-amp SOIC-8"),
    ("1N5819HW", "D_SOD-123"): ("Diodes Inc.", "1N5819HW-7-F", 2, "Schottky 40 V 1 A SOD-123 (reverse-polarity protection)"),
}

# through-hole and off-board parts: (designators, qty, description, manufacturer part, supplier / supplier number)
HAND_PARTS = [
    ('C2, C3, C101-C502', 14, 'Film capacitor 220 nF 63 V 5 %, 5 mm pitch, 7.2 x 2.5 mm', 'KEMET R82DC3220SH60J', 'Mouser 80-R82DC3220SH60J'),
    ('J1, J2', 2, '6.35 mm mono jack, switched, horizontal PCB, with nut', 'Neutrik NMJ4HCD2', 'Mouser 550-12202'),
    ('J3', 1, 'DC power jack 5.5 x 2.1 mm, horizontal PCB', 'Same Sky (CUI) PJ-102AH', 'Mouser 490-PJ-102AH'),
    ('RV1-RV5', 5, 'Pot 20 kOhm linear, centre detent, 9 mm, horizontal, M9 bushing, D shaft 15 mm', 'Alps Alpine RK09L112003P', 'Mouser 688-RK09L112003P'),
    ('PS1', 1, 'Isolated DC-DC 12 V -> +-12 V 1 W, SIP-7', 'TRACO TMA 1212D', 'Mouser 495-TMA-1212D'),
    ('D2', 1, 'LED 3 mm red, low current (2 mA)', 'Kingbright WP710A10LID', 'Mouser 604-WP710A10LID'),
    ('-', 5, 'Knob for 6 mm D shaft, diameter 11 mm, black ABS', 'Same Sky SPK-016A', 'Mouser 179-SPK-016A'),
]


def run(*args):
    subprocess.run([CLI] + list(args), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def footprints():
    tree = parse(open(PCB).read())
    out = []
    for fp in find(tree, "footprint"):
        lib_id = fp[1]
        props = {p[1]: p[2] for p in find(fp, "property")}
        attr = find1(fp, "attr")
        out.append(dict(ref=props.get("Reference"), value=props.get("Value"), fp=lib_id.split(":")[1],
                        smd=bool(attr and "smd" in [str(a) for a in attr[1:]])))
    return out


def main():
    if os.path.isdir(FAB):
        shutil.rmtree(FAB)
    gdir = os.path.join(FAB, "gerbers")
    os.makedirs(gdir)
    run("pcb", "export", "gerbers", "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
        "--no-protel-ext", "-o", gdir + "/", PCB)
    run("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
        "--map-format", "gerberx2", "-o", gdir + "/", PCB)
    with zipfile.ZipFile(os.path.join(FAB, "sub-eq-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(gdir)):
            z.write(os.path.join(gdir, f), f)

    groups = collections.OrderedDict()
    for p in sorted(footprints(), key=lambda p: p["ref"]):
        if not p["smd"]:
            continue
        groups.setdefault((p["value"], p["fp"]), []).append(p["ref"])
    missing = [k for k in groups if k not in MOUSER_SMD]
    if missing:
        raise SystemExit("no Mouser part for: %s" % missing)
    # merge lines that resolve to the same manufacturer part (e.g. 10u and 10u 25V)
    lines = collections.OrderedDict()
    for key, refs in groups.items():
        mfr, mpn, qty, desc = MOUSER_SMD[key]
        line = lines.setdefault(mpn, dict(mfr=mfr, qty=0, refs=[], desc=desc))
        line["refs"] += refs
        line["qty"] = max(line["qty"], qty)
    with open(os.path.join(FAB, "bom_mouser_smd.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Manufacturer", "Manufacturer Part Number", "Quantity", "Designators", "Qty on board", "Description"])
        for mpn, l in lines.items():
            w.writerow([l["mfr"], mpn, max(l["qty"], len(l["refs"])), " ".join(l["refs"]), len(l["refs"]), l["desc"]])
    with open(os.path.join(FAB, "bom_hand_solder.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Qty", "Description", "Manufacturer Part", "Supplier"])
        for row in HAND_PARTS:
            w.writerow(row)

    run("sch", "export", "pdf", "-o", os.path.join(FAB, "schematic.pdf"), SCH)
    run("pcb", "export", "pdf", "--layers", "F.Cu,F.SilkS,Edge.Cuts", "--mode-single",
        "-o", os.path.join(FAB, "pcb-top.pdf"), PCB)
    run("pcb", "export", "step", "--subst-models", "--force", "-o", os.path.join(FAB, "sub-eq-pcb.step"), PCB)
    print("fab files in", FAB, "| SMD placements:", sum(len(v) for v in groups.values()),
          "| SMD part numbers:", len(lines))


if __name__ == "__main__":
    main()
