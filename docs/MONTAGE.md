# Impression, montage et mise sous tension

## 1. À contrôler sur les pièces reçues, avant de commander les PCB et d'imprimer

Le PCB et le boîtier reposent sur les plans constructeurs. Les cotes sont en tête de `enclosure/enclosure.py`.

1. **Potentiomètres Alps RK09L112003P** (catalogue Alps RK09L, style 1), vérifiés sur le plan :
   - 3 broches au pas de 2,5 mm, pattes de carcasse 4,1 mm derrière les broches : conforme à l'empreinte.
   - Épaulement du canon M9 × 0,75 à 5 mm devant les broches, axe à 3,5 mm du PCB.
   - **Sens à vérifier au multimètre avant soudure :** axe vers toi, broches en bas, la broche 1 est à gauche. Tourné à fond dans le sens anti-horaire, la résistance entre la broche 1 et la broche centrale doit être ≈ 0 Ω. Si c'est l'inverse, les potentiomètres couperaient dans le sens horaire : préviens-moi avant de souder.
   - **Ergot anti-rotation** (2 × 0,8 mm, à 6 mm de l'axe) : la façade a 4 petites poches autour de chaque trou, il rentre dans l'une d'elles quel que soit son côté.
2. **Jacks Neutrik NMJ4HCD2** (plan ST-NMJ4HCD2), vérifiés : broches T / TN à 16,7 mm du panneau, S / SN à 4 mm, entraxe 16,23 mm, axe à 3,5 mm du PCB, perçage Ø 11,4 mm (11,8 mm imprimé).
3. **Prise DC PJ-102AH**, vérifiée : face de 9,0 × 11,0 mm, axe à 6,5 mm du PCB. Elle traverse le panneau et affleure à l'extérieur. **Contrôle :** broche centrale Ø 2,0 mm, donc fiche 5,5 / 2,1 mm ; au multimètre, la broche arrière (pastille carrée) est bien le contact central.
4. **DC-DC TMA 1212D**, vérifié sur la fiche Traco : SIP-7, broches 1, 2, 4, 5, 6 ; broche 1 (+Vin) sur la pastille carrée.
5. **Condensateurs film 220 nF** : pas de 5 mm, épaisseur ≤ 3 mm (l'empreinte prévoit 2,5 mm, le pas entre deux condensateurs est de 3,7 mm).
6. **Bloc secteur :** 12 V continu régulé, positif au centre, 300 mA ou plus.

## 2. Impression 3D

| Pièce | Orientation | Notes |
|---|---|---|
| `tray.stl` (fond) | à plat, fond sur le plateau | pas de support |
| `lid.stl` (couvercle) | **retourné**, dessus sur le plateau | pas de support ; colonnes vers le haut |
| `back_panel.stl` | à plat, face extérieure vers le haut | textes gravés nets |
| `front_panel.stl` | à plat, face extérieure vers le haut | les poches des ergots sont dessous : ponts de 1,4 mm, sans support |

Réglages conseillés : PETG ou PLA+, buse 0,4, couches 0,2 mm, 3 périmètres, remplissage 20 %.

Imprime **les deux panneaux d'abord** et présente-les sur les pièces reçues avant de lancer le fond et le couvercle. Rainures de 2,75 mm pour des panneaux de 2,5 mm ; si un panneau coince, ponce légèrement ses tranches.

**Inserts :** pose les 4 inserts M3 au fer (≈ 220 °C pour le PETG) dans le bout des colonnes du couvercle.

**Blindage :** tapisse de ruban de cuivre à adhésif conducteur l'intérieur du fond, du couvercle et des deux panneaux, en faisant se chevaucher les bandes. Découpe autour des trous, et laisse 3 mm de plastique nu autour de la prise DC (sa masse n'est pas la masse audio). Soude un fil de 6 cm sur le ruban du fond : il ira sur la pastille SHIELD.

## 3. Soudure des CMS

**Si les CMS sont posés par JLCPCB, saute cette section** : contrôle seulement à la loupe qu'aucune pièce ne manque, puis fais le test de court-circuit en fin de section.

Les repères sont dans `hardware/fab/pcb-top.pdf` : imprime-le à l'échelle 1:1 et coche au fur et à mesure. Fer à 330–350 °C, étain 0,5 mm, flux no-clean, tresse, brucelles, loupe.

**Ordre conseillé :**
1. **U1, U2** (TL074, SOIC-14) et **U3** (TL072, SOIC-8) : point de la broche 1 sur le repère, deux coins opposés d'abord.
2. **D1** (Schottky SOD-123) : **bande = cathode**, comme sur la sérigraphie.
3. Les résistances 0805 **bande par bande**. Toutes sont des valeurs courantes ; certaines fonctions sont faites de deux résistances en série (repères n06, n07, n08), absentes quand une seule suffit :

   | Bande | Entrée : Rn01 (+ Rn06) | Vers la masse : Rn02 (+ Rn07) | Contre-réaction : Rn03 (+ Rn08) | Rn04, Rn05 |
   |---|---|---|---|---|
   | 31 Hz (R1xx) | 100 k | 2,7 k | 200 k | 2 k |
   | 40 Hz (R2xx) | 68 k + 8,2 k | 2,2 k | 150 k + 2,4 k | 2 k |
   | 50 Hz (R3xx) | 47 k + 15 k | 1,5 k + 220 Ω | 100 k + 24 k | 2 k |
   | 63 Hz (R4xx) | 47 k + 3 k | 680 Ω + 680 Ω | 100 k | 2 k |
   | 80 Hz (R5xx) | 27 k + 12 k | 680 Ω + 390 Ω | 68 k + 10 k | 2 k |

   Le filtre subsonique utilise trois résistances de 51 k (R3, R4, R16).

4. Les autres résistances et les condensateurs céramique.
5. Les 3 électrolytiques C6, C10, C11 : **la bande noire marque le « − »**, le « + » est sérigraphié.

**Contrôle au multimètre :** pas de court-circuit entre +12V et GND (sur C10), ni entre −12V et GND (sur C11).

## 4. Soudure des composants traversants

1. Les 12 condensateurs film 220 nF (C2, C3, C101 à C502), non polarisés, plaqués.
2. **PS1** (TMA 1212D), plaqué, broche 1 sur la pastille carrée.
3. **J3** (prise DC), puis **J1, J2** (jacks), bien plaqués et d'équerre avec le bord de carte.
4. **RV1 à RV5** et **D2** (LED : patte courte = cathode = pastille carrée) : **monte d'abord la façade** sur les canons des potentiomètres, écrous serrés à la main, enfile la LED dans son trou, puis soude. Les pièces sont ainsi alignées sur le panneau. Soude aussi les deux pattes de carcasse de chaque potentiomètre : elles le mettent à la masse.
5. Le fil du blindage sur **TP1** (SHIELD).

## 5. Premiers tests (boîtier ouvert)

### Avant de brancher

1. **Isolement :** au multimètre, pas de continuité entre la masse audio (pastille SHIELD) et le corps de la prise DC. Les deux masses sont isolées par le convertisseur.
2. **Courts-circuits :** pas de continuité entre +12V et la masse audio (sur C10), ni entre −12V et la masse audio (sur C11), ni entre les deux broches de la prise DC.

### Première mise sous tension, courant limité

Avec une alimentation de laboratoire : 12 V, limite à 200 mA. Sans alimentation de laboratoire : intercale une résistance de 22 Ω dans le fil « + » du bloc secteur.

La carte doit consommer ≈ 60 mA (valeur estimée), soit moins de 1,5 V aux bornes de la résistance de 22 Ω. Si le courant dépasse 150 mA ou si une pièce chauffe, coupe tout de suite et cherche le court-circuit ou la pièce inversée. Retire ensuite la résistance.

### Tests

Branche le bloc 12 V directement, sans source ni ampli.

1. **Alimentation :** la LED s'allume. Par rapport à la masse audio (pastille SHIELD), mesure **+12 V et −12 V, à ±1 V près**, sur C10 et C11. Si la LED reste éteinte et que rien ne chauffe, la polarité du bloc est inversée (la diode D1 protège).
2. **Offset :** moins de 20 mV continus sur la pointe du jack OUT, potentiomètres au centre.
3. **Signal :** envoie une sinusoïde de 50 Hz à niveau ligne. Potentiomètres au centre, la sortie a le même niveau que l'entrée. Le bouton 50 Hz à fond à droite donne ≈ +12 dB (×4), à fond à gauche ≈ −12 dB (÷4).
4. **Chaque bande :** même essai à 31, 40, 63 et 80 Hz avec le bouton correspondant.
5. **Ronflette :** entrée débranchée, sortie sur un ampli, tous les boutons à fond : pose le couvercle blindé, la ronflette à 50 Hz doit rester inaudible.

## 6. Assemblage du boîtier

1. Façade sur les potentiomètres (écrous M9 serrés modérément) et la LED ; panneau arrière sur les jacks (écrous) et la prise DC.
2. Pose l'ensemble dans le fond : les panneaux glissent dans les rainures, le PCB repose sur les 4 entretoises.
3. Couvercle, puis les 4 vis M3 × 14 fraisées par-dessous.
4. Patins, puis les 5 boutons (13 mm de diamètre au plus).
