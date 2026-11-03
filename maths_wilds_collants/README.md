# Maths : symboles géants + wilds multiplicateurs collants (style Dog House)

**Ce dossier est celui de ta slot « symboles géants + wilds collants qui bougent ».** L'autre dossier, `maths_multi_rouleaux/`, est celui de la slot à multis de colonne : ne les mélange pas.

RTP visé : **96,2 %** (fourchette acceptée : 96,0 à 96,5 %), équilibré entre les spins et les bonus.

## Le jeu par défaut

| | |
|---|---|
| Grille | 5 rouleaux × 4 lignes, **1 024 ways** (gains de gauche à droite) |
| **Symboles géants** | Sur les rouleaux, chaque symbole payant forme un bloc de **1, 2 ou 3 cases de haut**. Un symbole géant compte pour chaque case visible qu'il occupe : un H1 géant de 3 cases = 3 symboles H1 pour les ways |
| **Wilds multiplicateurs** | Wild `W` (rouleaux 2 à 5) avec un multi **x2, x3** (x5 rare en bonus 1). Dans une way, les multis des wilds se **multiplient** d'un rouleau à l'autre, comme dans Dog House |
| Jeu de base | Peu de wilds, non collants : ≈ 32 % de tours gagnants |
| **Bonus 1 « Free spins »** | 3 scatters, 10 FS, wilds **collants qui bougent** : chaque wild reste et avance d'un rouleau vers la gauche à chaque free spin, puis sort par le rouleau 1 |
| **Bonus 2 « Super free spins »** | 4 scatters ou plus, 10 FS, wilds **collants fixes** : chaque wild reste à sa place jusqu'à la fin du bonus (Dog House) |
| Retrigger | 3 scatters pendant les FS = +5 FS |
| Bonus buy | Bonus 1 à 97x, bonus 2 à 465x (500x au plus pour garder la mise maximale de 1 000 $) |
| Max win | 10 000x |

**L'équilibre**

| Composante | Fréquence | Gain moyen | Part du RTP |
|---|---|---|---|
| Spins (calcul exact) | chaque spin | 0,60x | **≈ 62 %** |
| Bonus 1 (wilds qui bougent) | 1 spin sur 305 | ≈ 93x (médiane ≈ 35x) | **≈ 32 %** |
| Bonus 2 (wilds fixes) | 1 spin sur 7 700 | ≈ 450x (médiane ≈ 84x) | **≈ 6 %** |

## Quel fichier prendre

| Pour… | Fichier |
|---|---|
| Faire le front-end (conversation avec Claude) | `PROMPT_SLOT.md` (à coller) + `SPEC_MATHS.md` + `sortie/config_fe_0_0_wilds.json` (à joindre) |
| Installer et utiliser tout ça sur ton Mac | `INSTALLATION_MAC.md` |
| Régler les maths ou faire une autre slot du même type | `classeur_maths.xlsx` + `simulateur.py` |
| Générer les fichiers à publier sur Stake | `stake/` (voir `INSTALLATION_MAC.md`, étape 3) |

## Les fichiers

| Fichier | Rôle |
|---|---|
| `classeur_maths.xlsx` | Les réglages (cellules bleues) et le tableau de bord : RTP, part des spins et de chaque bonus, prix conseillés, contrôles. |
| `generer_classeur.py` | Regénère le classeur avec les valeurs par défaut ou d'autres valeurs. |
| `simulateur.py` | Construit les bandes (symboles géants), calcule **exactement** le RTP des spins et la fréquence des bonus (toutes les positions des bandes), simule les bonus à wilds collants, vérifie les règles de Stake Engine. Écrit l'onglet Simulation et `rapport_validation.md`. |
| `stake/` | Le jeu pour le math SDK de Stake Engine : `exporter.py`, `verifier_sdk.py`, `games/0_0_wilds/`. |
| `SPEC_MATHS.md`, `PROMPT_SLOT.md` | La spec pour le front-end et le texte à coller dans la conversation qui fait le jeu. |
| `sortie/` | La config front-end et les statistiques du SDK. |

## Utilisation

1. Ouvre `classeur_maths.xlsx` et modifie les cellules bleues : Config (dont les bonus et le mode des wilds NON / FIXE / MARCHE), Paytable, Tailles (symboles géants), Poids, Wilds.
2. Calcule :
   ```bash
   python simulateur.py classeur_maths.xlsx --exact --buy 250000   # ≈ 15 s : spins exacts + bonus simulés, pour caler
   python simulateur.py classeur_maths.xlsx --buy 500000           # ≈ 10 min : simulation complète et contrôles
   ```
3. Exporte vers le math SDK et génère les fichiers à publier : voir `INSTALLATION_MAC.md`.

**À savoir pour régler** : les bandes sont construites au hasard (avec une graine fixe) depuis les poids. Changer un poids reconstruit toute la bande, et le gain d'un bonus peut bouger de ±2 %. Pour un réglage fin du RTP, change plutôt les multis des wilds (onglet Wilds) ou la paytable, qui ne touchent pas aux bandes.

## Les contrôles

Les mêmes que pour l'autre dossier, repris des repos officiels de Stake Engine ([github.com/engineio](https://github.com/engineio), `docs` et `math-sdk`) :
- RTP de chaque mode entre 96,0 et 96,7 % (ta règle : 96,0 à 96,5 %), modes à 0,5 % maximum les uns des autres ;
- au moins 1 tour gagnant sur 20 (cible : 1 sur 3 à 8) ;
- max win plus fréquent que 1 sur 10 000 000 ;
- écart-type du jeu de base ≥ 0,6 ;
- les 6 contrôles de risque du SDK (`RISK_CHECKS`) ;
- gains en multiples de 0,1x ;
- achats à 500x au plus pour la mise maximale de 1 000 $.

Les « étoiles » de Stake (0 à 3) sont une note de qualité donnée par 3 relecteurs : elles ne dépendent pas des maths.
