#!/usr/bin/env bash
# Freerouting is not deterministic: route, check DRC errors, retry (max 6 attempts).
set -uo pipefail
cd "$(dirname "$0")/.."
KAPP=~/Applications/KiCad/KiCad.app/Contents
KPY=$KAPP/Frameworks/Python.framework/Versions/Current/bin/python3
for i in 1 2 3 4 5 6; do
    # a failure here must stop everything: otherwise the previous board would be routed again, silently
    if ! "$KPY" scripts/gen_pcb.py > "${TMPDIR:-/tmp}/sub-eq-gen.log" 2>&1; then
        echo "gen_pcb.py failed:"; grep -v "Fontconfig\|wxApp\|Debug:" "${TMPDIR:-/tmp}/sub-eq-gen.log" | tail -5; exit 1
    fi
    if ! "$KPY" scripts/route_pcb.py > "${TMPDIR:-/tmp}/sub-eq-route.log" 2>&1; then
        echo "route_pcb.py failed:"; grep -v "Fontconfig\|wxApp\|Debug:" "${TMPDIR:-/tmp}/sub-eq-route.log" | tail -5; exit 1
    fi
    rm -rf en
    if "$KAPP/MacOS/kicad-cli" pcb drc --schematic-parity --refill-zones --severity-error --exit-code-violations \
        -o fab-drc.rpt sub-eq.kicad_pcb >/dev/null 2>&1; then
        "$KAPP/MacOS/kicad-cli" pcb drc --schematic-parity --refill-zones --severity-all \
            -o fab-drc-all.rpt sub-eq.kicad_pcb >/dev/null 2>&1
        echo "routing attempt $i: DRC clean ($(grep -c '^\[' fab-drc-all.rpt) warnings, see hardware/fab-drc-all.rpt)"; exit 0
    fi
    echo "routing attempt $i: DRC errors, retrying"
done
echo "no clean routing after 6 attempts (see hardware/fab-drc.rpt)"; exit 1
