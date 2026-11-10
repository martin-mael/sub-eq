#!/usr/bin/env bash
# Regenerate everything: symbols -> schematic -> ERC + netlist check -> simulation -> PCB -> autoroute (retries)
# -> fab files -> enclosure. Needs: KiCad 10 in ~/Applications/KiCad, Java 21+, Freerouting jar (FREEROUTING_JAR),
# .venv with numpy, build123d and cairosvg.
set -euo pipefail
cd "$(dirname "$0")"
KAPP=~/Applications/KiCad/KiCad.app/Contents
: "${FREEROUTING_JAR:?set FREEROUTING_JAR=/path/to/freerouting-2.5.0.jar}"
export FREEROUTING_JAR JAVA=${JAVA:-/opt/homebrew/opt/openjdk/bin/java}
NET=$(mktemp -d)/sub-eq.net

cd hardware/scripts
python3 gen_symbols.py
python3 gen_schematic.py
"$KAPP/MacOS/kicad-cli" sch erc --severity-error --exit-code-violations -o ../fab-erc.rpt ../sub-eq.kicad_sch 2>/dev/null
"$KAPP/MacOS/kicad-cli" sch export netlist --format kicadsexpr -o "$NET" ../sub-eq.kicad_sch >/dev/null 2>&1
python3 check_netlist.py "$NET" | tee /dev/stderr | grep -q "NETLIST OK"
../../.venv/bin/python sim_eq.py > ../sim-report.txt
./route_until_clean.sh          # gen_pcb.py + route_pcb.py + DRC, retried until clean
python3 build_fab.py 2>/dev/null
cd ../../enclosure
../.venv/bin/python enclosure.py && ../.venv/bin/python check_fit.py && ../.venv/bin/python preview.py
