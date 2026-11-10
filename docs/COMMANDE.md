# Commande : 2 Sub EQ, CMS posés par JLCPCB

Prix et stocks relevés le 2026-11-10 ; revérifie-les au moment de commander. Rien n'est commandé. Détail de chaque composant : [BOM.md](BOM.md).

## 1. JLCPCB : PCB et assemblage des CMS

Fichiers à envoyer sur cart.jlcpcb.com/quote :

| Fichier | Rôle |
|---|---|
| `hardware/fab/sub-eq-gerbers.zip` | circuit imprimé |
| `hardware/jlc/bom_jlc.csv` | nomenclature, avec la référence LCSC de chaque ligne |
| `hardware/jlc/cpl_jlc.csv` | position des 70 CMS |

- **PCB :** 2 couches, 1,6 mm, 90 × 62 mm, **5 exemplaires** (le minimum), noir, HASL (with lead), pas de pochoir à commander.
- **PCB Assembly :** Economic, Top Side, **PCBA Qty 2**, Tooling holes « Added by JLCPCB ».
- **Devis relevé : 21,41 € HT**, hors port. Détail dans [ASSEMBLAGE-JLC.md](ASSEMBLAGE-JLC.md).
- **Port :** choisis « Global Standard Direct Line » ; le site présélectionne DHL Express (≈ 21 €).

À vérifier sur le site avant de payer :
- **toutes les lignes de la nomenclature sont cochées** (le site en laisse une partie décochée tout en affichant « parts confirmed ») : 35 lignes, 33 de base et 2 étendues ;
- le délai « 24 hours (PCBA Only) » n'est pas resté présélectionné ;
- le panier ne contient plus l'ancienne version de la carte.

## 2. Mouser : composants traversants (pour 2 cartes)

| Repères | Qté | Pièce | Réf. fabricant (Mouser) | € HT | Stock |
|---|---|---|---|---|---|
| RV1–RV5 | 10 | Potentiomètre 20 kΩ linéaire, cran central, canon M9, axe en D 15 mm | Alps RK09L112003P (688-RK09L112003P) | 10 × 2,46 | 761 |
| J1, J2 | 4 | Jack 6,35 mm mono commuté, coudé, avec écrou | Neutrik NMJ4HCD2 (550-12202) | 4 × 1,92 | 8 133 |
| PS1 | 2 | DC-DC isolé 12 V → ±12 V, 1 W | Traco TMA 1212D (495-TMA-1212D) | 2 × 4,80 | 379 |
| C2, C3, C101–C502 | 24 (+2) | Film 220 nF 63 V 5 %, pas de 5 mm | KEMET R82DC3220SH60J (80-R82DC3220SH60J) | 26 × 0,158 | 1 657 |
| J3 | 2 | Prise DC 5,5 / 2,1 mm coudée | Same Sky PJ-102AH (490-PJ-102AH) | 2 × 0,662 | 32 489 |
| D2 | 2 | LED 3 mm rouge faible courant | Kingbright WP710A10LID (604-WP710A10LID) | 2 × 0,232 | 21 676 |
| — | 10 | Bouton Ø 11 mm pour axe en D de 6 mm | Same Sky SPK-016A (179-SPK-016A) | 10 × 0,252 | 2 487 |

**Total : 50,30 € HT**, port non compté (commande groupée). Délai usine long sur le potentiomètre (21 semaines) : le stock actuel suffit, mais ne tarde pas.

## 3. Mécanique et accessoires (pour 2 boîtes, estimations)

| Qté | Pièce | ≈ € |
|---|---|---|
| 2 | Bloc secteur 12 V continu régulé, ≥ 300 mA, fiche 5,5 / 2,1 mm, **positif au centre** | 18 |
| 1 | Ruban de cuivre à adhésif conducteur, 25 à 50 mm de large | 8 |
| 8 | Vis M3 × 14 tête fraisée (ISO 10642) | 2 |
| 8 | Inserts filetés à chaud M3 × 5,7 (le sachet d'audio-box suffit) | — |
| 8 | Patins adhésifs Ø 10 mm | 1 |
| — | Filament PETG ≈ 120 g | 3 |

**Total : ≈ 131 € TTC pour 2 boîtes.** Détail dans [CHIFFRAGE.md](CHIFFRAGE.md).

## Variante : souder les CMS à la main

Commande alors les PCB nus (sans « PCB Assembly ») et importe `hardware/fab/bom_mouser_smd.csv` dans le BOM Tool de Mouser, en conditionnement « Cut Tape ». Le stock des nouvelles valeurs de résistances n'a pas été relevé une à une ; toute résistance 0805 à 1 % de la même valeur convient.
