# Modèle de maths : grille 5x5, clusters, globe à multiplicateurs, free spins

Base de calcul pour une slot. Les symboles sont génériques : tu fais ta propre direction artistique par-dessus, les maths ne changent pas.

**Le principe**
- **Grille** : 5 rouleaux × 5 lignes.
- **Clusters** : au moins 5 symboles identiques reliés horizontalement ou verticalement. Le gain dépend de la taille du cluster.
- **Cascades** : les clusters gagnants explosent, les symboles tombent et de nouveaux arrivent, jusqu'à ce qu'il n'y ait plus de gain.
- **Globe** : quand il arrive sur la grille, au départ ou pendant une cascade, ses 8 voisins deviennent des **wilds multiplicateurs**. Le multi d'un cluster est la somme des multis qu'il contient.
- **3 bonus** : 3 symboles bonus = bonus 1, 4 = bonus 2 (plus de globes, multis plus forts), 5 = bonus 3, le **bonus caché** (5 FS, un globe garanti à chaque FS). Pendant les FS, chaque symbole bonus donne **+1 FS**.
- **Spins boostés** : un spin plus cher (1,5x la mise) avec plus de symboles bonus, donc environ 2 fois plus de bonus.
- **Bonus buy** : bonus 1 et bonus 2 (le bonus caché ne s'achète pas).

| Fichier | Rôle |
|---|---|
| `modele_maths.xlsx` | Le classeur : paramètres, paytables, poids, multis, fréquence du bonus en direct, résultats de simulation et résumé du RTP. |
| `simulateur.py` | Le simulateur Monte Carlo. Il lit le classeur, joue des millions de spins et écrit les résultats dans l'onglet **Simulation**. |
| `../stake_math/` | L'export vers le math SDK officiel de Stake Engine, et la génération des fichiers à publier. |

## Utilisation

1. Ouvre le classeur. Modifie seulement les cellules **bleues sur fond jaune** dans *Config* (dont la table des 3 bonus et le prix des spins boostés), *Paytable* (table du bas, pour les clusters), *Poids* (5 blocs : base, boost, bonus 1, 2, 3) et *Multis* (une colonne par bonus).
2. Enregistre, puis lance la simulation (Python 3 avec `numpy` et `openpyxl`) :

   ```bash
   pip install numpy openpyxl
   python simulateur.py modele_maths.xlsx
   # plus rapide pour tester : --spins 300000 --boost 150000 --buy 10000 ; afficher sans écrire : --no-write
   ```

   Ferme le fichier dans Excel avant de lancer, car le script le réécrit. Le jeu est très volatil à cause du globe : compte quelques millions de spins pour un RTP précis à ±2 % (environ 20 minutes pour les valeurs par défaut).

   Le simulateur calcule exactement la loi du nombre de symboles bonus sur la grille de départ, puis simule chaque cas à part (0, 1, … 5 symboles bonus), en jouant beaucoup plus souvent les cas rares qui déclenchent un bonus. Le bonus caché, très rare, est ainsi mesuré précisément. Il joue aussi chaque bonus directement, comme un achat.
3. L'onglet *Résumé* compare le RTP simulé au RTP cible pour le jeu de base et les spins boostés, donne la fréquence et le gain moyen de chaque bonus, le prix conseillé des bonus buy et les indicateurs « 3 étoiles » du SDK.
4. Quand c'est « OK », exporte vers Stake Engine (voir `../stake_math/README.md`).

## Règles (réglables dans *Config*)

**Mode des multiplicateurs**
- `WILD_ADD` (par défaut) : les multis et le globe sont des wilds. Ils relient les symboles d'un cluster.
- `GLOBAL_SUM` : les multis ne sont pas des wilds, et la somme des multis à l'écran multiplie chaque gain.

**Autres règles**
- Cascades : `OUI` ou `NON`.
- Les symboles bonus, les globes et les multis déjà posés ne sont pas recouverts.
- Sur la grille de départ, il y a au plus 1 symbole bonus par rouleau, comme sur les bandes du SDK. Les cascades peuvent en ajouter, et le bonus est choisi d'après la grille finale.
- Bonus avec « globe garanti » : si la grille de départ d'un FS n'a pas de globe, une case au hasard (hors symbole bonus) devient un globe.
- Les modes `LINES` (onglet *Lignes*, paytable 3/4/5 ×) et `WAYS` restent disponibles. Leur paytable a été calée avec d'anciens poids : elle est donc à recaler si tu changes de mode.
- Les valeurs fournies sont des **valeurs de départ calées pour environ 96 %**, à ajuster à ton goût.

## Vérifications faites

Toutes les vérifications passent par `../stake_math/verifier_sdk.py` :
- **Grilles identiques** : sur des grilles aléatoires avec globes, le simulateur donne exactement les mêmes gains et les mêmes cases gagnantes que le math SDK de Stake Engine, dans tous les modes (clusters, lignes, ways).
- **Cascades** : le gain moyen et le taux de spins gagnants du simulateur et du SDK concordent statistiquement.
- **Globe garanti** (bonus caché) : le gain moyen d'un FS concorde statistiquement entre le simulateur et le SDK, et chaque FS du SDK a bien un globe.
