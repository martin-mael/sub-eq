"""Small-signal check of the Sub EQ, with the real component values (ideal op-amps, nodal analysis).

    ../../.venv/bin/python sim_eq.py

Topology (constant-Q graphic EQ, 9 op-amp sections):
  IN -> subsonic Sallen-Key high-pass (unity gain)              -> H
  H  -> A: inverting summer (RIN, RF), "cut" bus = its - input   -> VA
  VA -> INV: inverter (RI, RI)                                   -> VI
  VI -> 5 x multiple-feedback band-pass (gain -1 at f0)          -> X1..X5   (X = +bp * VA)
  VA -> B: inverting summer (RIN, RF), "boost" bus = its - input -> OUT
  each pot: wiper = X, one end -> RS -> cut bus, other end -> RS -> boost bus
  OUT/H = (1 + sum kb.bp) / (1 + sum kc.bp): exactly flat with every pot centred.
"""
import numpy as np

from circuit import RIN, RF, RI, RP, RS, C, BANDS, HP_R1, HP_R2   # the real values


class Net:
    def __init__(self):
        self.idx, self.g, self.opamps, self.src = {}, [], [], None

    def n(self, name):
        return self.idx.setdefault(name, len(self.idx))

    def y(self, a, b, y):                      # admittance between a and b ("0" = ground)
        self.g.append((a, b, y))

    def opamp(self, plus, minus, out):
        self.opamps.append((plus, minus, out))

    def solve(self, f, src="IN"):
        s = 2j * np.pi * f
        for a, b, _ in self.g:
            for k in (a, b):
                if k != "0":
                    self.n(k)
        n = len(self.idx)
        Y = np.zeros((n, n), complex)
        rhs = np.zeros(n, complex)
        for a, b, y in self.g:
            y = y(s) if callable(y) else y
            for p, q in ((a, b), (b, a)):
                if p != "0":
                    Y[self.idx[p], self.idx[p]] += y
                    if q != "0":
                        Y[self.idx[p], self.idx[q]] -= y
        for plus, minus, out in self.opamps:   # the output node's KCL row becomes V+ = V-
            r = self.idx[out]
            Y[r, :] = 0
            if plus != "0":
                Y[r, self.idx[plus]] = 1
            Y[r, self.idx[minus]] -= 1
        r = self.idx[src]
        Y[r, :] = 0
        Y[r, r] = 1
        rhs[r] = 1
        v = np.linalg.solve(Y, rhs)
        return {k: v[i] for k, i in self.idx.items()}


def build(pos, hpf=False):
    """pos[i] in 0..1: 0 = full cut, 0.5 = flat, 1 = full boost."""
    net = Net()
    cap = lambda c: (lambda s: s * c)
    if hpf:
        net.y("IN", "HA", cap(C)); net.y("HA", "HB", cap(C))
        net.y("HA", "H", 1 / HP_R1); net.y("HB", "0", 1 / HP_R2)
        net.opamp("HB", "H", "H")
        src = "H"
    else:
        src = "IN"
    net.y(src, "NA", 1 / RIN); net.y("NA", "VA", 1 / RF); net.opamp("0", "NA", "VA")
    net.y("VA", "NI", 1 / RI); net.y("NI", "VI", 1 / RI); net.opamp("0", "NI", "VI")
    net.y("VA", "NB", 1 / RIN); net.y("NB", "OUT", 1 / RF); net.opamp("0", "NB", "OUT")
    for i, (_, r1, r2, r3) in enumerate(BANDS):
        m, k, x = "M%d" % i, "K%d" % i, "X%d" % i      # MFB: m = input node, k = - input
        net.y("VI", m, 1 / r1); net.y(m, "0", 1 / r2)
        net.y(m, k, cap(C)); net.y(m, x, cap(C)); net.y(k, x, 1 / r3)
        net.opamp("0", k, x)
        p = min(max(pos[i], 0.0), 1.0)
        net.y(x, "NB", 1 / (RS + (1 - p) * RP))        # boost end
        net.y(x, "NA", 1 / (RS + p * RP))              # cut end
    return net


def db(x):
    return 20 * np.log10(abs(x))


def resp(f, pos, hpf=False):
    return build(pos, hpf).solve(f)


def peak(pos):
    fs = np.logspace(np.log10(15), np.log10(200), 1500)
    g = np.array([db(resp(f, pos)["OUT"]) for f in fs])
    k = int(np.argmax(abs(g)))
    w = fs[abs(g) >= abs(g[k]) - 3.0]
    return fs[k], g[k], fs[k] / (w[-1] - w[0])


if __name__ == "__main__":
    nb = len(BANDS)
    flat = [0.5] * nb
    print("all pots centred: %+.4f dB at 50 Hz, %+.4f dB at 1 kHz" % (
        db(resp(50, flat)["OUT"]), db(resp(1000, flat)["OUT"])))
    print("\nfilter cells (design: f0 = 1/(2 pi C sqrt(R3 (R1||R2))), Q = pi f0 C R3, gain = R3/(2 R1)):")
    for lab, r1, r2, r3 in BANDS:
        rp = r1 * r2 / (r1 + r2)
        f0 = 1 / (2 * np.pi * C * np.sqrt(r3 * rp))
        print("  %s Hz: f0 %.1f Hz  Q %.2f  gain %.3f" % (lab, f0, np.pi * f0 * C * r3, r3 / (2 * r1)))
    print("\none band at a time (peak frequency, gain, -3 dB Q):")
    for i, b in enumerate(BANDS):
        up = list(flat); up[i] = 1.0
        dn = list(flat); dn[i] = 0.0
        hf = list(flat); hf[i] = 0.75
        f1, g1, q1 = peak(up)
        f2, g2, _ = peak(dn)
        print("  %s Hz: full boost %5.1f Hz %+6.2f dB (Q %.1f) | full cut %5.1f Hz %+6.2f dB | pot at 75 %%: %+.1f dB"
              % (b[0], f1, g1, q1, f2, g2, peak(hf)[1]))
    print("\n   f     all max  all min  31 max   80 max   +-+-+    with HPF, flat   largest internal node (V per V in, all max)")
    for f in [10, 16, 20, 25, 31.5, 35, 40, 45, 50, 56, 63, 71, 80, 90, 100, 125, 160, 250, 1000]:
        v = resp(f, [1.0] * nb)
        worst = max(abs(v[k]) for k in v if k[0] in "XV")
        print("%6.1f  %+6.2f   %+6.2f   %+6.2f   %+6.2f   %+6.2f   %+6.2f           %.2f" % (
            f, db(v["OUT"]), db(resp(f, [0.0] * nb)["OUT"]),
            db(resp(f, [1, .5, .5, .5, .5])["OUT"]), db(resp(f, [.5, .5, .5, .5, 1])["OUT"]),
            db(resp(f, [1, 0, 1, 0, 1])["OUT"]), db(resp(f, flat, hpf=True)["OUT"]), worst))
    f0 = 1 / (2 * np.pi * C * np.sqrt(HP_R1 * HP_R2))
    print("\nsubsonic HPF: f0 = %.2f Hz, Q = %.3f" % (f0, 0.5 * np.sqrt(HP_R2 / HP_R1)))
