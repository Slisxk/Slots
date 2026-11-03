## Sticky Wilds : ways, symboles géants, wilds multiplicateurs collants (style Dog House)

Toutes les valeurs viennent de params.json et des CSV de reels/, générés par exporter.py depuis le
classeur (les bandes sont exactement celles du simulateur). Symboles génériques (H1…H4, L1…L5, W, S).

#### Gains
Ways de gauche à droite (NB_LIGNES ^ NB_ROULEAUX ways). Calcul par Ways du SDK, stratégie « symbol » :
chaque wild compte pour son multi (x2, x3, x5) au lieu de 1, donc les multis de rouleaux différents se
multiplient.

#### Symboles géants
Sur les bandes, chaque symbole payant forme un bloc de 1, 2 ou 3 cases ; deux blocs du même symbole ne se
touchent jamais. Événement "giantSymbols" après le reveal : blocs de 2 ou 3 cases visibles (row = ligne du
haut du bloc, padding compris ; elle peut être 0 ou moins si le bloc commence au-dessus de l'écran).

#### Bonus (params.json["bonuses"])
Le nombre de scatters choisit le bonus. freeSpinTrigger porte "bonus" et "wilds".
* wilds NON : wilds normaux.
* wilds FIXE : chaque wild qui tombe reste à sa place jusqu'à la fin du bonus, avec son multi.
* wilds MARCHE : les wilds collants avancent d'un rouleau vers la gauche au début de chaque free spin,
  puis sortent par le rouleau 1.
Ordre d'un free spin (game_override.draw_board) : les wilds collants avancent (MARCHE), nouvelle grille,
les wilds collants recouvrent la grille, les nouveaux wilds deviennent collants. Événement "stickyWilds".
Retrigger : RETRIG_SCATTERS scatters ou plus = +RETRIG_FS FS. Bonus buy : modes "bonus", "super".

#### Poids des résultats
ponderation.py : probabilités exactes de chaque bonus, fréquence de gain et du max win simulées, RTP exact,
contrôles de risque du math SDK.
