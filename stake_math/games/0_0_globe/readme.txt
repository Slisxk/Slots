## Globe Multipliers : 5 rouleaux x 5 lignes

Toutes les valeurs (paytable, lignes, bandes, multis, FS, bonus buy) viennent de params.json et
des CSV de reels/, générés par exporter.py depuis la feuille de calcul. Les symboles sont génériques
(H1, H2, H3, M1, L1, L2, L3, BN, GL) : la direction artistique se fait côté front-end.

#### Symboles
* Payants : codes de la Paytable de la feuille (le 1er est le plus fort).
* BN (scatter) : trophée. Au plus 1 par rouleau visible.
* GL (globe) : porte un multi (1x par défaut). Wild en mode WILD_*.
* W (créé par le globe) : wild multiplicateur, n'existe pas sur les bandes.
* MX (créé par le globe, mode GLOBAL_SUM) : multiplicateur non wild.

#### Globe
Quand un globe tombe, ses 8 voisins (sauf trophées et globes) deviennent des multiplicateurs.
Leur valeur est tirée dans mult_values (base / FS). Événement envoyé au front-end juste après le
reveal : "globeMultipliers" (positions des globes et des cases transformées, avec leur multi).

* LINES + WILD_ADD : les multis > 1 des wilds d'une ligne gagnante s'additionnent.
  Une ligne 100 % wild paie comme le symbole le plus fort.
* WAYS + WILD_MULT : les multis des wilds se multiplient d'un rouleau à l'autre.
  Une way doit commencer par le symbole naturel sur le rouleau 1.
* GLOBAL_SUM : les multis ne sont pas wild ; leur somme (globe compris) multiplie
  le gain total du spin.

#### Free spins
3 / 4 / 5 trophées (ou les seuils de la feuille) donnent N free spins. Pendant les FS, chaque
trophée ajoute fs_per_scatter_in_fs FS. Bandes FR0 (plus de globes et de trophées que BR0).

#### Bonus buy (mode "bonus")
Coût buy.cost x la mise, donne buy.spins free spins.

#### Max win
wincap x la mise par tour. La bande FRWCAP (globes x10) sert seulement à fabriquer des
résultats « max win » pour l'optimiseur.
