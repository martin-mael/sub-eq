# Chiffrage (prix relevés le 2026-11-10)

**≈ 73 € TTC pour le Sub EQ**, bloc secteur compris. Avec le DJ Filter commandé en même temps : ≈ 162 € TTC pour les deux boîtes.

## Hypothèses

- **Mouser :** prix relevés le 2026-11-10 par un agent, en lecture seule, sans panier. Ils sont comptés hors TVA (c'est ce qu'affichait le panier d'audio-box), TVA de 20 % ajoutée. **Aucun panier n'a été rempli** : le total est calculé à partir de la nomenclature et des prix unitaires.
- **Port Mouser :** offert à partir de 75 € HT lors de la commande d'audio-box, non revérifié. Les deux boîtes ensemble font ≈ 71 € HT : commande-les ensemble et ajoute une ou deux pièces de rechange.
- **JLCPCB :** panier réel rempli le 2026-11-10 avec les deux cartes : 7,12 € de PCB + 6,98 € de port standard = 14,10 € HT. La TVA n'est pas affichée avant le paiement : avec 20 % et ≈ 2 € de dédouanement, ≈ 19 € TTC, partagés en deux.
- **Non compté :** outillage, temps de montage, câbles jack.

## Détail

| Poste | Détail | € HT | € TTC | Source |
|---|---|---|---|---|
| Mouser, CMS | 31 lignes, passifs par 10 | 12,3 | 14,7 | relevé (1,0 € non relevé) |
| Mouser, traversants | potentiomètres, jacks, DC-DC, films, LED, boutons | 27,1 | 32,6 | relevé |
| JLCPCB | 5 PCB noirs HASL (3,56 € HT) + moitié du port, TVA et dédouanement | — | ≈ 9,5 | panier réel, TVA estimée |
| Bloc secteur 12 V | 12 V DC régulé, positif au centre | — | ≈ 9 | estimé |
| Blindage | moitié d'un rouleau de ruban de cuivre | — | ≈ 4 | estimé |
| Visserie, patins | vis M3, patins (inserts : reste d'audio-box) | — | ≈ 2 | estimé |
| Impression 3D | ≈ 60 g de PETG | — | ≈ 2 | estimé |
| **Total** | | | **≈ 73 €** | |

Postes les plus lourds : les 5 potentiomètres à cran central (13,75 € HT), le DC-DC (4,80 €) et les jacks (3,84 €).

## Pistes d'économie

- **Potentiomètres Bourns PTV09A à cran central** (≈ 0,8 € pièce au lieu de 2,75 €) : −10 €. Mais la version à axe parallèle au PCB n'est pas stockée (12 semaines), et elle n'a pas de canon fileté pour se fixer à la façade.
- **Masse virtuelle au lieu du DC-DC** : −5 €, mais la sortie écrêterait dès +2 dBu en entrée avec 12 dB de boost.
