"""Release manifest -> hardware/fab/MANIFEST.txt: revision and SHA-256 of every file sent to a manufacturer.

Run last (after build_fab.py and build_jlc.py): the Gerber zip, the JLCPCB BOM and the placement file listed
here belong to the same design revision; send them together, never mixed with files of another run.
"""
import hashlib, os, subprocess
import circuit

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
FILES = ["%s.kicad_sch" % circuit.PROJECT, "%s.kicad_pcb" % circuit.PROJECT,
         "fab/%s-gerbers.zip" % circuit.PROJECT, "fab/bom_mouser_smd.csv", "fab/bom_hand_solder.csv",
         "fab/schematic.pdf", "fab/pcb-top.pdf", "fab/%s-pcb.step" % circuit.PROJECT,
         "jlc/bom_jlc.csv", "jlc/cpl_jlc.csv"]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    try:
        commit = subprocess.run(["git", "-C", HW, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    lines = ["project   %s" % circuit.PROJECT, "revision  %s" % circuit.REV,
             "built on  commit %s (plus uncommitted changes, if any)" % (commit or "?"), ""]
    for f in FILES:
        p = os.path.join(HW, f)
        lines.append("%s  %s" % (sha(p) if os.path.exists(p) else "MISSING".ljust(64), f))
    out = os.path.join(HW, "fab", "MANIFEST.txt")
    open(out, "w").write("\n".join(lines) + "\n")
    print("wrote", out, "| revision", circuit.REV)


if __name__ == "__main__":
    main()
