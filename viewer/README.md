# Sub EQ — visionneuse 3D

Application web locale (Vite + React + TypeScript + React Three Fiber) qui montre le boîtier
de l'égaliseur assemblé : pièces imprimées, PCB réel issu de KiCad et pièces de panneau.
Copie adaptée de la visionneuse d'audio-box.

## Lancer

```bash
cd viewer
npm install        # première fois
npm run assets     # régénère public/models/ depuis le STEP et KiCad
npm run dev        # http://localhost:5174
npm run build      # build de production dans viewer/dist (npm run preview pour le servir)
```

Ou, depuis Claude Code, la configuration « viewer » de `.claude/launch.json` (port 5174 ; audio-box
utilise 5173 et dj-filter 5175).

Aucun backend, aucun accès réseau à l'exécution (l'éclairage studio est généré localement par des
`Lightformer`, pas de HDR téléchargé).

## Commandes

- **Souris** : glisser = orbite, molette = zoom, clic droit = panoramique.
- **Barre du bas** : vues *Avant ¾*, *Arrière ¾*, *Dessus*, *Gros plan avant*, bouton *Éclater / Assembler*, *Capture PNG*.
- **Panneau « Réglages »** (leva) :
  - *Éclaté* 0–1 : couvercle vers le haut, panneaux vers l'extérieur, fond vers le bas, PCB fixe
    (boutons et écrous suivent leur panneau, en allant plus loin).
  - *Couvercle*, *Panneaux*, *PCB*, *Rayons X* (boîtier semi-transparent), *Étiquettes* (toutes visibles).
  - *Sous tension* (LED allumée), une glissière par bande (31, 40, 50, 63, 80 Hz) de −12 à +12 dB :
    rotation du bouton, 300° de course, 0 dB au cran central, sens horaire = boost.
  - *Filament* (Anthracite, Blanc, Sable, Olive), couleur libre du boîtier, couleur des boutons.
  - *Capture PNG* : télécharge l'image du canvas.
- **Survol** d'une pièce de panneau : étiquette détaillée (IN, OUT, 12V DC, 31 à 80 Hz, ON).

## D'où viennent les modèles

Le reste du dépôt est la source de vérité ; `viewer/public/models/` n'est qu'un dérivé.

| Fichier | Source | Remarque |
|---|---|---|
| `tray.glb`, `lid.glb`, `back_panel.glb`, `front_panel.glb` | `enclosure/out/*.step` | déjà dans le repère boîtier ; gravures incluses |
| `pcb.glb` | `hardware/fab/sub-eq-pcb.step` | couleurs par face conservées (lecture XCAF), recalé comme `enclosure/check_fit.py` |
| `pcb_top_color.png`, `pcb_top_rm.png` | `hardware/sub-eq.kicad_pcb` via `kicad-cli pcb export svg` (F.Cu, F.Mask, F.Silkscreen) | texture de la face composants : pistes sous vernis noir, pastilles HASL, sérigraphie |
| `assets.json` | — | offset PCB appliqué, date de génération |

`convert_assets.py` importe `enclosure/enclosure.py` (dimensions du PCB, hauteur de la carte, trous) et
**vérifie `src/scene/dims.ts`** : chaque constante qui porte le même nom que dans `enclosure.py`
(positions des pièces de panneau, hauteurs d'axe, corps des pièces, cotes du boîtier) doit avoir la même valeur,
sinon la conversion s'arrête en listant les écarts.

### Commande de conversion

```bash
.venv/bin/python viewer/scripts/convert_assets.py     # depuis la racine du projet
# équivalent : (cd viewer && npm run assets)
```

Le script utilise le venv build123d/OCP (lien vers celui d'audio-box) et
`~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` pour les couches du PCB
(si kicad-cli est absent, la texture n'est simplement pas régénérée).

### Rafraîchir après une modification

1. **Boîtier modifié** : `cd enclosure && ../.venv/bin/python enclosure.py`, puis la conversion.
2. **PCB modifié** : `build.sh` (ou `build_fab.py`, qui régénère le STEP), puis la conversion.
3. **Pièce de panneau déplacée ou changée** : modifier `gen_pcb.py` et `enclosure.py` (puis `check_fit.py`),
   reporter la cote dans `src/scene/dims.ts`, puis la conversion (qui contrôle la cohérence).

Recharger la page suffit ensuite (`npm run dev` sert directement `public/models/`).

## Organisation du code

```
viewer/
  scripts/convert_assets.py   conversion STEP/KiCad -> GLB/PNG, contrôle de dims.ts
  public/models/              assets générés
  src/App.tsx                 canvas, panneau leva, barre de vues, capture PNG
  src/scene/Scene.tsx         assemblage, éclaté, éclairage, ombres, caméra, étiquettes
  src/scene/EnclosurePart.tsx pièces PETG (lignes de couches en normal map, rayons X)
  src/scene/Pcb.tsx           PCB KiCad + texture de la face composants + LED
  src/scene/Connectors.tsx    maquettes : jack NMJ4HCD2, potentiomètre RK09L, bouton SPK-016A, prise DC PJ-102AH,
                              DC-DC TMA 1212D, visserie, pieds
  src/scene/dims.ts           cotes (mm) reprises de enclosure.py
  src/scene/materials.ts      matériaux PBR et textures procédurales
  screenshots/                captures de vérification
```

En développement, `window.__viewer` expose `set({...})`, `view('front34' | 'back34' | 'top' | 'closeFront')`
et `shot(nom)` (écrit `screenshots/<nom>.png` via un petit middleware Vite, dev uniquement) ;
`window.__viewerCam([x, y, z], [cx, cy, cz])` place la caméra (repère three.js, Y en haut) pour les contrôles.

## Approximations

- Pièces sans modèle 3D KiCad (jacks, potentiomètres, boutons, prise DC, DC-DC) : formes simplifiées aux cotes
  de `enclosure.py` (`envelopes()`) et des plans constructeurs ; détails (contacts, filetages, cosses) indicatifs.
- Écrou du jack : 11 mm sur plats comme indiqué, sur un nez fileté de Ø 11 : il ne reste presque pas de matière
  sur les plats. Une des deux valeurs est probablement à revoir sur le plan ST-NMJ4HCD2.
- Écrou M9 du potentiomètre (12 mm sur plats, 2 mm) et rondelle : valeurs courantes, non vérifiées.
- Bouton SPK-016A : cylindre strié noir Ø 11 × 17,2 mm, trait repère blanc ; forme exacte (jupe, profil) non vérifiée.
  Posé 0,3 mm devant le bout du canon.
- La LED et les composants CMS / condensateurs viennent du STEP KiCad (la LED est recolorée en rouge diffus).
- Couleur du vernis : noir (choix d'audio-box ; `docs/COMMANDE.md` laisse la couleur au choix).
- Le PCB du STEP fait 1,51 mm d'épaisseur au lieu de 1,6 : la carte est posée sur `Z_PCB_BOT`, comme dans `check_fit.py`.
