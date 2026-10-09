# Wild Side School : modèle de maths réutilisable

Ce dossier sert de base pour une slot au même board que *Wild Side School* (Oddspark Studios) :

- grille 5 × 5 ;
- symbole **Globe** : les 8 cases autour de lui deviennent des multiplicateurs ;
- **free spins** déclenchés par les **Trophées**, avec +1 FS par trophée pendant les FS ;
- **bonus buy**.

| Fichier | Rôle |
|---|---|
| `wild_side_school_math.xlsx` | Le classeur : paramètres, paytable, poids, multis, calculs analytiques en direct et résumé du RTP. |
| `simulateur.py` | Le simulateur Monte Carlo. Il lit le classeur, joue des millions de spins et écrit les résultats dans l'onglet **Simulation**. |

## Utilisation

1. Ouvre le classeur. Modifie seulement les cellules **bleues sur fond jaune** dans *Config*, *Paytable*, *Lignes*, *Poids* et *Multis*.
2. *Calc_Gains* et *Calc_Bonus* se mettent à jour tout seuls. Ils donnent :
   - le RTP exact des lignes ou des ways hors globe ;
   - la fréquence du bonus ;
   - le nombre moyen de FS avec retrigger ;
   - la fréquence du globe.
3. Enregistre le classeur, puis lance la simulation (Python 3 avec `numpy` et `openpyxl`) :

   ```bash
   pip install numpy openpyxl
   python simulateur.py wild_side_school_math.xlsx
   # plus rapide pour tester : --spins 300000 --buy 10000 ; afficher sans écrire : --no-write
   ```

   Ferme le fichier dans Excel avant de lancer la simulation, car le script le réécrit.
4. L'onglet *Résumé* compare le RTP simulé au RTP cible. Il affiche aussi le prix conseillé du bonus buy.

Pour une autre slot : renomme les symboles, change les gains et les poids, puis relance le simulateur jusqu'à avoir « OK » dans le *Résumé*.

## Hypothèses (réglables dans *Config*)

Les règles officielles du jeu n'étaient pas accessibles. Le modèle part donc des captures d'écran et ces points restent à vérifier :

- **Mode de gain** : `LINES` (20 lignes par défaut, onglet *Lignes*) ou `WAYS` (3 125 ways).
- **Mode des multiplicateurs** :
  - `WILD_ADD` (par défaut) : les cases multi sont des wilds, et les multis d'une même ligne ou way s'additionnent ;
  - `WILD_MULT` : les multis se multiplient ;
  - `GLOBAL_SUM` : les multis ne sont pas des wilds, et leur somme multiplie le gain total du spin.
- Les trophées et les globes ne sont pas recouverts par les multis.
- En lignes, une ligne 100 % wild paie comme le premier symbole PAY (le Singe). En ways, une way doit commencer par un vrai symbole sur le rouleau 1 : une way 100 % wild ne paie pas (règle du SDK).
- Chaque case suit les poids de son rouleau, avec au plus 1 trophée par rouleau visible, comme sur les bandes du SDK de Stake Engine.
- Les multis ne restent pas d'un spin à l'autre.
- En WILD_ADD, seuls les multis supérieurs à 1x s'additionnent : le globe 1x ne compte pas. C'est la règle du SDK.
- La paytable, les poids et les multis sont des **valeurs de départ calées pour environ 96 %**. Ce ne sont pas les valeurs officielles du jeu.

## Passer sur Stake Engine

Le dossier [`../stake_math`](../stake_math/README.md) exporte cette feuille vers le math SDK officiel de Stake Engine et génère les fichiers à publier. Les règles du simulateur sont alignées sur celles du SDK : sur 20 000 grilles, les gains sont identiques pour les 4 combinaisons de modes.

## Vérifications faites

- Avec le poids du globe à 0, le RTP simulé est égal au RTP analytique de *Calc_Gains*, en lignes comme en ways.
- Sur 20 000 grilles aléatoires avec globes, le simulateur donne exactement les mêmes gains que le math SDK de Stake Engine, pour les 4 combinaisons de modes gérées par le SDK (`../stake_math/verifier_sdk.py`).
