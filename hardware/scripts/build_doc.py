"""Project sheet for someone who has not followed the project -> docs/sub-eq-fiche.pdf (+ docs/BOM.md, docs/img/).

    ../../.venv/bin/python build_doc.py        (after build.sh: needs the routed PCB, fab/ and jlc/)

Everything is computed from the project data: circuit.py (values), sim_eq.py (curves), jlc/bom_jlc.csv,
build_jlc.LCSC (basic / extended), the tables below (prices read on 2026-11-10).
"""
import csv, html, os, subprocess, tempfile
import numpy as np
import circuit, sim_eq, build_jlc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(ROOT, "docs")
IMG = os.path.join(DOCS, "img")
CLI = os.path.expanduser("~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UNITS = 2                                   # the order this sheet is costed for

INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]      # validated categorical order (5 slots)

# through-hole parts, hand soldered: (refs, description, part, qty per board, unit price EUR excl. VAT, stock)
THT = [
    ("RV1–RV5", "Potentiomètre 20 kΩ linéaire, cran central, 9 mm, canon M9", "Alps RK09L112003P", 5, 2.46, "761"),
    ("J1, J2", "Embase jack 6,35 mm mono, coudée", "Neutrik NMJ4HCD2", 2, 1.92, "8 133"),
    ("PS1", "Convertisseur DC-DC isolé 12 V → ±12 V, 1 W", "Traco TMA 1212D", 1, 4.80, "379"),
    ("C2, C3, C101–C502", "Condensateur film 220 nF 63 V 5 %, pas 5 mm", "KEMET R82DC3220SH60J", 12, 0.158, "1 657"),
    ("J3", "Prise DC 5,5 / 2,1 mm, coudée", "Same Sky PJ-102AH", 1, 0.662, "32 489"),
    ("D2", "LED 3 mm rouge", "Kingbright WP710A10LID", 1, 0.232, "21 676"),
    ("—", "Bouton Ø 11 mm pour axe en D de 6 mm", "Same Sky SPK-016A", 5, 0.252, "2 487"),
]
THT_SPARES = {"KEMET R82DC3220SH60J": 2}    # extra pieces on the whole order
MECA = [   # (description, qty per box, note)
    ("Boîtier imprimé 3D : fond, couvercle, 2 panneaux (PETG, ≈ 60 g)", 1, "fichiers STL fournis"),
    ("Vis M3 × 14 tête fraisée", 4, ""),
    ("Insert fileté à chaud M3 × 5,7", 4, ""),
    ("Patin adhésif Ø 10 mm", 4, ""),
    ("Ruban de cuivre à adhésif conducteur (blindage)", 1, "un rouleau pour les deux"),
    ("Bloc secteur 12 V DC régulé, ≥ 300 mA, fiche 5,5 / 2,1 mm, + au centre", 1, ""),
]
# JLCPCB quote read on 2026-11-10 for 5 PCB / 2 assembled (EUR excl. VAT, excl. shipping)
JLC_QUOTE = [("PCB (5 exemplaires)", 3.56), ("Mise en route", 7.33), ("Pochoir", 1.38), ("Composants", 2.36),
             ("Frais de pièces étendues (2)", 5.50), ("Pose et refusion", 1.28)]
EST = dict(jlc_ship=9.0, jlc_customs=2.0, psu=9.0, tape=8.0, screws=3.0, filament=3.0)   # estimates, EUR incl. VAT


def fr(x, nd=2):
    return ("%.*f" % (nd, x)).replace(".", ",")


def val_fr(v):
    """'2.7k' -> '2,7 kΩ', '680' -> '680 Ω', '100n' -> '100 nF', '10u 25V' -> '10 µF 25 V'."""
    t = v.split()[0]
    if t[-1] in "kM" and t[:-1].replace(".", "").isdigit():
        return t[:-1].replace(".", ",") + " " + t[-1] + "Ω"
    if t.replace(".", "").isdigit():
        return t.replace(".", ",") + " Ω"
    if t[-1] in "pnu" and t[:-1].replace(".", "").isdigit():
        return t[:-1].replace(".", ",") + " " + {"p": "pF", "n": "nF", "u": "µF"}[t[-1]]
    return v


def designation(val, pkg):
    if pkg.startswith("R_0805"):
        return "Résistance 0805, 1 %"
    if pkg.startswith("C_0805"):
        return {"22p C0G": "Céramique 0805, C0G 50 V", "10u 25V": "Céramique 0805, X5R 25 V"}.get(
            val, "Céramique 0805, X7R 50 V")
    if pkg.startswith("CP_"):
        return "Électrolytique CMS 35 V, Ø 6,3 × 7,7 mm"
    if pkg.startswith("D_SOD"):
        return "Schottky 40 V 1 A, SOD-123 (B5819W)"
    return {"TL074": "Quadruple ampli-op JFET, SOIC-14", "TL072": "Double ampli-op JFET, SOIC-8"}.get(val, val)


def smd_lines():
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "hardware", "jlc", "bom_jlc.csv"))):
        refs = r["Designator"].split(",")
        out.append(dict(val=r["Comment"], refs=refs, pkg=r["Footprint"], lcsc=r["JLCPCB Part #"],
                        basic=build_jlc.LCSC[r["Comment"]][1]))
    return out


# ------------------------------------------------------------------ charts (static SVG, print)
_CLIP = [0]


def chart(series, title, w=720, h=300, ymin=-18, ymax=20, legend=True, end_labels=False):
    """series: [(label, color, [(f, dB)], peak_label_or_None)]"""
    ml, mr, mt, mb = 46, 150 if end_labels else 16, 34 if legend else 12, 34
    pw, ph = w - ml - mr, h - mt - mb
    f0, f1 = 10.0, 1000.0
    X = lambda f: ml + pw * (np.log10(f / f0) / np.log10(f1 / f0))
    Y = lambda d: mt + ph * (ymax - d) / (ymax - ymin)
    _CLIP[0] += 1
    clip = "plot%d" % _CLIP[0]
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (w, h, html.escape(title))]
    s.append('<rect width="%d" height="%d" fill="%s"/>' % (w, h, SURFACE))
    s.append('<defs><clipPath id="%s"><rect x="%d" y="%d" width="%d" height="%d"/></clipPath></defs>' % (clip, ml, mt, pw, ph))
    for d in range(-30, 31, 6 if ymax - ymin > 20 else 3):
        if ymin <= d <= ymax:
            s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="%s"/>' % (
                ml, Y(d), ml + pw, Y(d), "#b9b8b2" if d == 0 else GRID, 1))
            s.append('<text x="%d" y="%.1f" text-anchor="end" font-size="10" fill="%s">%+d</text>' % (ml - 6, Y(d) + 3.5, INK2, d) if d else
                     '<text x="%d" y="%.1f" text-anchor="end" font-size="10" fill="%s">0</text>' % (ml - 6, Y(d) + 3.5, INK2))
    for f in (10, 20, 31.5, 40, 50, 63, 80, 125, 250, 500, 1000):
        s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>' % (X(f), mt, X(f), mt + ph, GRID))
        s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="10" fill="%s">%s</text>' % (
            X(f), mt + ph + 14, INK2, ("%g" % f).replace(".", ",") if f < 1000 else "1 k"))
    s.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="10" fill="%s">Fréquence (Hz)</text>' % (ml + pw / 2, h - 4, INK2))
    s.append('<text x="12" y="%.1f" text-anchor="middle" font-size="10" fill="%s" transform="rotate(-90 12 %.1f)">Gain (dB)</text>' % (
        mt + ph / 2, INK2, mt + ph / 2))
    for label, color, pts, peak in series:
        d = " ".join("%s%.1f,%.1f" % ("M" if i == 0 else "L", X(f), Y(g)) for i, (f, g) in enumerate(pts))
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" clip-path="url(#%s)"/>' % (d, color, clip))
    for label, color, pts, peak in series:
        if peak:
            f, g = max(pts, key=lambda p: p[1])
            s.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="10" font-weight="600" fill="%s">%s</text>' % (
                X(f), Y(g) - 6, INK, html.escape(peak)))
        if end_labels:
            f, g = pts[-1]
            s.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="%s" stroke-width="2"/>' % (X(f), Y(g), color, SURFACE))
    if end_labels:      # labels at the right end, spread so they never collide
        ends = sorted(((Y(pts[-1][1]), label) for label, _, pts, _ in series))
        y_prev = -99
        for y, label in ends:
            y = max(y, y_prev + 13)
            s.append('<text x="%.1f" y="%.1f" font-size="10" fill="%s">%s</text>' % (ml + pw + 10, y + 3.5, INK, html.escape(label)))
            y_prev = y
    if legend:
        x = ml
        for label, color, _, _ in series:
            s.append('<line x1="%.1f" y1="14" x2="%.1f" y2="14" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (x, x + 16, color))
            s.append('<text x="%.1f" y="17.5" font-size="10" fill="%s">%s</text>' % (x + 22, INK, html.escape(label)))
            x += 34 + 6.2 * len(label)
    s.append("</svg>")
    return "\n".join(s)


def curves():
    fs = np.logspace(1, 3, 260)
    nb = len(circuit.BANDS)
    db = lambda pos: [(f, sim_eq.db(sim_eq.resp(f, pos, hpf=True)["OUT"])) for f in fs]
    one = []
    for i, b in enumerate(circuit.BANDS):
        up = [0.5] * nb; up[i] = 1.0
        dn = [0.5] * nb; dn[i] = 0.0
        one.append((b[0] + " Hz", SERIES[i], db(up), b[0]))
        one.append((None, SERIES[i], db(dn), None))
    c1 = chart_named(one, "Une bande à la fois, au maximum puis au minimum")
    c2 = chart([("Toutes au maximum", SERIES[0], db([1.0] * nb), None),
                ("Potentiomètres au centre", INK2, db([0.5] * nb), None),
                ("Toutes au minimum", SERIES[1], db([0.0] * nb), None)],
               "Toutes les bandes ensemble", h=205, legend=False, end_labels=True, ymin=-24, ymax=20)
    c3 = chart([(name.split(" : ")[0], SERIES[i], db(pos), None) for i, (name, pos) in enumerate(EXAMPLES)]
               + [("Potentiomètres au centre", INK2, db([0.5] * nb), None)],
               "Exemples de réglages courants", h=225, ymin=-9, ymax=9, legend=True)
    return c1, c2, c3


# typical settings: pot positions, 0.5 = centre detent, 0 / 1 = end stops (31, 40, 50, 63, 80 Hz)
EXAMPLES = [
    ("A : renfort de l'extrême grave", [0.75, 0.65, 0.5, 0.5, 0.5]),
    ("B : résonance de salle atténuée vers 50 Hz", [0.5, 0.5, 0.2, 0.4, 0.5]),
    ("C : réglage mixte", [0.7, 0.4, 0.3, 0.6, 0.65]),
]


def chart_named(series, title):
    named = [s for s in series if s[0]]
    svg = chart(named + [("", c, p, None) for (l, c, p, k) in series if not l], title, h=262, legend=False)
    # legend row for the named series only
    x, parts = 46, []
    for label, color, _, _ in named:
        parts.append('<line x1="%.1f" y1="14" x2="%.1f" y2="14" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (x, x + 16, color))
        parts.append('<text x="%.1f" y="17.5" font-size="10" fill="%s">%s</text>' % (x + 22, INK, html.escape(label)))
        x += 34 + 6.2 * len(label)
    return svg.replace("</svg>", "\n".join(parts) + "</svg>").replace('viewBox="0 0 720 262"', 'viewBox="0 2 720 260"')


# ------------------------------------------------------------------ block diagram
def block_diagram():
    W, H = 780, 372
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="Schéma fonctionnel">' % (W, H),
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker></defs>' % INK]

    def box(x, y, w, h, l1, l2="", fill="#f4f4f1"):
        s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="5" fill="%s" stroke="%s" stroke-width="1.2"/>' % (x, y, w, h, fill, INK))
        if l2:
            s.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="11" font-weight="600" fill="%s">%s</text>' % (x + w / 2, y + h / 2 - 2, INK, l1))
            s.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="9.5" fill="%s">%s</text>' % (x + w / 2, y + h / 2 + 11, INK2, l2))
        else:
            s.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="11" font-weight="600" fill="%s">%s</text>' % (x + w / 2, y + h / 2 + 4, INK, l1))

    def wire(pts, arrow=True, label=None, lx=0, ly=0):
        d = " ".join("%s%d,%d" % ("M" if i == 0 else "L", x, y) for i, (x, y) in enumerate(pts))
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.4"%s/>' % (d, INK, ' marker-end="url(#a)"' if arrow else ""))
        if label:
            s.append('<text x="%d" y="%d" font-size="10" fill="%s">%s</text>' % (lx, ly, INK2, label))

    y, h = 40, 46
    box(8, y, 54, h, "IN", "jack 6,35")
    box(84, y, 92, h, "Filtre RF", "470 Ω · 1 nF")
    box(198, y, 104, h, "Subsonique", "20 Hz · 12 dB/oct")
    box(324, y, 66, h, "Σ coupe")
    box(546, y, 66, h, "Σ boost")
    box(634, y, 84, h, "Sortie", "100 Ω · 100 µF")
    box(736, y, 40, h, "OUT")
    yc = y + h // 2
    for a, b in ((62, 84), (176, 198), (302, 324), (390, 546), (612, 634), (718, 736)):
        wire([(a, yc), (b, yc)])
    s.append('<circle cx="430" cy="%d" r="3" fill="%s"/>' % (yc, INK))
    y2 = 170
    box(390, y2, 80, h, "Inverseur")
    box(214, y2, 140, h, "5 passe-bande", "31 · 40 · 50 · 63 · 80 Hz, Q 4,3")
    box(36, y2, 142, h, "5 potentiomètres", "20 kΩ lin., cran central")
    y2c = y2 + h // 2
    wire([(430, yc), (430, y2)])
    wire([(390, y2c), (354, y2c)])
    wire([(214, y2c), (178, y2c)])
    wire([(107, y2), (107, 128), (357, 128), (357, y + h)], label="vers la gauche : coupe", lx=116, ly=122)
    wire([(107, y2 + h), (107, 250), (579, 250), (579, y + h)], label="vers la droite : boost", lx=116, ly=264)
    s.append('<text x="8" y="20" font-size="10.5" fill="%s">Signal</text>' % INK2)
    y3 = 306
    s.append('<text x="8" y="%d" font-size="10.5" fill="%s">Alimentation</text>' % (y3 - 12, INK2))
    box(8, y3, 78, h, "12 V DC", "+ au centre")
    box(110, y3, 92, h, "Schottky", "anti-inversion")
    box(226, y3, 148, h, "DC-DC isolé 1 W", "Traco TMA 1212D")
    box(398, y3, 122, h, "Filtres", "10 Ω · 100 µF par rail")
    box(544, y3, 136, h, "±12 V", "3 amplis-op, LED")
    for a, b in ((86, 110), (202, 226), (374, 398), (520, 544)):
        wire([(a, y3 + h // 2), (b, y3 + h // 2)])
    s.append("</svg>")
    return "\n".join(s)


# ------------------------------------------------------------------ assets
def render_pcb():
    out = os.path.join(IMG, "pcb.png")
    subprocess.run([CLI, "pcb", "render", "--side", "top", "--width", "2000", "--height", "1400", "--quality", "high",
                    "--background", "transparent", "--zoom", "1", "-o", out,
                    os.path.join(ROOT, "hardware", "sub-eq.kicad_pcb")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def costs():
    jlc = sum(v for _, v in JLC_QUOTE)
    tht = sum(q * UNITS * p for _, _, _, q, p, _ in THT) + sum(
        n * p for _, _, part, _, p, _ in THT for k, n in THT_SPARES.items() if k == part)
    rows = [
        ("JLCPCB : 5 PCB, CMS posés sur %d cartes" % UNITS, jlc, jlc * 1.2, "devis relevé"),
        ("JLCPCB : port standard et dédouanement", None, EST["jlc_ship"] * 1.2 + EST["jlc_customs"], "estimé"),
        ("Mouser : composants traversants (port non compté)", tht, tht * 1.2, "prix relevés"),
        ("%d blocs secteur 12 V" % UNITS, None, EST["psu"] * UNITS, "estimé"),
        ("Ruban de cuivre, vis, inserts, patins, filament", None, EST["tape"] + EST["screws"] + EST["filament"], "estimé"),
    ]
    return rows, sum(r[2] for r in rows)


# ------------------------------------------------------------------ BOM (markdown)
def write_bom_md(smd):
    rows, total = costs()
    L = ["# Nomenclature du Sub EQ", "",
         "Générée par `hardware/scripts/build_doc.py`. Quantités **par carte** ; prix et stocks relevés le 2026-11-10.", "",
         "## CMS posés par JLCPCB (%d lignes, %d composants par carte)" % (len(smd), sum(len(l["refs"]) for l in smd)), "",
         "Fichiers : `hardware/jlc/bom_jlc.csv` et `cpl_jlc.csv`. Pour les souder à la main : `hardware/fab/bom_mouser_smd.csv`.", "",
         "| Valeur | Désignation | Qté | Repères | Réf. LCSC | Catalogue JLCPCB |", "|---|---|---|---|---|---|"]
    for l in smd:
        L.append("| %s | %s | %d | %s | %s | %s |" % (val_fr(l["val"]), designation(l["val"], l["pkg"]), len(l["refs"]),
                                                      ", ".join(l["refs"]), l["lcsc"], "de base" if l["basic"] else "étendu"))
    L += ["", "## Traversants, soudés à la main (Mouser)", "",
          "| Repères | Pièce | Référence | Qté | € HT pièce | Stock |", "|---|---|---|---|---|---|"]
    for refs, desc, part, q, p, stock in THT:
        L.append("| %s | %s | %s | %d | %s | %s |" % (refs, desc, part, q, fr(p, 3 if p < 1 else 2), stock))
    L += ["", "## Mécanique (par boîte)", "", "| Pièce | Qté | Remarque |", "|---|---|---|"]
    for desc, q, note in MECA:
        L.append("| %s | %d | %s |" % (desc, q, note))
    L += ["", "## Coût pour %d unités" % UNITS, "", "| Poste | € HT | € TTC | Source |", "|---|---|---|---|"]
    for name, ht, ttc, src in rows:
        L.append("| %s | %s | ≈ %s | %s |" % (name, fr(ht) if ht else "—", fr(ttc, 0), src))
    L.append("| **Total** | | **≈ %s €**, soit ≈ %s € par boîte | |" % (fr(total, 0), fr(total / UNITS, 0)))
    open(os.path.join(DOCS, "BOM.md"), "w").write("\n".join(L) + "\n")


# ------------------------------------------------------------------ HTML -> PDF
CSS = """
@page { size: A4; margin: 15mm 15mm 14mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #0b0b0b; font-size: 9.6pt; line-height: 1.38; margin: 0; }
h1 { font-size: 24pt; margin: 0 0 1mm; letter-spacing: -0.3pt; }
h2 { font-size: 13pt; margin: 0 0 3mm; padding-bottom: 1.5mm; border-bottom: 1px solid #0b0b0b; }
h3 { font-size: 10pt; margin: 5mm 0 1.5mm; }
p { margin: 0 0 2.5mm; }
.sub { font-size: 11pt; color: #52514e; margin-bottom: 5mm; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; }
th { text-align: left; font-weight: 600; border-bottom: 1px solid #0b0b0b; padding: 1.2mm 1.5mm; }
td { border-bottom: 1px solid #e4e3df; padding: 1.1mm 1.5mm; vertical-align: top; }
td.n, th.n { text-align: right; white-space: nowrap; }
table.kv td:first-child { width: 34mm; color: #52514e; }
.fig { margin: 2mm 0 1mm; }
.fig img, .fig svg { width: 100%; display: block; }
.cap { font-size: 8.4pt; color: #52514e; margin: 1mm 0 4mm; }
.note { font-size: 8.6pt; color: #52514e; }
.total td { font-weight: 600; border-bottom: none; border-top: 1px solid #0b0b0b; }
.small { font-size: 7.8pt; }
"""


def table(head, rows, cls="", num=()):
    h = "".join('<th class="%s">%s</th>' % ("n" if i in num else "", c) for i, c in enumerate(head))
    b = "".join("<tr%s>%s</tr>" % (' class="total"' if r and str(r[0]).startswith("<b>") else "",
                                    "".join('<td class="%s">%s</td>' % ("n" if i in num else "", c) for i, c in enumerate(r)))
                for r in rows)
    return '<table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (cls, h, b)


def build_html(smd, c1, c2, c3, diagram):
    nb_smd = sum(len(l["refs"]) for l in smd)
    rows, total = costs()
    specs = [
        ("Fonction", "Égaliseur graphique mono pour caisson de basses"),
        ("Bandes", "31 · 40 · 50 · 63 · 80 Hz, ±12 dB chacune, cran central à 0 dB"),
        ("Filtre subsonique", "Passe-haut fixe à 20 Hz, 12 dB / octave"),
        ("Entrée / sortie", "Jack 6,35 mm asymétrique, niveau ligne +4 dBu. Entrée ≈ 50 kΩ, sortie 100 Ω"),
        ("Bande passante", "Signal pleine bande accepté : réponse plate au-dessus des bandes"),
        ("Niveau maximal", "≈ +19 dBu en sortie (rails ±12 V)"),
        ("Alimentation", "Bloc 12 V continu, + au centre ; masse audio isolée du bloc"),
        ("Carte", "90 × 62 mm, 2 couches, %d CMS (0805, SOIC) + traversants" % nb_smd),
        ("Boîtier", "Imprimé 3D, 97 × 71 × 25 mm, doublé de ruban de cuivre"),
    ]
    bands = [(b[0] + " Hz", " + ".join(val_fr(circuit.fmt(v)) for v in r1), " + ".join(val_fr(circuit.fmt(v)) for v in r2),
              " + ".join(val_fr(circuit.fmt(v)) for v in r3))
             for b, (_, r1, r2, r3) in zip(circuit.BANDS, circuit.BAND_PARTS)]
    perf = []
    for i, b in enumerate(circuit.BANDS):
        up = [0.5] * 5; up[i] = 1.0
        f, g, q = sim_eq.peak(up)
        perf.append((b[0] + " Hz", fr(f, 1) + " Hz", "±" + fr(g, 1) + " dB", fr(q, 1)))
    ex_rows = []
    fs = np.logspace(np.log10(20), np.log10(200), 200)
    for name, pos in EXAMPLES:
        g = [sim_eq.db(sim_eq.resp(f, pos, hpf=False)["OUT"]) for f in fs]
        k = int(np.argmax(np.abs(g)))
        ex_rows.append([name] + [("%+d %%" % round((p - 0.5) * 200)).replace("-", "−") if abs(p - 0.5) > 1e-9 else "cran" for p in pos]
                       + ["%s dB à %s Hz" % (("+" if g[k] > 0 else "−") + fr(abs(g[k]), 1), fr(fs[k], 0))])
    smd_rows = [(val_fr(l["val"]), designation(l["val"], l["pkg"]), len(l["refs"]), ", ".join(l["refs"]), l["lcsc"],
                 "de base" if l["basic"] else "étendu") for l in smd]
    tht_rows = [(refs, desc, part, q, fr(p, 3 if p < 1 else 2)) for refs, desc, part, q, p, _ in THT]
    cost_rows = [(n, fr(ht) if ht else "—", "≈ " + fr(ttc, 0), src) for n, ht, ttc, src in rows]
    cost_rows.append(("<b>Total pour %d boîtes</b>" % UNITS, "", "<b>≈ %s €</b>" % fr(total, 0), "≈ %s € par boîte" % fr(total / UNITS, 0)))
    jlc_rows = [(n, fr(v)) for n, v in JLC_QUOTE] + [("<b>Total hors port, hors TVA</b>", "<b>%s</b>" % fr(sum(v for _, v in JLC_QUOTE)))]
    return """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Sub EQ</title><style>%s</style></head><body>

<div class="page">
<h1>Sub EQ</h1>
<div class="sub">Égaliseur graphique 5 bandes pour caisson de basses</div>
<div class="fig"><img src="apercu-boitier.png" alt="Vue éclatée du boîtier"></div>
<div class="cap">Vue éclatée : fond, carte, couvercle, panneaux avant et arrière. Façade : 5 potentiomètres et une LED. Arrière : entrée, sortie, alimentation.</div>
%s
<h3>État</h3>
<p>Conçu et vérifié par calcul : règles électriques et de routage KiCad sans erreur, réponse simulée à partir des valeurs réelles, boîtier contrôlé contre le modèle 3D de la carte. <b>Pas encore fabriqué ni mesuré.</b></p>
</div>

<div class="page">
<h2>Schéma fonctionnel</h2>
<div class="fig">%s</div>
<div class="cap">Chaque bande est un filtre passe-bande. Son potentiomètre envoie le signal filtré vers le sommateur de coupe ou vers celui de boost ; au centre, les deux s'annulent et la réponse est plate.</div>
<h3>Valeurs des cinq filtres (condensateurs : 2 × 220 nF film par bande)</h3>
%s
<p class="note">Les valeurs séparées par « + » sont deux résistances en série. Schéma électrique complet en dernière page.</p>
<h3>Chaque bande seule, à fond (simulation)</h3>
%s
</div>

<div class="page">
<h2>Réponse en fréquence (simulée)</h2>
<h3>Une bande à la fois, au maximum puis au minimum</h3>
<div class="fig">%s</div>
<h3>Exemples de réglages courants</h3>
<div class="fig">%s</div>
%s
<h3>Cas extrêmes : toutes les bandes en butée</h3>
<div class="fig">%s</div>
<div class="cap">Calcul avec amplis-op idéaux, filtre subsonique inclus. Position des boutons : 0 %% = cran central, ±100 %% = butée. Les bandes voisines s'additionnent : cinq bandes à fond donnent +17 dB, un réglage qui ne correspond pas à un usage normal.</div>
</div>

<div class="page">
<h2>Carte électronique</h2>
<div class="fig"><img src="img/pcb.png" alt="Vue de dessus de la carte"></div>
<div class="cap">Vue de dessus, 90 × 62 mm. En haut (arrière du boîtier) : jacks, prise DC, convertisseur. En bas (façade) : les cinq potentiomètres et la LED. Rendu KiCad : les potentiomètres, les jacks, la prise DC et le convertisseur n'y figurent pas ; la carte commandée est noire.</div>
<h3>Fabrication prévue</h3>
%s
</div>

<div class="page">
<h2>Nomenclature (par carte)</h2>
<h3>Composants montés en surface, posés par JLCPCB : %d lignes, %d composants</h3>
%s
</div>

<div class="page">
<h2>Nomenclature (suite) et coût</h2>
<h3>Composants traversants, soudés à la main (Mouser)</h3>
%s
<h3>Mécanique (par boîte)</h3>
%s
<h3>Devis JLCPCB relevé le 10/11/2026 : 5 PCB, CMS posés sur 2 cartes</h3>
%s
<h3>Coût pour %d boîtes complètes</h3>
%s
<p class="note">Prix relevés le 10/11/2026. Port Mouser non compté (commande groupée). Les montants « estimés » ne viennent pas d'un devis.</p>
</div>
</body></html>""" % (
        CSS, table(["", ""], specs, "kv"), diagram,
        table(["Bande", "Résistance d'entrée", "Vers la masse", "Contre-réaction"], bands),
        table(["Bande", "Fréquence du maximum", "Plage", "Q à −3 dB"], perf, num=(1, 2, 3)),
        c1, c3, table(["Réglage", "31 Hz", "40 Hz", "50 Hz", "63 Hz", "80 Hz", "Effet maximal"], ex_rows, num=(1, 2, 3, 4, 5, 6)), c2,
        table(["", ""], [
            ("Circuit imprimé", "JLCPCB, 2 couches, 1,6 mm, noir, finition HASL"),
            ("CMS", "Posés par JLCPCB (assemblage « Economic », face du dessus)"),
            ("Traversants", "Potentiomètres, jacks, prise DC, convertisseur, condensateurs film, LED : soudés à la main"),
            ("Boîtier", "4 pièces imprimées en PETG, 4 vis M3 dans des inserts à chaud"),
        ], "kv"),
        len(smd), nb_smd,
        table(["Valeur", "Désignation", "Qté", "Repères", "Réf. LCSC", "Catalogue"], smd_rows, "small", num=(2,)),
        table(["Repères", "Pièce", "Référence", "Qté", "€ HT pièce"], tht_rows, num=(3, 4)),
        table(["Pièce", "Qté", "Remarque"], [(d, q, n) for d, q, n in MECA], num=(1,)),
        table(["Poste", "€ HT"], jlc_rows, num=(1,)),
        UNITS, table(["Poste", "€ HT", "€ TTC", "Source"], cost_rows, num=(1, 2)))


def main():
    os.makedirs(IMG, exist_ok=True)
    smd = smd_lines()
    write_bom_md(smd)
    c1, c2, c3 = curves()
    diagram = block_diagram()
    for name, svg in (("courbes-bandes.svg", c1), ("courbes-ensemble.svg", c2), ("courbes-exemples.svg", c3),
                      ("schema-fonctionnel.svg", diagram)):
        open(os.path.join(IMG, name), "w").write(svg)
    render_pcb()
    prev = os.path.join(ROOT, "enclosure", "out", "preview.png")
    if os.path.exists(prev):
        open(os.path.join(DOCS, "apercu-boitier.png"), "wb").write(open(prev, "rb").read())
    page = os.path.join(DOCS, "sub-eq-fiche.html")
    open(page, "w").write(build_html(smd, c1, c2, c3, diagram))
    body = os.path.join(tempfile.mkdtemp(), "body.pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + body,
                    "file://" + page], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = os.path.join(DOCS, "sub-eq-fiche.pdf")
    from pypdf import PdfReader, PdfWriter      # append the full KiCad schematic as the last page
    w = PdfWriter()
    for src in (body, os.path.join(ROOT, "hardware", "fab", "schematic.pdf")):
        for p in PdfReader(src).pages:
            w.add_page(p)
    w.add_metadata({"/Title": "Sub EQ — fiche projet", "/Subject": "Égaliseur graphique 5 bandes pour caisson de basses"})
    with open(out, "wb") as f:
        w.write(f)
    os.remove(page)
    print("wrote", out, "| pages:", len(PdfReader(out).pages))


if __name__ == "__main__":
    main()
