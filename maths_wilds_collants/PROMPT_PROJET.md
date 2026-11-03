Tu m'aides à créer une slot complète pour Stake Engine, de la direction artistique jusqu'à la publication. Les maths sont déjà faites et validées avec le math SDK officiel de Stake : elles sont dans les fichiers de ce projet. Mes idées pour cette slot sont à la fin de ce texte, sous « Mes idées pour la slot ».

## Les fichiers du projet
- `SPEC_MATHS.md` : la spécification des maths. Elle contient les règles, la paytable, les symboles géants, les wilds collants, les bonus, les événements envoyés par le serveur, des exemples de vrais tours et les règles d'approbation de Stake. **C'est la référence** : lis-la entièrement avant de commencer.
- `config_fe_0_0_wilds.json` : la config front-end générée par le math SDK (symboles, paytable, bandes des rouleaux, modes de mise).
- `README.md` : le résumé du modèle de maths.
- Si je les ajoute : `classeur_maths.xlsx`, `simulateur.py` et `generer_classeur.py` (pour modifier les maths), et les books `books_*.jsonl.zst` (pour tester avec de vrais tours).

## Les maths en bref
| | |
|---|---|
| Grille | 5 rouleaux × 4 lignes, 1 024 ways, gains de gauche à droite |
| Symboles | 4 premiums (H1 à H4), 5 bas (L1 à L5), wild multiplicateur `W` (rouleaux 2 à 5), scatter `S` |
| Symboles géants | Un symbole payant peut occuper 1, 2 ou 3 cases de haut sur un rouleau. Il compte pour chaque case visible |
| Wilds multiplicateurs | x2 ou x3 (x5 rare en bonus 1). Dans une way, les multis de tous les wilds traversés se **multiplient** entre eux |
| Bonus 1 | 3 scatters, 10 free spins, wilds **collants qui avancent** : chaque wild reste et se déplace d'un rouleau vers la gauche à chaque free spin, puis sort par le rouleau 1 |
| Bonus 2 | 4 scatters ou plus, 10 free spins, wilds **collants fixes** : ils restent à leur place jusqu'à la fin du bonus |
| Retrigger | 3 scatters pendant les free spins = +5 free spins |
| Bonus buy | Bonus 1 à 97×, bonus 2 à 465× |
| RTP | 96,20 % dans les 3 modes (spins ≈ 62 %, bonus 1 ≈ 32 %, bonus 2 ≈ 6 %) |
| Max win | 10 000× |

## Ce qui est libre et ce qui touche aux maths
- **Libre** : le thème, l'histoire, le nom du jeu, l'apparence des symboles, les noms des bonus, les animations, les sons et l'interface. Dans les données, les symboles gardent leurs codes (H1, L1, W, S…) : seul leur visuel change.
- **Touche aux maths** : le nombre de free spins, les valeurs des wilds, la taille des symboles géants, le comportement des wilds collants, la taille de la grille, une nouvelle feature, la paytable, les prix d'achat, le max win.
- **Si une de mes idées touche aux maths**, ne l'intègre jamais en silence :
  1. dis-moi ce qu'elle change et propose une version compatible avec les maths actuelles ;
  2. si je veux quand même modifier les maths, donne-moi les cellules à changer dans `classeur_maths.xlsx` et les commandes à relancer (`simulateur.py`, puis la génération Stake). Le mode des wilds de chaque bonus se règle dans l'onglet Config : NON (normaux), FIXE (collants) ou MARCHE (collants qui avancent) ;
  3. pour un réglage fin, préfère la paytable ou les multis des wilds : changer un poids de symbole reconstruit les rouleaux et peut faire bouger un bonus de ±2 % ;
  4. vérifie le résultat :
     - RTP entre 96,0 et 96,5 % dans chaque mode ;
     - tous les contrôles du Résumé au vert ;
     - le même équilibre (environ 2/3 du RTP pour les spins, 1/3 pour les bonus, aucun bonus qui donne tout) ;
  5. mets à jour `SPEC_MATHS.md`.

## Règles à respecter
1. **Les maths sont la seule source de vérité.** Le front-end ne fait que rejouer les résultats envoyés par le serveur de Stake (les « books ») : il ne calcule et n'invente jamais un gain. Si quelque chose manque dans la spec, demande-moi avant d'inventer.
2. **Web SDK officiel de Stake Engine** : https://github.com/engineio/web-sdk (Svelte 5 + PixiJS 8, Node 22). Pars de son exemple de jeu le plus proche (ways) et adapte-le. La doc est sur https://github.com/engineio/docs.
3. **Gère chaque événement de la section 7** de la spec, dans l'ordre où ils arrivent. Fais particulièrement attention à :
   - `giantSymbols` : chaque bloc de 2 ou 3 cases se dessine comme **un seul grand symbole**, qui peut dépasser en haut ou en bas de l'écran ;
   - `stickyWilds` :
     - en bonus 1 (`mode: "MARCHE"`), anime le déplacement des wilds collants d'un rouleau vers la gauche avant l'arrivée des nouveaux ;
     - en bonus 2 (`mode: "FIXE"`), les wilds restent en place ;
     - la valeur du multi de chaque wild doit toujours être bien visible ;
   - `winInfo` : surligne les cases gagnantes, wilds compris, et montre comment les multis des wilds se multiplient ;
   - `freeSpinTrigger` et ses champs `bonus` (1 ou 2) et `wilds` : chaque bonus a son intro et son ambiance ;
   - les positions : `row` 0 et 5 sont des symboles hors écran (lignes visibles 1 à 4) ;
   - les montants : entiers en centièmes de la mise.
4. **Teste avec les exemples réels** de la section 9 de la spec, puis avec les books : le gain affiché doit être exactement égal à `payoutMultiplier`.
5. **Règles d'approbation de Stake** (section 10 de la spec) :
   - jeu original : on peut s'inspirer d'une mécanique (les wilds collants à la Dog House), mais ne copie jamais le nom, les personnages, les images, la musique ou le look d'un jeu existant, même si je cite un jeu dans mes idées ;
   - rien qui attire les mineurs ;
   - une page de règles claire, avec le RTP et le max win de chaque mode et les règles des deux bonus ;
   - une bonne qualité visuelle.
6. **Mobile et desktop**, avec :
   - les boutons standards : mise, spin (barre espace), autoplay avec confirmation, turbo, son ;
   - un menu **bonus buy** avec les deux achats, chacun avec une confirmation ;
   - le mode replay, et le mode social de Stake.us (sans les mots « bet », « buy »…).

## Comment procéder
1. **Lis la spec et mes idées.** Résume-moi en quelques lignes le jeu tel que tu le comprends, et signale ce qui, dans mes idées, touche aux maths.
2. **Direction artistique.** Pose-moi des questions seulement sur ce qui manque dans mes idées : thème, palette, style des symboles et des symboles géants, look des wilds multiplicateurs et de leur déplacement, identité des deux bonus, musique et sons. Si je n'ai pas d'idée précise sur un point, propose-moi 2 ou 3 directions.
3. **Installe le web SDK** et fais tourner son exemple en local.
4. **Construis le jeu étape par étape**, et montre-moi le résultat à chaque étape :
   1. grille 5×4, `reveal` et symboles géants (`giantSymbols`) ;
   2. gains en ways (`winInfo`) avec les wilds multiplicateurs ;
   3. wilds collants, qui avancent (bonus 1) puis fixes (bonus 2) ;
   4. les deux bonus (intros, free spins, retriggers) ;
   5. interface et bonus buy ;
   6. célébrations des gains (`winLevel`) et écran max win ;
   7. page de règles.
5. **Assets** : tant que je n'ai pas les images et les sons, mets des placeholders propres, avec des noms de fichiers clairs pour que je les remplace facilement.
6. **À la fin**, donne-moi :
   - le build prêt à déposer sur Stake Engine ;
   - la liste des assets à fournir, avec leurs dimensions ;
   - les étapes de publication : le front-end, et les fichiers de maths regénérés avec 100 000 tours par mode (`run.py --books 100000`).

## Mes idées pour la slot

