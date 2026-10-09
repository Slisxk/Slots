## Globe Multipliers : grille 5 x 5, clusters + cascades, 3 bonus, spins boostés

Toutes les valeurs (paytable, bandes, multis, bonus, prix) viennent de params.json et des CSV
de reels/, générés par exporter.py depuis la feuille de calcul. Les symboles sont génériques
(H1, H2, H3, M1, L1, L2, L3, BN, GL) : la direction artistique se fait côté front-end.

#### Symboles
* Payants : H1 (le plus fort) … L3.
* BN (scatter) : symbole bonus. Au plus 1 par rouleau sur la grille de départ.
* GL (globe) : porte un multi (1x par défaut). Wild en mode WILD_ADD.
* W (créé par le globe) : wild multiplicateur. N'existe pas sur les bandes.
* MX (créé par le globe, mode GLOBAL_SUM) : multiplicateur non wild.

#### Gains (mode cluster, par défaut)
Un cluster = au moins 5 symboles identiques reliés horizontalement ou verticalement ; les wilds
relient les symboles. Le gain dépend de la taille du cluster (paytable de params.json).
Cascades : les cases gagnantes explosent, les symboles tombent, de nouveaux arrivent du haut
de la bande, et on recommence tant qu'il y a un gain (ou jusqu'au max win).

#### Globe
Quand un globe arrive sur la grille (au reveal ou pendant une cascade), ses 8 voisins (sauf
symboles bonus, globes et multis déjà posés) deviennent des multiplicateurs. Leur valeur est
tirée dans les multis du jeu de base ou du bonus en cours. Événement "globeMultipliers" envoyé
juste après le reveal ou le tumbleBoard concerné.

#### Les 3 bonus (params.json["bonuses"])
Le nombre de symboles bonus sur la grille finale (après cascades) choisit le bonus : le plus fort
dont le seuil est atteint.
* Bonus 1 : 3 symboles bonus, bandes FR1, multis du bonus 1.
* Bonus 2 : 4 symboles bonus, bandes FR2 (plus de globes), multis plus forts.
* Bonus 3, caché : 5 symboles bonus ou plus, peu de FS, bandes FR3, et un globe garanti sur
  chaque FS (game_override.ensure_globe : sans globe sur la grille de départ, une case au
  hasard, hors symbole bonus, devient un globe avant le reveal).
Pendant les FS, chaque symbole bonus ajoute fs_per_scatter_in_fs FS. L'événement freeSpinTrigger
porte en plus "bonus": 1, 2 ou 3.

#### Modes de mise
* base (1x) : bandes BR0.
* boost (boost.cost x la mise) : bandes BRB, avec plus de symboles bonus, donc plus de bonus.
* bonus (bonus 1 acheté) et super (bonus 2 acheté) : prix buy_cost de chaque bonus. Le bonus
  caché ne s'achète pas.
Critères des modes base et boost : wincap, bonus1 / bonus2 / bonus3 (grille de départ forcée
avec 3 / 4 / 5 symboles bonus ; le bonus obtenu peut monter avec les cascades), 0, basegame.

#### Poids des résultats
ponderation.py (appelé par run.py) : distribution naturelle du jeu mesurée par la feuille,
RTP exact, limites « 3 étoiles » du SDK respectées.

#### Max win
wincap x la mise par tour : les cascades et les FS s'arrêtent quand il est atteint. La bande
FRWCAP (globes x10) et des multis plus forts servent seulement à fabriquer des résultats
« max win » (critère wincap).
