# sub-eq

Égaliseur graphique 5 bandes pour caissons de basses (31, 40, 50, 63, 80 Hz), mono, jacks 6,35 mm, alimentation 12 V DC. **Exemplaire unique** : toute incertitude se tranche maintenant.

La méthode générale est dans le skill personnel `hardware-product`. Ce fichier ne donne que ce qui est propre à ce projet. Projet jumeau : `../dj-filter` (même alimentation, mêmes jacks, même boîtier ; les deux se commandent ensemble).

## Sources de vérité (ne pas éditer les fichiers générés à la main)
| Domaine | Source | Généré |
|---|---|---|
| Circuit et valeurs | `hardware/scripts/circuit.py` | `sub-eq.kicad_sch`, la netlist |
| Symboles sur mesure (TMA, potentiomètres avec carcasse) | `gen_symbols.py` | `sub-eq.kicad_sym` |
| Réponse calculée | `hardware/scripts/sim_eq.py` (lit `circuit.py`) | `hardware/sim-report.txt` |
| Implantation | `hardware/scripts/gen_pcb.py` (`PLACE`, `PANEL_PARTS`, `CONNECTOR_GEOM`) | `sub-eq.kicad_pcb` |
| Fabrication et BOM | `hardware/scripts/build_fab.py` (`MOUSER_SMD`, `HAND_PARTS`) | `hardware/fab/` |
| Boîtier | `enclosure/enclosure.py` (cotes reprises de `gen_pcb.py` : garder les deux synchronisés) | `enclosure/out/` |
| Visionneuse | `viewer/src/scene/dims.ts` (cotes reprises de `enclosure.py`, contrôlées par `npm run assets`), `Connectors.tsx` | `viewer/public/models/` (`npm run assets`) |

## Régénérer
```bash
FREEROUTING_JAR=~/.cache/freerouting/freerouting-2.5.0.jar ./build.sh
```
- `build.sh` enchaîne : symboles, schéma, ERC, contrôle de netlist, simulation, routage (jusqu'à 6 essais), fabrication, boîtier, contrôle d'ajustement.
- `.venv` est un lien vers `../audio-box/.venv`.
- **BOM seule :** `cd hardware/scripts && python3 build_fab.py`.
- **Boîtier seul :** `cd enclosure && ../.venv/bin/python enclosure.py && ../.venv/bin/python check_fit.py && ../.venv/bin/python preview.py`. `check_fit.py` doit afficher `interferences: 0`.
- **Visionneuse :** `cd viewer && npm install && npm run assets` après un changement du boîtier ou du PCB, puis le serveur de dev via `.claude/launch.json`, nom « viewer » (port 5174).

## Particularités
- Les potentiomètres, les jacks, la prise DC et le DC-DC n'ont **pas de modèle 3D KiCad** : `enclosure.envelopes()` les représente par des volumes tirés des plans constructeurs, et `check_fit.py` les contrôle.
- Changer une valeur dans `circuit.py` change le schéma et la sérigraphie : il faut relancer `build.sh` (routage compris).
- Toute modification d'une pièce de panneau se répercute dans `gen_pcb.py`, `enclosure.py` et `viewer/src/scene/dims.ts`, puis passe par `check_fit.py` (et `npm run assets`, qui refuse un `dims.ts` désynchronisé).

## Règles
- Aucune commande, aucun paiement, aucune connexion à un compte marchand : c'est l'utilisateur qui valide les paniers.
- Les docs (`docs/*.md`, `README.md`) sont en français.
