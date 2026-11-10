# Commande : PCB, composants, visserie

Montage : **PCB nu chez JLCPCB, tout soudé à la main.** Prix et stocks relevés sur mouser.fr le 2026-11-10 ; revérifie-les au moment de commander. Rien n'est commandé, aucun panier n'est rempli.

## 1. PCB nus chez JLCPCB

Envoie `hardware/fab/sub-eq-gerbers.zip`, **sans assemblage**, dans la même commande que la carte de `../dj-filter` (un seul port).

- **Options :** 2 couches, 1,6 mm, **90 × 62 mm**, 5 exemplaires (le minimum).
- **Finition : HASL (with lead), couleur noire.** Le noir n'ajoute aucun supplément ; le délai de fabrication passe de 2 à 3 jours.
- **Pas de pochoir.**
- **Devis relevé le 2026-11-10** (Gerbers envoyés sur le site, sans compte ni panier) : le site détecte bien 2 couches et les bonnes dimensions, sans avertissement.

  | Finition | 5 PCB, € HT |
  |---|---|
  | HASL avec plomb (retenue) | **3,56** |
  | HASL sans plomb | 4,63 |
  | ENIG | 18,86 |

- **Port vers la France : Global Standard Direct Line, 5,99 €**, 10 à 12 jours ouvrés (estimation du site pour cette carte seule ; DHL Express : 20,92 €).
- **Les deux cartes dans le même panier** : 2 × 3,56 € + un seul port ≈ 6 €, soit ≈ 13 € HT. Avec la TVA de 20 % prélevée à la commande et ≈ 2 € de dédouanement (relevés pour audio-box) : **≈ 18 € TTC pour les deux**. Les PCB d'audio-box peuvent partir dans le même colis.
- **Non vérifié** (il faudrait remplir un panier) : le port exact à plusieurs cartes, et si le prix de 3,56 €, affiché comme « Special Offer », vaut pour chaque carte du panier.
- Isolement et pistes minimales : 0,15 mm, dans les capacités standard.

## 2. Composants CMS (Mouser)

Fichier : `hardware/fab/bom_mouser_smd.csv`. Sur mouser.fr, va dans **BOM Tool**, importe le fichier et associe la colonne « Manufacturer Part Number ». Les passifs sont commandés par 10.

**Conditionnement : choisis « Cut Tape » (ruban coupé)**, sans frais. Évite « MouseReel », facturé 5 € par ligne.

**Une seule commande Mouser pour les deux boîtes** : les deux nomenclatures partagent des lignes, et les deux ensemble font ≈ 71 € HT. Le port était offert à partir de 75 € lors de la commande d'audio-box : ajoute un potentiomètre et un ampli-op de rechange pour passer le seuil.

| Réf. | Pièce | Réf. fabricant | Prix relevé | Stock |
|---|---|---|---|---|
| U1, U2 | Quadruple ampli-op JFET, SOIC-14 | TI TL074CDR | 0,44 € | 2 675 |
| U3 | Double ampli-op JFET, SOIC-8 | TI TL072CDR | 0,32 € | 110 |
| D1 | Schottky 40 V 1 A, SOD-123 | Diodes 1N5819HW-7-F | **non relevé** | **non relevé** |
| C6, C10, C11 | 100 µF 35 V, 6,3 × 7,7 mm | Nichicon UWT1V101MCL1GS | 0,35 € | 69 324 |
| C… | 0805 : 1 nF et 22 pF C0G, 100 nF X7R, 10 µF X5R | voir CSV | 0,04 à 0,13 € | en stock |
| R… | 0805 1 %, 23 valeurs | Yageo RC0805FR-07… (voir CSV) | ≈ 0,02 € | en stock, sauf ci-dessous |

Sous-total : **≈ 12 € HT**.

**Remplacements faits dans la BOM :**
- **39,2 kΩ et 1,07 kΩ** (R501, R502) : les Yageo sont en rupture. Remplacées par Panasonic **ERJ-6ENF3922V** (relevé : 44 073 en stock) et **ERJ-6ENF1071V** (**stock non relevé**, Mouser a bloqué le relevé). Si l'une manque, toute résistance 0805 à 1 % de la même valeur convient.
- **D1** : la référence B5819W-7-F prévue d'abord n'existe pas chez Mouser. Remplacée par **1N5819HW-7-F**, même boîtier SOD-123, **stock non relevé**. Toute Schottky SOD-123 de 30 V et 0,5 A ou plus convient (par exemple onsemi MBR0540T1G).

## 3. Composants traversants (Mouser)

Également listés dans `hardware/fab/bom_hand_solder.csv`.

| Réf. | Qté | Pièce | Réf. fabricant (Mouser) | € HT | Stock |
|---|---|---|---|---|---|
| RV1–RV5 | 5 | Potentiomètre 20 kΩ linéaire, cran central, canon M9, axe en D 15 mm | Alps RK09L112003P (688-RK09L112003P) | 5 × 2,75 | 761 |
| J1, J2 | 2 | Jack 6,35 mm mono commuté, coudé, avec écrou | Neutrik NMJ4HCD2 (550-12202) | 2 × 1,92 | 8 133 |
| J3 | 1 | Prise DC 5,5 / 2,1 mm coudée | Same Sky PJ-102AH (490-PJ-102AH) | 0,66 | 32 489 |
| PS1 | 1 | DC-DC isolé 12 V → ±12 V, 1 W | Traco TMA 1212D (495-TMA-1212D) | 4,80 | 379 |
| C2, C3, C101–C502 | 12 (+2) | Film 220 nF 63 V 5 %, pas de 5 mm, 7,2 × 2,5 × 6,5 mm | KEMET R82DC3220SH60J (80-R82DC3220SH60J) | 14 × 0,16 | 1 657 |
| D2 | 1 | LED 3 mm rouge faible courant | Kingbright WP710A10LID (604-WP710A10LID) | 0,23 | 21 676 |
| — | 5 | Bouton Ø 11 mm pour axe en D de 6 mm, ABS noir | Same Sky SPK-016A (179-SPK-016A) | 5 × 0,33 | 2 487 |

Sous-total : **≈ 27 € HT**. Délai usine long sur le potentiomètre (21 semaines) : le stock actuel suffit, mais ne tarde pas.

## 4. Mécanique et accessoires (estimations, non relevées)

| Qté | Pièce | ≈ € |
|---|---|---|
| 1 | Bloc secteur 12 V continu régulé, ≥ 300 mA, fiche 5,5 / 2,1 mm, **positif au centre** | 9 |
| 1 | Ruban de cuivre à adhésif conducteur, 25 à 50 mm de large (un rouleau pour les deux boîtes) | 4 |
| 4 | Vis M3 × 14 tête fraisée (ISO 10642) | 1 |
| 4 | Inserts filetés à chaud M3 × 5,7 (le sachet d'audio-box suffit) | — |
| 4 | Patins adhésifs Ø 10 mm | 1 |
| — | Filament PETG ≈ 60 g | 2 |

**Total : ≈ 73 € TTC pour cette boîte.** Détail dans [CHIFFRAGE.md](CHIFFRAGE.md).
