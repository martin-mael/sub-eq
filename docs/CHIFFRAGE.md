# Chiffrage : 2 Sub EQ, CMS posés par JLCPCB (prix relevés le 2026-11-10)

**≈ 131 € TTC pour 2 boîtes complètes, soit ≈ 65 € par boîte**, blocs secteur compris. Port Mouser non compté : la commande est groupée avec d'autres.

Le détail ligne par ligne est dans [BOM.md](BOM.md), le devis d'assemblage dans [ASSEMBLAGE-JLC.md](ASSEMBLAGE-JLC.md).

## Détail

| Poste | Détail | € HT | € TTC | Source |
|---|---|---|---|---|
| JLCPCB | 5 PCB noirs HASL, 70 CMS posés sur 2 cartes | 21,41 | ≈ 26 | devis relevé |
| JLCPCB, port et taxes | port standard ≈ 9 € HT, TVA, ≈ 2 € de dédouanement | — | ≈ 13 | estimé |
| Mouser, traversants | 10 potentiomètres, 4 jacks, 2 DC-DC, 2 prises DC, 26 condensateurs film, 2 LED, 10 boutons | 50,30 | ≈ 60 | prix relevés |
| Blocs secteur | 2 × 12 V DC régulé, positif au centre | — | ≈ 18 | estimé |
| Mécanique | ruban de cuivre, vis M3, inserts, patins, filament | — | ≈ 14 | estimé |
| **Total** | | | **≈ 131 €** | |

## Hypothèses

- **JLCPCB :** devis relevé sur le site pour 5 PCB dont 2 assemblés, sans rien enregistrer au panier. Le port d'un colis assemblé (≈ 0,47 kg) n'est pas affiché avant l'enregistrement : il est extrapolé des tarifs lus pour des cartes nues.
- **Mouser :** prix unitaires relevés, hors TVA ; les potentiomètres et les boutons sont au tarif par 10. **Port non compté**, la commande étant groupée (il est offert à partir de 75 € HT d'après la commande d'audio-box, non revérifié).
- **Non compté :** outillage, temps de montage, câbles jack.

## Ce qui ne s'achète plus chez Mouser

Les 35 lignes de CMS (résistances, condensateurs céramique et électrolytiques, diode, TL074, TL072) sont fournies et posées par JLCPCB. `hardware/fab/bom_mouser_smd.csv` ne sert que si tu soudes les CMS toi-même.

## Postes les plus lourds

Les 10 potentiomètres à cran central (24,60 € HT), les 2 convertisseurs DC-DC (9,60 €) et les 4 jacks (7,68 €).

## Variante : tout souder à la main, un seul exemplaire

PCB nus (3,56 € HT les 5) et CMS chez Mouser (≈ 12 € HT) : ≈ 73 € TTC pour une boîte, port Mouser non compté.
