"""Custom schematic symbols -> hardware/<project>.kicad_sym

TMA_Dual: TRACO TMA xxxxD, 1 W isolated DC-DC, SIP-7. Pin numbers from the TRACO TMA datasheet
(page 4, "Pinout", dual column): 1 +Vin, 2 -Vin, 4 -Vout, 5 Common, 6 +Vout (no pin 3, no pin 7).
All pins are typed passive; the rails get PWR_FLAGs in circuit.py.
"""
import os
from sexp import dump, Sym
import circuit

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", circuit.PROJECT + ".kicad_sym")
S = Sym


def font():
    return [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]


def prop(name, value, x, y, hide=False):
    p = [S("property"), name, value, [S("at"), x, y, 0], font()]
    if hide:
        p[-1].append([S("hide"), S("yes")])
    return p


def pin(num, name, x, y, ang, etype="passive"):
    return [S("pin"), S(etype), S("line"), [S("at"), x, y, ang], [S("length"), 2.54],
            [S("name"), name, font()], [S("number"), str(num), font()]]


def tma_dual():
    pins = [pin(1, "+Vin", -12.7, 2.54, 0), pin(2, "-Vin", -12.7, -2.54, 0),
            pin(6, "+Vout", 12.7, 5.08, 180), pin(5, "Com", 12.7, 0, 180), pin(4, "-Vout", 12.7, -5.08, 180)]
    return [S("symbol"), "TMA_Dual", [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
            [S("on_board"), S("yes")],
            prop("Reference", "PS", 0, 10.16), prop("Value", "TMA_Dual", 0, -10.16),
            prop("Footprint", "Converter_DCDC:Converter_DCDC_TRACO_TMA-05xxD_12xxD_Dual_THT", 0, 0, True),
            prop("Datasheet", "https://www.tracopower.com/products/tma.pdf", 0, 0, True),
            prop("Description", "1 W isolated unregulated DC-DC converter, dual output, SIP-7", 0, 0, True),
            [S("symbol"), "TMA_Dual_0_1",
             [S("rectangle"), [S("start"), -10.16, 7.62], [S("end"), 10.16, -7.62],
              [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]],
             [S("polyline"), [S("pts"), [S("xy"), 0, 7.62], [S("xy"), 0, -7.62]],
              [S("stroke"), [S("width"), 0.254], [S("type"), S("dash")]], [S("fill"), [S("type"), S("none")]]]],
            [S("symbol"), "TMA_Dual_1_1"] + pins]


def pot(name, descr, left, right):
    """Box-style potentiometer with the metal frame lugs (footprint pads "MP") as a pin, so it can be grounded.
    Pin 1 / 4 = CCW end, 2 / 5 = wiper, 3 / 6 = CW end (Alps RK09L catalogue, shaft seen from the front)."""
    w = 5.08
    pins = [pin(n, nm, -w - 2.54, 2.54 - 2.54 * i, 0) for i, (n, nm) in enumerate(left)]
    pins += [pin(n, nm, w + 2.54, 2.54 - 2.54 * i, 180) for i, (n, nm) in enumerate(right)]
    pins.append(pin("MP", "frame", 0, -7.62, 90))
    return [S("symbol"), name, [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
            [S("on_board"), S("yes")],
            prop("Reference", "RV", 0, 7.62), prop("Value", name, 0, -10.16),
            prop("Footprint", "", 0, 0, True), prop("Datasheet", "~", 0, 0, True),
            prop("Description", descr, 0, 0, True),
            [S("symbol"), name + "_0_1",
             [S("rectangle"), [S("start"), -w, 5.08], [S("end"), w, -5.08],
              [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]],
            [S("symbol"), name + "_1_1"] + pins]


def main():
    lib = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), circuit.PROJECT],
           [S("generator_version"), "1"], tma_dual(),
           pot("Pot_MP", "Potentiometer with grounded frame", [(1, "CCW"), (2, "W"), (3, "CW")], []),
           pot("Pot_Dual_MP", "Dual potentiometer with grounded frame",
               [(1, "CCW"), (2, "W"), (3, "CW")], [(4, "CCW"), (5, "W"), (6, "CW")])]
    with open(OUT, "w") as f:
        f.write(dump(lib) + "\n")
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
