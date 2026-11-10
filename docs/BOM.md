# Nomenclature du Sub EQ

Générée par `hardware/scripts/build_doc.py`. Quantités **par carte** ; prix et stocks relevés le 2026-11-10.

## CMS posés par JLCPCB (35 lignes, 70 composants par carte)

Fichiers : `hardware/jlc/bom_jlc.csv` et `cpl_jlc.csv`. Pour les souder à la main : `hardware/fab/bom_mouser_smd.csv`.

| Valeur | Désignation | Qté | Repères | Réf. LCSC | Catalogue JLCPCB |
|---|---|---|---|---|---|
| 1 nF | Céramique 0805, X7R 50 V | 1 | C1 | C46653 | de base |
| 22 pF | Céramique 0805, C0G 50 V | 2 | C4, C5 | C1804 | de base |
| 100 µF | Électrolytique CMS 35 V, Ø 6,3 × 7,7 mm | 3 | C6, C10, C11 | C970686 | étendu |
| 10 µF | Céramique 0805, X5R 25 V | 3 | C7, C8, C9 | C15850 | de base |
| 100 nF | Céramique 0805, X7R 50 V | 6 | C12, C13, C14, C15, C16, C17 | C49678 | de base |
| 1N5819HW | Schottky 40 V 1 A, SOD-123 (B5819W) | 1 | D1 | C8598 | de base |
| 1 MΩ | Résistance 0805, 1 % | 1 | R1 | C17514 | de base |
| 470 Ω | Résistance 0805, 1 % | 1 | R2 | C17710 | de base |
| 51 kΩ | Résistance 0805, 1 % | 3 | R3, R4, R16 | C17737 | de base |
| 20 kΩ | Résistance 0805, 1 % | 6 | R5, R6, R7, R8, R9, R10 | C4328 | de base |
| 100 Ω | Résistance 0805, 1 % | 1 | R11 | C17408 | de base |
| 100 kΩ | Résistance 0805, 1 % | 4 | R12, R101, R303, R403 | C149504 | de base |
| 10 Ω | Résistance 0805, 1 % | 2 | R13, R14 | C17415 | de base |
| 4,7 kΩ | Résistance 0805, 1 % | 1 | R15 | C17673 | de base |
| 2,7 kΩ | Résistance 0805, 1 % | 1 | R102 | C17530 | de base |
| 200 kΩ | Résistance 0805, 1 % | 1 | R103 | C17539 | de base |
| 2 kΩ | Résistance 0805, 1 % | 10 | R104, R105, R204, R205, R304, R305, R404, R405, R504, R505 | C17604 | de base |
| 68 kΩ | Résistance 0805, 1 % | 2 | R201, R503 | C17801 | de base |
| 2,2 kΩ | Résistance 0805, 1 % | 1 | R202 | C17520 | de base |
| 150 kΩ | Résistance 0805, 1 % | 1 | R203 | C17470 | de base |
| 8,2 kΩ | Résistance 0805, 1 % | 1 | R206 | C17828 | de base |
| 2,4 kΩ | Résistance 0805, 1 % | 1 | R208 | C17526 | de base |
| 47 kΩ | Résistance 0805, 1 % | 2 | R301, R401 | C17713 | de base |
| 1,5 kΩ | Résistance 0805, 1 % | 1 | R302 | C4310 | de base |
| 15 kΩ | Résistance 0805, 1 % | 1 | R306 | C17475 | de base |
| 220 Ω | Résistance 0805, 1 % | 1 | R307 | C17557 | de base |
| 24 kΩ | Résistance 0805, 1 % | 1 | R308 | C17575 | de base |
| 680 Ω | Résistance 0805, 1 % | 3 | R402, R407, R502 | C17798 | de base |
| 3 kΩ | Résistance 0805, 1 % | 1 | R406 | C17661 | de base |
| 27 kΩ | Résistance 0805, 1 % | 1 | R501 | C17593 | de base |
| 12 kΩ | Résistance 0805, 1 % | 1 | R506 | C17444 | de base |
| 390 Ω | Résistance 0805, 1 % | 1 | R507 | C17655 | de base |
| 10 kΩ | Résistance 0805, 1 % | 1 | R508 | C17414 | de base |
| TL074 | Quadruple ampli-op JFET, SOIC-14 | 2 | U1, U2 | C12594 | étendu |
| TL072 | Double ampli-op JFET, SOIC-8 | 1 | U3 | C6961 | de base |

## Traversants, soudés à la main (Mouser)

| Repères | Pièce | Référence | Qté | € HT pièce | Stock |
|---|---|---|---|---|---|
| RV1–RV5 | Potentiomètre 20 kΩ linéaire, cran central, 9 mm, canon M9 | Alps RK09L112003P | 5 | 2,46 | 761 |
| J1, J2 | Embase jack 6,35 mm mono, coudée | Neutrik NMJ4HCD2 | 2 | 1,92 | 8 133 |
| PS1 | Convertisseur DC-DC isolé 12 V → ±12 V, 1 W | Traco TMA 1212D | 1 | 4,80 | 379 |
| C2, C3, C101–C502 | Condensateur film 220 nF 63 V 5 %, pas 5 mm | KEMET R82DC3220SH60J | 12 | 0,158 | 1 657 |
| J3 | Prise DC 5,5 / 2,1 mm, coudée | Same Sky PJ-102AH | 1 | 0,662 | 32 489 |
| D2 | LED 3 mm rouge | Kingbright WP710A10LID | 1 | 0,232 | 21 676 |
| — | Bouton Ø 11 mm pour axe en D de 6 mm | Same Sky SPK-016A | 5 | 0,252 | 2 487 |

## Mécanique (par boîte)

| Pièce | Qté | Remarque |
|---|---|---|
| Boîtier imprimé 3D : fond, couvercle, 2 panneaux (PETG, ≈ 60 g) | 1 | fichiers STL fournis |
| Vis M3 × 14 tête fraisée | 4 |  |
| Insert fileté à chaud M3 × 5,7 | 4 |  |
| Patin adhésif Ø 10 mm | 4 |  |
| Ruban de cuivre à adhésif conducteur (blindage) | 1 | un rouleau pour les deux |
| Bloc secteur 12 V DC régulé, ≥ 300 mA, fiche 5,5 / 2,1 mm, + au centre | 1 |  |

## Coût pour 2 unités

| Poste | € HT | € TTC | Source |
|---|---|---|---|
| JLCPCB : 5 PCB, CMS posés sur 2 cartes | 21,41 | ≈ 26 | devis relevé |
| JLCPCB : port standard et dédouanement | — | ≈ 13 | estimé |
| Mouser : composants traversants (port non compté) | 50,30 | ≈ 60 | prix relevés |
| 2 blocs secteur 12 V | — | ≈ 18 | estimé |
| Ruban de cuivre, vis, inserts, patins, filament | — | ≈ 14 | estimé |
| **Total** | | **≈ 131 €**, soit ≈ 65 € par boîte | |
