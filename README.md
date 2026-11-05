# Slots : maths pour Stake Engine

Ce repo contient les **maths de mes slots** pour [Stake Engine](https://github.com/engineio). Elles sont finies, validées avec le math SDK officiel de Stake et prêtes pour le front-end. Les symboles n'ont que des codes (`H1`, `L1`, `W`, `S`…) : la direction artistique est libre, et elle ne change pas les maths.

**Une slot = un dossier.** Prends le dossier de la mécanique que tu veux, et ne mélange pas les dossiers entre eux.

## Les 3 slots

| | **Multis de colonne** | **Wilds collants** | **Globe** (première slot) |
|---|---|---|---|
| Dossier | [`maths_multi_rouleaux/`](maths_multi_rouleaux/) | [`maths_wilds_collants/`](maths_wilds_collants/) | [`modele_maths/`](modele_maths/) + [`stake_math/`](stake_math/), avec `SPEC_MATHS.md` et `PROMPT_SLOT.md` à la racine |
| Grille | 5 × 3, 243 ways | 5 × 4, 1 024 ways | 5 × 5, clusters + cascades |
| Feature | Un multi **x2 à x500** couvre un rouleau entier. Les multis des colonnes traversées s'additionnent | **Symboles géants** (1 à 3 cases de haut) et **wilds multiplicateurs** x2 à x5, dont les multis se multiplient | Le **globe** transforme ses 8 voisins en wilds multiplicateurs |
| Bonus 1 | 3 scatters, 10 FS, multis non collants | 3 scatters, 10 FS, wilds collants qui avancent d'un rouleau à chaque spin | 3 symboles bonus, 10 FS |
| Bonus 2 | 4+ scatters, 10 FS, multis collants qui s'additionnent | 4+ scatters, 10 FS, wilds collants fixes | 4 symboles bonus, 12 FS |
| Autres | Retrigger +5 FS | Retrigger +5 FS | Bonus 3 caché (5 symboles bonus : 5 FS, un globe garanti à chaque FS), spins boostés à 1,25× |
| Bonus buy | 101× et 490× | 97× et 465× | 59× et 160× |
| RTP | 96,20 % (3 modes) | 96,20 % (3 modes) | 96,20 % (4 modes) |
| Max win | 10 000× | 10 000× | 10 000× |

Les deux dernières slots, multis de colonne et wilds collants, ont le même équilibre :
- environ 2/3 du RTP vient des spins ;
- le bonus 1 en donne environ 30 % ;
- le bonus 2 en donne environ 6 %.

## Quel fichier prendre

| Je veux… | Fichier |
|---|---|
| **Faire le front-end et la DA** de la slot Multis de colonne ou Wilds collants, dans un nouveau projet Claude | Le `PROMPT_PROJET.md` du dossier de la slot (tes idées à la fin), avec `SPEC_MATHS.md`, `README.md` et `sortie/config_fe_*.json` du même dossier |
| Faire le front-end de la slot **Globe** | `PROMPT_SLOT.md` + `SPEC_MATHS.md` (à la racine) + `stake_math/sortie/config_fe_0_0_globe.json`. Pour l'installation, voir `modele_maths/README.md` et `stake_math/README.md` |
| **Créer les maths d'une nouvelle slot**, avec les mêmes cibles et les mêmes contrôles | [`PROMPT_NOUVELLES_MATHS.md`](PROMPT_NOUVELLES_MATHS.md) (le board et la feature à remplir) |
| Installer et utiliser les maths sur mon Mac | Le `INSTALLATION_MAC.md` du dossier de la slot |
| Régler les maths ou faire une variante | Le `classeur_maths.xlsx` et le `simulateur.py` du dossier de la slot |
| Générer les fichiers à publier sur Stake | Le dossier `stake/` de la slot (voir `INSTALLATION_MAC.md`) |

## Ce qu'il y a dans chaque dossier de slot

| Fichier | Rôle |
|---|---|
| `README.md` | Le jeu, son équilibre, et quel fichier prendre |
| `classeur_maths.xlsx` | La feuille de maths. Tu règles les cellules bleues, et le Résumé affiche le RTP, la part de chaque bonus, les prix d'achat conseillés et les contrôles en vert ou rouge |
| `generer_classeur.py` | Regénère le classeur avec ses valeurs par défaut |
| `simulateur.py` | Calcule les spins exactement, simule les bonus et vérifie les règles de Stake. Il écrit l'onglet Simulation et `rapport_validation.md` |
| `stake/` | Le jeu au format du math SDK : export, pondération des books, vérification feuille = SDK |
| `sortie/` | La config front-end (`config_fe_*.json`) et les statistiques du SDK |
| `SPEC_MATHS.md` | La spec pour le front-end : règles, paytable, événements, exemples de vrais tours, règles d'approbation |
| `PROMPT_PROJET.md` | Le prompt pour le projet qui fait le front-end |
| `INSTALLATION_MAC.md` | L'installation sur Mac : Python 3.12, math SDK, génération des books |

## Les règles respectées par toutes les slots

Elles viennent du [math SDK](https://github.com/engineio/math-sdk) et de la [doc](https://github.com/engineio/docs) officiels de Stake Engine :
- RTP de chaque mode entre 96,0 et 96,5 % (cible 96,20 %), modes à 0,5 % maximum les uns des autres ;
- au moins 1 tour gagnant sur 20 (les slots tournent à environ 1 sur 3) ;
- max win plus fréquent que 1 tour sur 10 millions ;
- les 6 contrôles de risque du SDK (`RISK_CHECKS`) ;
- mise maximale de 1 000 $, donc des achats à 500× au plus ;
- gains en multiples de 0,1× ;
- la feuille et le jeu SDK donnent les mêmes gains, vérifié par `verifier_sdk.py`.

La méthode (RTP théorique, simulé et des books, puis validation) vient de [Slot-Casino-Game-Developer-Skills-for-Stake-Engine](https://github.com/egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine).

## Avant de publier une slot

1. Regénère les books avec au moins 100 000 tours par mode (`run.py --books 100000`, voir `INSTALLATION_MAC.md`). Ceux du repo ont été générés avec 20 000 tours, pour les tests.
2. Fais un jeu original : on peut reprendre une mécanique, mais jamais le nom, les personnages, les images ou la musique d'un jeu existant.
3. Le front-end se fait avec le [web SDK](https://github.com/engineio/web-sdk) de Stake. Ce repo ne contient que les maths.
