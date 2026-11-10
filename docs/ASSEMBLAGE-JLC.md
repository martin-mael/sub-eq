# Sub EQ — assemblage des CMS par JLCPCB : devis relevé le 2026-11-10

Expérimentation de prix : faire poser les CMS par JLCPCB au lieu de les souder à la main. Devis réels relevés sur le site (assemblage « Economic », face du dessus, PCB noir, HASL avec plomb), **sans rien enregistrer au panier**. Montants hors TVA et hors port.

Fichiers à envoyer : le zip Gerber, `hardware/jlc/bom_jlc.csv` (avec la référence LCSC de chaque ligne) et `hardware/jlc/cpl_jlc.csv`. Ces deux fichiers sont régénérés par `build.sh` (`hardware/scripts/build_jlc.py`).

## Devis (carte recalculée en valeurs de base)

| Poste | 2 cartes assemblées (5 PCB) | 5 cartes (5 PCB) | 10 cartes (10 PCB) |
|---|---|---|---|
| PCB | 3,56 € | 3,56 € | 4,45 € |
| Mise en route | 7,33 € | 7,33 € | 7,33 € |
| Pochoir | 1,38 € | 1,38 € | 1,38 € |
| Composants (35 lignes) | 2,36 € | 5,74 € | 11,37 € |
| Frais de pièces étendues (2 lignes) | 5,50 € | 5,50 € | 5,50 € |
| Pose et refusion | 1,28 € | 2,10 € | 3,46 € |
| **Total** | **21,41 €** | **25,61 €** | **33,48 €** |
| **Par carte assemblée** | **10,71 €** | **5,12 €** | **3,35 €** |

Les 35 lignes sont placées, chacune avec la référence LCSC de `bom_jlc.csv`, sans substitution ni rupture : 33 pièces « de base », 2 « étendues » (le condensateur 100 µF C970686 et le TL074 C12594).

## Avant / après le recalcul des bandes

La première version de la carte utilisait des résistances en série E96 (97,6 k, 2,74 k…), toutes « étendues » chez JLCPCB : 19 lignes étendues, 49,47 € de frais.

| | Première version | Version recalculée |
|---|---|---|
| 2 cartes assemblées | 67,66 € | **21,41 €** |
| 5 cartes | 71,33 € | **25,61 €** |
| 10 cartes | 78,58 € | **33,48 €** |

Les bandes sont maintenant faites de valeurs du catalogue de base, certaines en série (voir `BAND_PARTS` dans `circuit.py`). La réponse simulée est inchangée, à moins de 1 % près sur les fréquences.

## À noter

- JLCPCB compte 3 condensateurs 100 µF de plus que nécessaire (9 pour 2 cartes) : c'est leur marge de perte à la pose.
- Le site avait présélectionné un délai « 24 hours (PCBA Only) » ; à vérifier au moment de commander.

## Ce que le devis ne couvre pas

- **Les traversants** (potentiomètres, jacks, prise DC, DC-DC, condensateurs film, LED) restent à souder à la main.
- **Le port et la TVA** : le port d'un colis assemblé ne s'affiche qu'après enregistrement au panier. Le poids relevé va de 0,44 à 0,88 kg selon le scénario.
- **Minimum** : 5 PCB, dont 2 assemblés au moins.

## À faire au moment de commander

- Sur la page de correspondance, **vérifier que toutes les lignes sont cochées** : le site en laisse une partie décochée tout en affichant « parts confirmed ».
- Revérifier les stocks : ils bougent d'un jour à l'autre.
