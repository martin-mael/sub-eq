"""JLCPCB assembly files -> hardware/jlc/ (optional: SMD parts placed by JLCPCB instead of hand soldering).

  bom_jlc.csv   Comment, Designator, Footprint, JLCPCB Part # (LCSC reference of every line)
  cpl_jlc.csv   Designator, Mid X, Mid Y, Layer, Rotation (top side, SMD only)

Run with plain python3 after the PCB is routed. LCSC references read on jlcpcb.com on 2026-11-10;
"basic" parts carry no extended-part fee.
"""
import collections, csv, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(HW, "jlc")
CLI = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
PCB = os.path.join(HW, "sub-eq.kicad_pcb")

# value -> (LCSC reference, basic?)
LCSC = {
    "1n": ("C46653", True), "22p C0G": ("C1804", True), "100n": ("C49678", True), "10u 25V": ("C15850", True),
    "100u 35V": ("C970686", False), "1N5819HW": ("C8598", True),       # C8598 = B5819W, same SOD-123 Schottky
    "TL074": ("C12594", False), "TL072": ("C6961", True),
    "10": ("C17415", True), "100": ("C17408", True), "220": ("C17557", True), "390": ("C17655", True),
    "470": ("C17710", True), "680": ("C17798", True), "1.5k": ("C4310", True), "2k": ("C17604", True),
    "2.2k": ("C17520", True), "2.4k": ("C17526", True), "2.7k": ("C17530", True), "3k": ("C17661", True),
    "4.7k": ("C17673", True), "8.2k": ("C17828", True), "10k": ("C17414", True), "12k": ("C17444", True),
    "15k": ("C17475", True), "20k": ("C4328", True), "24k": ("C17575", True), "27k": ("C17593", True),
    "47k": ("C17713", True), "51k": ("C17737", True), "68k": ("C17801", True), "100k": ("C149504", True),
    "150k": ("C17470", True), "200k": ("C17539", True), "1M": ("C17514", True),
}


# KiCad footprint (regex) -> degrees added to the KiCad rotation. JLCPCB takes the orientation of the part on
# its reel as 0 degree, KiCad the footprint as drawn: these offsets are the usual ones (JLCKicadTools table).
# They are a starting point: the pin-1 / polarity dots MUST be checked in JLCPCB's placement preview.
ROTATION = [(r"^SOIC-", 270), (r"^SOP-", 270), (r"^SOT-23", 180), (r"^CP_Elec_", 180)]
DNP = [v for v, (ref, _) in LCSC.items() if not ref]        # no LCSC reference: left out of both files


def rotation(pkg, rot):
    import re
    for pattern, corr in ROTATION:
        if re.search(pattern, pkg):
            return (float(rot) + corr) % 360
    return float(rot) % 360


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(tempfile.mkdtemp(), "pos.csv")
    subprocess.run([CLI, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front",
                    "--smd-only", "--exclude-dnp", "-o", raw, PCB],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows = [r for r in csv.DictReader(open(raw)) if r["Val"] not in DNP]
    with open(os.path.join(OUT, "cpl_jlc.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", "Top", "%g" % rotation(r["Package"], r["Rot"])])
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault((r["Val"], r["Package"]), []).append(r["Ref"])
    missing = [v for v, _ in groups if v not in LCSC]
    if missing:
        raise SystemExit("no LCSC part for: %s" % missing)
    with open(os.path.join(OUT, "bom_jlc.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (val, pkg), refs in groups.items():
            w.writerow([val, ",".join(refs), pkg, LCSC[val][0]])
    ext = [v for v, _ in groups if not LCSC[v][1]]
    print("jlc files in", OUT, "| placements:", len(rows), "| BOM lines:", len(groups),
          "| extended:", len(ext), ext)


if __name__ == "__main__":
    main()
