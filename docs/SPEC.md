# Sub EQ — spécification v1 (validée le 2026-11-10)

Égaliseur graphique 5 bandes dédié aux caissons de basses, mono, dans un boîtier le plus petit possible. Exemplaire unique.

> Les valeurs marquées « conception » ont été figées après la validation, par calcul ou simulation (`hardware/scripts/sim_eq.py`, résultat dans `hardware/sim-report.txt`).

## Fonction

| Élément | Spécification |
|---|---|
| Bandes | 31, 40, 50, 63 et 80 Hz (tiers d'octave, Q = 4,3) |
| Plage | ±12 dB par bande, cran central à 0 dB. Conception : ±12,4 dB simulés ; +3,7 dB à mi-course |
| Topologie | égaliseur à Q constant : 5 passe-bande à contre-réaction multiple, un sommateur de coupe et un de boost. 9 sections d'ampli-op (2 × TL074, 1 × TL072), aucune inductance. Toutes les résistances sont des valeurs du catalogue « de base » de JLCPCB, certaines en série, pour permettre un assemblage sans frais de pièces étendues |
| Canaux | mono |
| Gain | unité quand tous les potentiomètres sont au centre (exact par construction) |
| Filtre subsonique | passe-haut fixe à 20 Hz, 12 dB / octave (Butterworth), toujours en service : −0,65 dB à 31 Hz |
| Bypass | aucun |

Deux comportements à connaître, propres à tout égaliseur graphique :
- les bandes voisines s'additionnent : les cinq à fond donnent +17 dB et non +12 dB ;
- une bande à fond agit encore de ≈ +2 dB une octave plus loin.

## Entrées / sorties

| Élément | Spécification |
|---|---|
| Entrée | 1 × jack 6,35 mm mono, asymétrique (TS), niveau ligne pro +4 dBu nominal, impédance ≈ 50 kΩ. Entrée mise à la masse quand rien n'est branché |
| Sortie | 1 × jack 6,35 mm mono, asymétrique (TS), impédance de sortie 100 Ω, condensateur de liaison |
| Marge | pas d'écrêtage avec +4 dBu en entrée et 12 dB de boost (+16 dBu en sortie). Sortie max ≈ +19 à +20 dBu, limitée par les rails ±12 V |

## Alimentation

- Bloc secteur **12 V continu** dédié à cette boîte, prise DC 5,5 / 2,1 mm, **positif au centre**. Consommation ≈ 60 mA.
- Diode Schottky en série contre l'inversion de polarité.
- Convertisseur DC-DC isolé **Traco TMA 1212D** (±12 V non régulés, 42 mA par rail), puis filtre 10 Ω + 100 µF par rail. La masse audio est isolée de la masse du bloc secteur : pas de boucle de masse par l'alimentation.
- LED témoin en façade. Pas d'interrupteur.

## Commandes

- Façade : 5 potentiomètres rotatifs 9 mm, 20 kΩ linéaires à cran central, de gauche à droite 31 / 40 / 50 / 63 / 80 Hz. Sens horaire = boost. LED de marche à droite.
- Arrière, vu de dos de gauche à droite : 12 V DC, OUT, IN.

## Fabrication

- PCB nu chez JLCPCB, 2 couches, **90 × 62 mm**, **tout soudé à la main** : CMS en 0805 / SOIC, puis les traversants. Option : CMS posés par JLCPCB, voir [ASSEMBLAGE-JLC.md](ASSEMBLAGE-JLC.md).
- Potentiomètres, jacks et prise DC soudés sur le PCB : aucun câblage interne, sauf le fil de masse du blindage.

## Boîtier

- Imprimé en 3D, méthode audio-box : fond et couvercle en U, panneaux avant et arrière glissés dans des rainures, 4 vis M3 qui serrent fond, PCB et couvercle.
- **Blindage** : ruban de cuivre à adhésif conducteur collé à l'intérieur, relié à la pastille SHIELD (TP1) par un fil soudé. Important ici : les bandes entourent le 50 Hz du secteur. Les carcasses des potentiomètres sont à la masse.
- Conception : **97 × 71 × 25 mm** (l × p × h), pour 92 × 68 × 32 mm visés. La largeur vient des 5 potentiomètres au pas de 15 mm et des 4 vis.

## Budget

Pas de plafond, mais on cherche l'économie : amplis-op courants, pas de pièce exotique.
