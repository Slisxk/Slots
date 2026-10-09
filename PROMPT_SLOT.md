Je veux créer le front-end d'une slot pour Stake Engine. Les maths sont déjà finies et validées : elles sont décrites dans le fichier `SPEC_MATHS.md` joint. C'est la seule source de vérité sur les règles, la paytable, les multiplicateurs, les free spins et le format des données.

## Ce que je te fournis
- `SPEC_MATHS.md` : la spécification complète. Lis-la entièrement avant de commencer.
- `config_fe_0_0_globe.json` : la config front-end générée par le math SDK (symboles, paytable, bandes d'animation des rouleaux, modes de mise).
- Si je les ai : les fichiers de résultats `books_base.jsonl.zst`, `books_boost.jsonl.zst`, `books_bonus.jsonl.zst` et `books_super.jsonl.zst`, pour tester avec de vrais tours.

## Ce que je veux
Une slot complète, jouable et prête à être publiée sur Stake Engine, avec **ma propre direction artistique**. Les maths ne bougent pas : le front-end ne fait que rejouer les résultats envoyés par le serveur de Stake (les « books »).

## Règles à respecter
1. **Ne modifie jamais les maths** : ni les règles, ni la paytable, ni les multiplicateurs, ni les 3 bonus, ni le nombre de FS, ni les prix (spins boostés 1,25×, achats 59× et 160×), ni le RTP (96,00 %), ni le max win (10 000×). Si quelque chose te semble manquer dans la spec, demande-moi avant d'inventer.
2. **Utilise le web SDK officiel de Stake Engine** : https://github.com/StakeEngine/web-sdk (Svelte 5 + PixiJS 8, Node 22). Pars de son exemple de jeu le plus proche (cascades / clusters) et adapte-le.
3. **Gère chaque événement de la section 7** de la spec, dans l'ordre où ils arrivent. Fais particulièrement attention à :
   - `globeMultipliers`, l'événement propre à ce jeu : animation du globe, puis transformation des 8 cases voisines en wilds multiplicateurs avec leur valeur ;
   - `tumbleBoard` : cascades, avec `explodingSymbols` à dédoublonner ;
   - `freeSpinTrigger` et son champ `bonus` (1, 2 ou 3) : chaque bonus a son intro, son ambiance et son décor. Le 3 est le **bonus caché** : il mérite une vraie révélation (rien ne l'annonce à l'écran avant qu'il tombe), et dans ses free spins chaque grille a un globe garanti, à mettre en scène ;
   - les positions : `row` 0 et 6 sont des symboles de padding hors écran ;
   - les montants : entiers en centièmes de la mise.
4. **Teste avec les exemples réels** de la section 9 de la spec, puis avec les books si je te les donne. Pour chaque cas, le gain affiché doit être exactement égal à `payoutMultiplier`.
5. **Respecte les règles d'approbation de Stake** (section 10 de la spec) :
   - jeu original ;
   - aucun personnage enfantin, rien qui puisse attirer les mineurs ;
   - page de règles claire, avec le RTP (le même dans les 4 modes), le max win et les 3 bonus, bonus caché compris ;
   - bonne qualité visuelle.
6. **Mobile et desktop** : le jeu doit bien fonctionner sur les deux, avec les boutons standards : mise, spin, autoplay, turbo et son, plus :
   - un interrupteur **spins boostés** (mode `boost`, 1,25× la mise par spin, bonus plus fréquents), qui reste activé d'un spin à l'autre et affiche clairement le coût réel du spin ;
   - un menu **bonus buy** avec deux achats : Bonus 1 (mode `bonus`, 59×) et Bonus 2 (mode `super`, 160×), avec confirmation avant l'achat. Le bonus caché ne s'achète pas.

## Comment procéder
1. **Lis la spec**, puis pose-moi tes questions sur la DA : thème, ambiance, palette, style des symboles, ce que représentent le globe, les wilds multiplicateurs et le symbole bonus, l'identité de chacun des 3 bonus (et la révélation du bonus caché), musique et sons. Propose-moi 2 ou 3 directions si je n'ai pas encore d'idée précise.
2. **Installe le web SDK** et fais tourner son exemple en local.
3. **Construis le jeu** étape par étape, et montre-moi le résultat à chaque étape :
   1. grille 5×5 et `reveal` ;
   2. clusters gagnants et cascades ;
   3. globe et multiplicateurs ;
   4. les 3 bonus (intros, free spins, retriggers, globe garanti du bonus caché) ;
   5. interface : spins boostés et les deux bonus buy ;
   6. célébrations des gains (`winLevel`) et écran max win ;
   7. page de règles.
4. **Assets** : si je n'ai pas encore les images et les sons, mets des placeholders propres et nomme les fichiers clairement, pour que je puisse les remplacer facilement.
5. **À la fin**, donne-moi :
   - le build prêt à déposer sur Stake Engine ;
   - la liste des fichiers d'assets à fournir, avec leurs dimensions ;
   - les étapes de publication (front-end + fichiers de maths).

Commence par lire `SPEC_MATHS.md`, puis dis-moi ce que tu as compris du jeu en quelques lignes avant de me poser tes questions sur la DA.
