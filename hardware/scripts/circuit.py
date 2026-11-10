"""
Single source of truth for the Sub EQ circuit (spec: docs/SPEC.md).

gen_schematic.py (KiCad schematic), gen_pcb.py (KiCad PCB) and sim_eq.py (response check)
all read this file, so they always share the same parts, nets and values.

Signal flow (mono, constant-Q graphic EQ, 9 op-amp sections):

  J1 IN -> 470R / 1n (RF filter) -> U1A: subsonic Sallen-Key high-pass, 20 Hz, Butterworth  = H
  H  -> U1B: inverting summer A (20k / 20k). Its - input is the CUT bus (NA)                = VA
  VA -> U1C: inverter (20k / 20k)                                                           = VI
  VI -> 5 x multiple-feedback band-pass, gain -1 at f0, Q 4.3 (U2A..D, U3A)                 = X1..X5
  VA -> U1D: inverting summer B (20k / 20k). Its - input is the BOOST bus (NB)              = VB
  each pot RVn (20k lin, centre detent): wiper = Xn, pin 3 (CW) -> 2k -> NB, pin 1 (CCW) -> 2k -> NA
  VB -> 100R -> 47u -> J2 OUT

  OUT/H = (1 + sum kb.bp) / (1 + sum kc.bp): exactly flat with every pot centred.

Power: J3 12 V DC (centre +) -> Schottky -> TRACO TMA 1212D (isolated, unregulated +-12 V, 42 mA)
       -> 10R + 100u per rail -> +12V / -12V.
The audio ground (GND) is isolated from the adapter ground (GNDPWR).

Python 3.9 compatible, no third-party import (KiCad's bundled interpreter runs gen_pcb.py).
"""

PROJECT = "sub-eq"
TITLE = "Sub EQ - 5-band graphic EQ for subwoofers (31 / 40 / 50 / 63 / 80 Hz)"
PAPER = "A3"

# ---------------------------------------------------------------- values (ohms, farads)
RIN = RF = 20e3          # summers A and B
RI = 20e3                # inverter
RP = 20e3                # pots: Alps RK09L112003P, 20k linear, centre detent
RS = 2.0e3               # pot end resistors: +-12.4 dB per band
C = 220e-9               # every filter capacitor (film, 5 %)
# Every resistor value below is a JLCPCB "Basic" 0805 1 % part (no extended-part fee when the board is assembled).
# band: (label, R1 input, R2 to ground, R3 feedback), each one a list of values wired in series.
#   f0 = 1/(2 pi C sqrt(R3 (R1||R2))), Q = pi f0 C R3, gain = R3/(2 R1)
BAND_PARTS = [
    ("31", [100e3], [2.7e3], [200e3]),
    ("40", [68e3, 8.2e3], [2.2e3], [150e3, 2.4e3]),
    ("50", [47e3, 15e3], [1.5e3, 220.0], [100e3, 24e3]),
    ("63", [47e3, 3e3], [680.0, 680.0], [100e3]),
    ("80", [27e3, 12e3], [680.0, 390.0], [68e3, 10e3]),
]
BANDS = [(label, sum(r1), sum(r2), sum(r3)) for label, r1, r2, r3 in BAND_PARTS]     # totals, for sim_eq.py
HP_R1, HP_R2 = 25.5e3, 51e3        # subsonic HPF: R1 to the op-amp output (2 x 51k in parallel), R2 to ground


def fmt(v):
    """196e3 -> '196k', 2740 -> '2.74k', 470 -> '470'."""
    for div, suf in ((1e6, "M"), (1e3, "k")):
        if v >= div:
            return ("%g" % (v / div)) + suf
    return "%g" % v


# ---------------------------------------------------------------- footprints
FP = {
    "R": "Resistor_SMD:R_0805_2012Metric",
    "C": "Capacitor_SMD:C_0805_2012Metric",
    "CFILM": "Capacitor_THT:C_Rect_L7.2mm_W2.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2",
    "CP_100u": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "SOIC8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "SOIC14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "SOD123": "Diode_SMD:D_SOD-123",
    "LED": "LED_THT:LED_D3.0mm_Horizontal_O1.27mm_Z6.0mm",
    "JACK": "Connector_Audio:Jack_6.35mm_Neutrik_NMJ4HCD2_Horizontal",
    "DCJACK": "Connector_BarrelJack:BarrelJack_CUI_PJ-102AH_Horizontal",
    "POT": "Potentiometer_THT:Potentiometer_Alps_RK09L_Single_Horizontal",
    "DCDC": "Converter_DCDC:Converter_DCDC_TRACO_TMA-05xxD_12xxD_Dual_THT",
    "PAD": "TestPoint:TestPoint_THTPad_D2.5mm_Drill1.2mm",
    "HOLE": "MountingHole:MountingHole_3.2mm_M3",
}

# ---------------------------------------------------------------- parts
PARTS = []


def part(ref, lib_id, value, fp, pins, at, unit=None, **kw):
    p = dict(ref=ref, lib_id=lib_id, value=value, fp=FP.get(fp, fp), pins=pins, at=at, unit=unit)
    p.update(kw)
    PARTS.append(p)
    return p


R = "Device:R"
CAP = "Device:C"
CP = "Device:C_Polarized"
QUAD = "Amplifier_Operational:TL074"     # units 1-4 = amplifiers, unit 5 = supply (4 = V+, 11 = V-)
DUAL = "Amplifier_Operational:TL072"     # units 1-2 = amplifiers, unit 3 = supply (8 = V+, 4 = V-)
JACK = "Connector_Audio:AudioJack2_SwitchT"
QPINS = {1: ("3", "2", "1"), 2: ("5", "6", "7"), 3: ("10", "9", "8"), 4: ("12", "13", "14")}   # (+, -, out)


class Row:
    """Left-to-right slots on the schematic sheet (everything on the 1.27 mm grid)."""
    def __init__(self, row, col=0):
        self.y = 35.56 + 22.86 * row
        self.col = col

    def at(self, slots=1):
        x = 25.4 + 15.24 * self.col + 7.62 * (slots - 1)
        self.col += slots
        return (x, self.y)


def res(ref, ohms, a, b, at):
    part(ref, R, fmt(ohms), "R", {"1": a, "2": b}, at)


def opamp(ref, lib, value, fp, unit, plus, minus, out, at):
    p, m, o = QPINS[unit]
    part(ref, lib, value, fp, {p: plus, m: minus, o: out}, at, unit=unit)


# --- input, subsonic high-pass, summers, inverter, output
r = Row(0)
part("J1", JACK, "IN 6.35", "JACK", {"T": "IN", "TN": "GND", "S": "GND"}, r.at(2), role="in",
     note="TN to GND: the input is grounded when nothing is plugged in")
res("R1", 1e6, "IN", "GND", r.at())
res("R2", 470, "IN", "INF", r.at())
part("C1", CAP, "1n", "C", {"1": "INF", "2": "GND"}, r.at())
part("C2", CAP, "220n film", "CFILM", {"1": "INF", "2": "HA"}, r.at())
part("C3", CAP, "220n film", "CFILM", {"1": "HA", "2": "HB"}, r.at())
res("R3", 2 * HP_R1, "HA", "H", r.at())
res("R16", 2 * HP_R1, "HA", "H", r.at())      # in parallel with R3: 25.5k
res("R4", HP_R2, "HB", "GND", r.at())
opamp("U1", QUAD, "TL074", "SOIC14", 1, "HB", "H", "H", r.at(2))
res("R5", RIN, "H", "NA", r.at())
res("R6", RF, "NA", "VA", r.at())
part("C4", CAP, "22p C0G", "C", {"1": "NA", "2": "VA"}, r.at())
opamp("U1", QUAD, "TL074", "SOIC14", 2, "GND", "NA", "VA", r.at(2))

r = Row(1)
res("R7", RI, "VA", "NI", r.at())
res("R8", RI, "NI", "VI", r.at())
opamp("U1", QUAD, "TL074", "SOIC14", 3, "GND", "NI", "VI", r.at(2))
res("R9", RIN, "VA", "NB", r.at())
res("R10", RF, "NB", "VB", r.at())
part("C5", CAP, "22p C0G", "C", {"1": "NB", "2": "VB"}, r.at())
opamp("U1", QUAD, "TL074", "SOIC14", 4, "GND", "NB", "VB", r.at(2))
res("R11", 100, "VB", "OUTC", r.at())
part("C6", CP, "100u 35V", "CP_100u", {"1": "OUTC", "2": "OUT"}, r.at())
res("R12", 100e3, "OUT", "GND", r.at())
part("J2", JACK, "OUT 6.35", "JACK", {"T": "OUT", "S": "GND"}, r.at(2), role="out")

# --- the five bands
def chain(refs, values, a, b, mid, r):
    """Resistors in series from net a to net b (refs / intermediate net used only when there are two)."""
    if len(values) == 1:
        res(refs[0], values[0], a, b, r.at())
    else:
        res(refs[0], values[0], a, mid, r.at())
        res(refs[1], values[1], mid, b, r.at())


for i, (label, r1, r2, r3) in enumerate(BAND_PARTS):
    n = (i + 1) * 100
    k = str(i + 1)
    m, kn, x = "M" + k, "K" + k, "X" + k
    r = Row(2 + i)
    chain(("R%d" % (n + 1), "R%d" % (n + 6)), r1, "VI", m, "MA" + k, r)
    chain(("R%d" % (n + 2), "R%d" % (n + 7)), r2, m, "GND", "MB" + k, r)
    part("C%d" % (n + 1), CAP, "220n film", "CFILM", {"1": m, "2": kn}, r.at())
    part("C%d" % (n + 2), CAP, "220n film", "CFILM", {"1": m, "2": x}, r.at())
    chain(("R%d" % (n + 3), "R%d" % (n + 8)), r3, kn, x, "MC" + k, r)
    if i < 4:
        opamp("U2", QUAD, "TL074", "SOIC14", i + 1, "GND", kn, x, r.at(2))
    else:
        opamp("U3", DUAL, "TL072", "SOIC8", 1, "GND", kn, x, r.at(2))
    # pot: pin 1 = CCW end, 2 = wiper, 3 = CW end. Clockwise = boost.
    part("RV" + k, "sub-eq:Pot_MP", "20k lin detent", "POT",
         {"1": "PC" + k, "2": x, "3": "PB" + k, "MP": "GND"}, r.at(2), role="pot" + k, note=label + " Hz")
    res("R%d" % (n + 4), RS, "PB" + k, "NB", r.at())
    res("R%d" % (n + 5), RS, "PC" + k, "NA", r.at())
# spare half of U3: follower on ground
part("U3", DUAL, "TL072", "SOIC8", {"5": "GND", "6": "SPARE", "7": "SPARE"}, Row(6, 16).at(2), unit=2)

# --- power
r = Row(7)
part("J3", "Connector:Barrel_Jack_Switch", "12V DC 5.5/2.1", "DCJACK",
     {"1": "VJ", "2": "GNDPWR", "3": "GNDPWR"}, r.at(2), role="dc", note="centre pin = +12 V")
part("D1", "Device:D_Schottky", "1N5819HW", "SOD123", {"2": "VJ", "1": "VIN"}, r.at(),
     note="reverse-polarity protection")
part("C7", CAP, "10u 25V", "C", {"1": "VIN", "2": "GNDPWR"}, r.at())
part("PS1", "sub-eq:TMA_Dual", "TMA 1212D", "DCDC",
     {"1": "VIN", "2": "GNDPWR", "6": "P12R", "5": "GND", "4": "N12R"}, r.at(3), role="dcdc")
part("C8", CAP, "10u 25V", "C", {"1": "P12R", "2": "GND"}, r.at())
part("C9", CAP, "10u 25V", "C", {"1": "GND", "2": "N12R"}, r.at())
res("R13", 10, "P12R", "+12V", r.at())
res("R14", 10, "N12R", "-12V", r.at())
part("C10", CP, "100u 35V", "CP_100u", {"1": "+12V", "2": "GND"}, r.at())
part("C11", CP, "100u 35V", "CP_100u", {"1": "GND", "2": "-12V"}, r.at())
res("R15", 4.7e3, "+12V", "LED_A", r.at())
part("D2", "Device:LED", "LED 3mm", "LED", {"2": "LED_A", "1": "GND"}, r.at(), role="led")
part("TP1", "Connector:TestPoint", "SHIELD", "PAD", {"1": "GND"}, r.at(), role="shield",
     note="wire to the copper tape lining the enclosure")

# --- op-amp supplies + 100 nF decoupling, power flags, mounting holes
r = Row(8)
for i, (u, lib, fp, unit, vp, vn) in enumerate((("U1", QUAD, "SOIC14", 5, "4", "11"),
                                                ("U2", QUAD, "SOIC14", 5, "4", "11"),
                                                ("U3", DUAL, "SOIC8", 3, "8", "4"))):
    part(u, lib, None, fp, {vp: "+12V", vn: "-12V"}, r.at(), unit=unit)
    part("C%d" % (12 + 2 * i), CAP, "100n", "C", {"1": "+12V", "2": "GND"}, r.at())
    part("C%d" % (13 + 2 * i), CAP, "100n", "C", {"1": "GND", "2": "-12V"}, r.at())
for i, net in enumerate(("+12V", "-12V", "GND")):
    part("#FLG0%d" % (i + 1), "power:PWR_FLAG", "PWR_FLAG", None, {"1": net}, r.at())
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M3", "HOLE", {}, r.at(), role="hole")

NOTES = [   # (text, schematic row)
    ("INPUT -> 20 Hz SUBSONIC HIGH-PASS (U1A) -> CUT SUMMER A (U1B)", 0),
    ("INVERTER (U1C) -> BAND-PASS CELLS ; BOOST SUMMER B (U1D) -> OUTPUT", 1),
    ("BANDS 31 / 40 / 50 / 63 / 80 Hz: MFB band-pass (gain -1, Q 4.3, JLCPCB Basic values in series) + 20k detent pot, CW = boost", 2),
    ("POWER: 12 V DC -> 1N5819HW -> TMA 1212D (isolated) -> 10R + 100u -> +-12 V. GND is isolated from GNDPWR.", 7),
]


def merged():
    """{ref: {lib_id, value, fp, pins, units, role}} with multi-unit parts merged."""
    out = {}
    for p in PARTS:
        q = out.setdefault(p["ref"], dict(ref=p["ref"], lib_id=p["lib_id"], value=p["value"], fp=p["fp"],
                                          pins={}, units=[], role=p.get("role"), note=p.get("note", "")))
        if p["value"] is not None:
            q["value"] = p["value"]
        if p.get("role"):
            q["role"] = p["role"]
        q["pins"].update(p["pins"])
        q["units"].append(p)
    return out


def nets():
    n = {}
    for ref, p in merged().items():
        for pin, net in p["pins"].items():
            n.setdefault(net, []).append((ref, pin))
    return n


if __name__ == "__main__":
    for net, conns in sorted(nets().items()):
        print("%-10s %s" % (net, " ".join("%s.%s" % c for c in conns)))
