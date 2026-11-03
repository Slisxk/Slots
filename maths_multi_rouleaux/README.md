# Maths réutilisables : ways + multis de colonne (x2 à x500), bonus collant ou non

Un modèle de maths pour tes futures slots, réglé par défaut sur **96,2 % de RTP** (fourchette acceptée : 96,0 à 96,5 %). Il est **équilibré** : les spins rapportent, chaque bonus rapporte, et aucun ne donne tout.

## Le jeu par défaut

| | |
|---|---|
| Grille | 5 rouleaux × 3 lignes, **243 ways** (format le plus courant chez Pragmatic Play) |
| Gains | Ways de gauche à droite. Wild `W` (pas sur le rouleau 1), scatter `S` (au plus 1 par rouleau) |
| **Multi de colonne** | Un multi de **x2 à x500** tombe sur un rouleau entier, de haut en bas. Une way est multipliée par la **somme** des multis des colonnes qu'elle traverse, comme les multis additionnés de Gates of Olympus. |
| Jeu de base | Multis rares (1,5 % par colonne et par spin, environ 1 spin sur 14 en a un), surtout x2 à x5 : ça donne envie de spinner sans trop donner |
| **Bonus 1 « Free spins »** | 3 scatters, 10 FS, multis **non collants** (ils disparaissent après chaque spin), 31 % par colonne et par spin |
| **Bonus 2 « Super free spins »** | 4 scatters ou plus, 10 FS, multis **collants** : un multi reste sur sa colonne jusqu'à la fin du bonus, et chaque nouveau multi sur cette colonne s'ajoute à sa valeur |
| Retrigger | 3 scatters pendant les FS = +5 FS (environ 1 session sur 16) |
| Bonus buy | Bonus 1 à 101x la mise (mode `bonus`), bonus 2 à 568x (mode `super`) |
| Max win | 10 000x |

**L'équilibre, d'après le calcul exact**

| Composante | Fréquence | Gain moyen | Part du RTP |
|---|---|---|---|
| Spins (multis compris) | chaque spin | 0,61x | **64 %** |
| Bonus 1 (non collant) | 1 spin sur 334 | ≈ 96x (médiane ≈ 43x) | **30 %** |
| Bonus 2 (collant) | 1 spin sur 8 700 | ≈ 546x | **7 %** |
| **Total** | | | **96,18 %** |

Simulation de 2 millions de spins : 30,4 % de tours gagnants (1 sur 3,3), écart-type de 19x, max win 1 tour sur 2,5 millions.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `classeur_maths.xlsx` | La feuille de maths. Le **RTP exact** est calculé en formules, en direct : spins, chaque bonus, multis collants ou non, retriggers. Le Résumé montre l'équilibre et les contrôles. |
| `generer_classeur.py` | Regénère le classeur avec les valeurs par défaut, ou d'autres valeurs (`python generer_classeur.py autre.xlsx "ACT_FS=(0.3,0.2,0.2)"`). |
| `simulateur.py` | Calcul exact + simulation Monte Carlo : vérifie les formules, mesure la volatilité, le max win et les contrôles de risque du math SDK. Écrit l'onglet Simulation et `rapport_validation.md`. |
| `rapport_validation.md` | Rapport de validation, au format du « Math Sign-Off Template » du repo de skills. |
| `stake/` | Le jeu pour le math SDK de Stake Engine : `exporter.py`, `verifier_sdk.py`, `games/0_0_colonnes/`. |

## Utilisation

1. **Régler la slot.** Ouvre `classeur_maths.xlsx` et modifie seulement les cellules bleues sur fond jaune : Config, Paytable, Poids, Multis. Le **Résumé** se recalcule tout de suite : RTP exact, part des spins et de chaque bonus, prix conseillé des achats, contrôles OK / ÉCHEC.
2. **Simuler** (Python 3 avec `numpy` et `openpyxl`) :
   ```bash
   python simulateur.py classeur_maths.xlsx             # 2M de spins + 100 000 tours par bonus (≈ 5 min)
   python simulateur.py classeur_maths.xlsx --exact     # calcul exact seulement, instantané
   python simulateur.py classeur_maths.xlsx --spins 20000000   # validation finale (≥ 20M conseillés)
   ```
3. **Exporter vers le SDK** et générer les fichiers à publier (Python 3.12+, [math SDK officiel](https://github.com/engineio/math-sdk) cloné à côté) :
   ```bash
   python stake/exporter.py classeur_maths.xlsx --game-id 0_0_colonnes --nom "Mon Jeu"
   cp -r stake/games/0_0_colonnes <math-sdk>/games/
   <math-sdk>/env/bin/python stake/verifier_sdk.py <math-sdk> classeur_maths.xlsx   # SDK = classeur ?
   cd <math-sdk> && env/bin/python games/0_0_colonnes/run.py --books 100000
   ```
   Les fichiers à déposer sont dans `<math-sdk>/games/0_0_colonnes/library/publish_files/`.

**Pour une autre slot** : change la grille (3 à 6 rouleaux, 2 à 6 lignes), les symboles, la paytable, les poids, les valeurs et les probabilités des multis, et jusqu'à 3 bonus (scatters, FS, collant ou non, prix). Tout se recalcule.

## Les contrôles

Les règles viennent des repos officiels de Stake Engine ([github.com/engineio](https://github.com/engineio) : `docs` et `math-sdk`, version de novembre 2026). La méthode vient du repo [Slot & Casino Game Developer Skills for Stake Engine](https://github.com/egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine).

| Règle | Source | Où |
|---|---|---|
| RTP entre 96,0 et 96,5 % | ta règle (le math SDK refuse hors de 96,0–96,7 %, pour chaque mode) | Résumé |
| Tous les modes à 0,5 % maximum du jeu de base | doc « Math Requirements » + FAQ | Résumé |
| 1 tour gagnant sur 3 à 8, jamais moins de 1 sur 20 | checklist d'approbation + doc | Résumé / Simulation |
| Max win plus fréquent que 1 sur 10 000 000 ; 1 000 000x au plus | doc « Math Requirements » + math SDK | Simulation |
| Écart-type du jeu de base ≥ 0,6 ; un mode à 1x | math SDK (soumission) | Simulation |
| **Contrôles de risque** : écart-type / coût ≤ 60 ; cvar ≤ 700 ; part du RTP venant des gains ≥ 40x le coût ≤ 0,9 et ≥ 10 000x ≤ 0,8 ; gains ≥ 5 000x ≤ 5 % | math SDK (`RISK_CHECKS`) : chaque contrôle raté baisse la mise maximale autorisée | Simulation, SDK |
| 100 000 à 1 000 000 de résultats par mode dans les books | doc « Math Requirements » | `run.py --books` |
| RTP théorique = simulé = mesuré sur les books | repo de skills | Simulation, `verifier_sdk.py`, SDK |
| Équilibre : spins entre 55 et 70 % du RTP, aucun bonus au-dessus de 35 % | ta demande | Résumé |

Les « étoiles » de Stake (0 à 3) sont une note de qualité donnée par 3 relecteurs (créativité, finition) : elles ne dépendent pas des maths. Il faut au moins 1 étoile pour être publié.

## Points de conception

- **Somme, pas produit.** Avec des multis jusqu'à x500, multiplier les colonnes entre elles ferait exploser les gains (x100 × x100). La somme garde des gros multis sans donner trop. Elle permet aussi un calcul exact simple en formules, valable pour les multis collants comme non collants.
- **5 × 3 plutôt que 5 × 4.** Avec 4 lignes (1 024 ways), presque 1 spin sur 2 gagne : c'est hors de la règle « 1 sur 3 à 8 » et ça dilue les gains. Avec 243 ways, on est à 30 %.
- **Peu de wilds en jeu de base, plus en bonus** : les spins restent sobres et les bonus généreux.
- **Les deux bonus sont achetables sans rien déformer.** Le math SDK rapporte ses contrôles de risque au prix du mode : les achats du bonus 1 (101x) et du bonus 2 (568x) les passent naturellement.
- **Super Scatter de Gates of Olympus** (gains instantanés de 5 000x) : non inclus. Il ajouterait beaucoup de gains ≥ 5 000x et pèserait sur les contrôles de risque du jeu de base.

Les ordres de grandeur s'inspirent des slots Pragmatic Play à succès : 5 × 3, bonus vers 1 spin sur 300 à 400, achat autour de 100x, 30 % de tours gagnants, multis additionnés. Ce ne sont pas des copies de leurs maths, qui ne sont pas publiques.
