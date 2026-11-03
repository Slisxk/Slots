Je veux créer le front-end d'une slot pour Stake Engine. Les maths sont déjà finies et validées : elles sont décrites dans le fichier `SPEC_MATHS.md` joint. C'est la seule source de vérité sur les règles, la paytable, les symboles géants, les wilds collants, les bonus et le format des données.

## Ce que je te fournis
- `SPEC_MATHS.md` : la spécification complète. Lis-la entièrement avant de commencer.
- `config_fe_0_0_wilds.json` : la config front-end générée par le math SDK (symboles, paytable, bandes d'animation des rouleaux, modes de mise).
- Si je les ai : les fichiers de résultats `books_base.jsonl.zst`, `books_bonus.jsonl.zst` et `books_super.jsonl.zst`, pour tester avec de vrais tours.

## Ce que je veux
Une slot complète, jouable et prête à être publiée sur Stake Engine, avec **ma propre direction artistique**. Les maths ne bougent pas : le front-end ne fait que rejouer les résultats envoyés par le serveur de Stake (les « books »).

## Règles à respecter
1. **Ne modifie jamais les maths** : ni les règles, ni la paytable, ni les multis, ni les bonus, ni les prix (97× et 465×), ni le RTP (96,20 %), ni le max win (10 000×). Si quelque chose te semble manquer dans la spec, demande-moi avant d'inventer.
2. **Utilise le web SDK officiel de Stake Engine** : https://github.com/engineio/web-sdk (Svelte 5 + PixiJS 8, Node 22). Pars de son exemple de jeu le plus proche (ways / lines) et adapte-le. La doc est sur https://github.com/engineio/docs.
3. **Gère chaque événement de la section 7** de la spec, dans l'ordre où ils arrivent. Fais particulièrement attention à :
   - `giantSymbols`, propre à ce jeu : chaque bloc de 2 ou 3 cases se dessine comme **un seul grand symbole** (il peut dépasser en haut ou en bas de l'écran) ;
   - `stickyWilds`, propre à ce jeu : en bonus 1 (`mode: "MARCHE"`), anime le déplacement d'un rouleau vers la gauche des wilds collants avant l'arrivée des nouveaux ; en bonus 2 (`mode: "FIXE"`), les wilds restent en place. La valeur du multi de chaque wild doit être bien visible ;
   - `winInfo` : surligne les cases gagnantes, wilds compris, et montre comment les multis des wilds se multiplient ;
   - `freeSpinTrigger` et ses champs `bonus` (1 ou 2) et `wilds` : chaque bonus a son intro, son ambiance et son décor ;
   - les positions : `row` 0 et 5 sont des symboles de padding hors écran (lignes visibles 1 à 4) ;
   - les montants : entiers en centièmes de la mise.
4. **Teste avec les exemples réels** de la section 9 de la spec, puis avec les books si je te les donne. Pour chaque cas, le gain affiché doit être exactement égal à `payoutMultiplier`.
5. **Respecte les règles d'approbation de Stake** (section 10 de la spec) : jeu original, rien qui attire les mineurs, page de règles claire (avec le RTP et le max win de chaque mode, et les règles des deux bonus), bonne qualité visuelle.
6. **Mobile et desktop**, avec les boutons standards : mise, spin (barre espace), autoplay avec confirmation, turbo, son, et un menu **bonus buy** avec les deux achats (Bonus 1 à 97×, Bonus 2 à 465×), chacun avec une confirmation. Prévois aussi le mode replay et le mode social de Stake.us (pas de mots « bet », « buy »…), décrits dans la doc.

## Comment procéder
1. **Lis la spec**, puis pose-moi tes questions sur la DA : thème, ambiance, palette, style des symboles, le style des symboles géants, à quoi ressemblent les wilds multiplicateurs et leur déplacement, l'identité des deux bonus, musique et sons. Propose-moi 2 ou 3 directions si je n'ai pas encore d'idée précise.
2. **Installe le web SDK** et fais tourner son exemple en local.
3. **Construis le jeu** étape par étape, et montre-moi le résultat à chaque étape :
   1. grille 5×4, `reveal` et symboles géants (`giantSymbols`) ;
   2. gains en ways (`winInfo`) avec les wilds multiplicateurs ;
   3. wilds collants, qui avancent (bonus 1) puis fixes (bonus 2) ;
   4. les deux bonus (intros, free spins, retriggers) ;
   5. interface et bonus buy ;
   6. célébrations des gains (`winLevel`) et écran max win ;
   7. page de règles.
4. **Assets** : si je n'ai pas encore les images et les sons, mets des placeholders propres et nomme les fichiers clairement, pour que je puisse les remplacer facilement.
5. **À la fin**, donne-moi le build prêt à déposer sur Stake Engine, la liste des assets à fournir (avec leurs dimensions) et les étapes de publication (front-end + fichiers de maths).

Commence par lire `SPEC_MATHS.md`, puis dis-moi ce que tu as compris du jeu en quelques lignes avant de me poser tes questions sur la DA.
