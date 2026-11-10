# Sub EQ

Égaliseur graphique 5 bandes pour caissons de basses (31, 40, 50, 63, 80 Hz), mono, jacks 6,35 mm, alimentation 12 V DC. Exemplaire unique, PCB 90 × 62 mm, boîtier 97 × 71 × 25 mm.

| Document | Contenu |
|---|---|
| [docs/SPEC.md](docs/SPEC.md) | spécification validée et valeurs figées à la conception |
| [docs/COMMANDE.md](docs/COMMANDE.md) | PCB, composants, visserie à commander |
| [docs/CHIFFRAGE.md](docs/CHIFFRAGE.md) | coût détaillé |
| [docs/MONTAGE.md](docs/MONTAGE.md) | contrôles, impression, soudure, tests, assemblage |

## Fichiers produits

- `hardware/sub-eq.kicad_sch`, `hardware/sub-eq.kicad_pcb` : schéma et carte (générés, ne pas éditer à la main).
- `hardware/fab/` : Gerbers zippés, nomenclatures, PDF du schéma et de l'implantation, STEP de la carte.
- `hardware/sim-report.txt` : réponse calculée à partir des valeurs réelles du circuit.
- `enclosure/out/` : STL et STEP des 4 pièces imprimées, vue éclatée `preview.png`.
- `viewer/` : visionneuse 3D web (voir [viewer/README.md](viewer/README.md)).

| Domaine | Source | Généré |
|---|---|---|
| Visionneuse | `viewer/src/scene/dims.ts`, `Connectors.tsx` | `viewer/public/models/` via `npm run assets` |

Toute modification d'une pièce de panneau se répercute dans `hardware/scripts/gen_pcb.py`, `enclosure/enclosure.py` et `viewer/src/scene/dims.ts`.

## Régénérer

```bash
FREEROUTING_JAR=~/.cache/freerouting/freerouting-2.5.0.jar ./build.sh
```

Il faut KiCad 10 dans `~/Applications/KiCad`, Java 21 ou plus, [Freerouting](https://github.com/freerouting/freerouting/releases) 2.5 et un `.venv` avec `numpy`, `build123d` et `cairosvg` (ici un lien vers celui d'audio-box).

Visionneuse 3D : `cd viewer && npm install && npm run assets && npm run dev` (http://localhost:5174).
