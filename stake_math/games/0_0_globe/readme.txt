## Globe Multipliers : grille 5 x 5, clusters + cascades

Toutes les valeurs (paytable, bandes, multis, FS, bonus buy) viennent de params.json et des CSV
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
tirée dans mult_values (base / FS). Événement "globeMultipliers" envoyé juste après le reveal
ou le tumbleBoard concerné.

* WILD_ADD : multi d'un cluster = somme des multis des wilds qu'il contient (globe compris).
* GLOBAL_SUM : les multis ne sont pas wild ; leur somme (globe compris) multiplie chaque gain.
(Les modes lines / ways restent possibles : voir le README du dossier stake_math.)

#### Free spins
3 / 4 / 5+ symboles bonus sur la grille finale (après cascades) donnent N free spins. Pendant les
FS, chaque symbole bonus ajoute fs_per_scatter_in_fs FS. Bandes FR0 (plus de globes que BR0).

#### Bonus buy (mode "bonus")
Coût buy.cost x la mise, donne buy.spins free spins.

#### Max win
wincap x la mise par tour : les cascades et les FS s'arrêtent quand il est atteint. La bande
FRWCAP (globes x10) sert seulement à fabriquer des résultats « max win » pour l'optimiseur.
