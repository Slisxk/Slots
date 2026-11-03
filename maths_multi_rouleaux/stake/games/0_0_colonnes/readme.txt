## Column Multipliers : ways + multis de colonne, bonus collant ou non

Toutes les valeurs viennent de params.json et des CSV de reels/, générés par exporter.py depuis le
classeur. Symboles génériques (H1…H4, L1…L5, W, S) : la direction artistique se fait côté front-end.

#### Gains
Ways de gauche à droite (NB_LIGNES ^ NB_ROULEAUX ways) : un symbole sur des rouleaux consécutifs à partir
du rouleau 1, le wild W remplace les symboles payants (pas sur le rouleau 1). Calcul par Ways du SDK.

#### Multis de colonne (game_override.draw_column_multipliers)
Après chaque reveal, chaque colonne peut recevoir un multi (x2 à x500) qui couvre tout le rouleau.
Une way est multipliée par la SOMME des multis des colonnes qu'elle traverse (x1 s'il n'y en a aucun) :
game_executables.evaluate_ways. Événement "columnMultipliers" juste après le reveal.
* Jeu de base et bonus non collant : les multis disparaissent après chaque spin.
* Bonus collant : un multi reste sur sa colonne jusqu'à la fin du bonus, et chaque nouveau multi sur
  cette colonne s'ajoute à sa valeur ("columns" donne la valeur cumulée).

#### Bonus (params.json["bonuses"])
Le nombre de scatters choisit le bonus (le plus fort dont le seuil est atteint). freeSpinTrigger porte
"bonus" (1, 2, 3) et "sticky". Retrigger : RETRIG_SCATTERS scatters ou plus = +RETRIG_FS FS.
Bonus buy : un mode par bonus achetable ("bonus", "super"…), au prix buy_cost.

#### Poids des résultats
ponderation.py (appelé par run.py) : probabilités exactes de chaque bonus (classeur), fréquence de gain
simulée, RTP exact, limites « 3 étoiles » du SDK.
