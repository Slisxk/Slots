# Maths Stake Engine : grille 5x5, clusters + cascades, globe à multiplicateurs, free spins

Ce dossier transforme la feuille de calcul (`../modele_maths/modele_maths.xlsx`) en jeu pour le **math SDK officiel de Stake Engine** ([StakeEngine/math-sdk](https://github.com/StakeEngine/math-sdk)). Le SDK produit les fichiers à déposer sur Stake Engine : books, lookup tables et `index.json`.

Les symboles sont génériques (`H1`…`L3`, `BN` pour le symbole bonus, `GL` pour le globe). Tu peux donc changer la DA côté front-end sans toucher aux maths.

Le principe :
- grille 5x5 ;
- gains en **clusters** : au moins 5 symboles identiques reliés, et les wilds relient ;
- **cascades** ;
- le **globe** transforme ses 8 voisins en wilds multiplicateurs, et le multi d'un cluster est la somme de ses multis ;
- **free spins** : +1 FS par symbole bonus ;
- **bonus buy**.

```
stake_math/
├── exporter.py            feuille de calcul -> params.json + bandes de rouleaux
├── verifier_sdk.py        compare le simulateur de la feuille au SDK (gains exacts + cascades)
├── sortie/                config front-end + statistiques de la dernière génération SDK
└── games/0_0_globe/       le jeu, au format d'un dossier games/ du math SDK
    ├── params.json        (généré) paytable, lignes, multis, FS, bonus buy, cibles RTP
    ├── reels/*.csv        (généré) bandes BR0 (base), FR0 (FS), FRWCAP (max win), PAD_* (animation)
    ├── game_config.py     modes de mise, distributions, symboles spéciaux
    ├── gamestate.py       déroulé d'un tour (base + free spins)
    ├── game_executables.py  transformation autour du globe + calcul des gains
    ├── game_events.py     événement « globeMultipliers » pour le front-end
    ├── game_optimization.py cibles de l'optimiseur
    └── run.py             simulation, optimisation, stats et vérifications
```

## Étapes

1. **Régler la feuille** : modifie les cellules bleues, puis lance `python simulateur.py modele_maths.xlsx` jusqu'à voir « OK » dans le Résumé.
2. **Exporter** :
   ```bash
   python exporter.py ../modele_maths/modele_maths.xlsx --game-id 0_0_globe --nom "Mon Jeu" --studio mon_studio
   ```
   Avec un autre `--game-id`, les fichiers Python sont recopiés dans `games/<game-id>/`.
3. **Installer le math SDK** (Python 3.12+, et Rust/Cargo pour l'optimiseur), à la racine de ce repo, à côté de `stake_math/` :
   ```bash
   git clone https://github.com/StakeEngine/math-sdk.git && cd math-sdk && make setup
   env/bin/pip install openpyxl   # pour verifier_sdk.py
   ```
4. **Copier le jeu** dans le SDK, puis lancer la génération :
   ```bash
   cp -r ../stake_math/games/0_0_globe games/
   env/bin/python ../stake_math/verifier_sdk.py . ../modele_maths/modele_maths.xlsx   # feuille = SDK ?
   env/bin/python games/0_0_globe/run.py --test   # essai rapide (2 000 books/mode)
   env/bin/python games/0_0_globe/run.py          # complet : books + optimisation + stats + checks
   ```
5. **Récupérer les fichiers à publier** dans `games/0_0_globe/library/publish_files/` :
   - `books_*.jsonl.zst` ;
   - `lookUpTable_*_0.csv` ;
   - `index.json`.

   Les stats détaillées sont dans `library/*_full_statistics.xlsx`.

## Ce que le front-end doit gérer

En plus des événements standard du SDK (`reveal`, `winInfo`, `tumbleBoard`, `updateTumbleWin`, `freeSpinTrigger`, `updateFreeSpin`…), le jeu envoie **`globeMultipliers`** juste après chaque `reveal` ou `tumbleBoard` qui fait arriver un globe :

```json
{"type": "globeMultipliers",
 "globes": [{"reel": 1, "row": 3, "multiplier": 1}],
 "multipliers": [{"reel": 0, "row": 2, "multiplier": 8, "symbol": "W"}, ...]}
```

Les lignes sont décalées de +1, à cause des symboles de padding, comme dans les autres événements du SDK. En mode `GLOBAL_SUM`, l'événement porte aussi `boardMultiplier`.

## Modes possibles

Les combinaisons gérées nativement par le SDK, à choisir dans la feuille :

| Mode de gain | Multis | Règle |
|---|---|---|
| CLUSTER (défaut) | WILD_ADD (défaut) | Le multi d'un cluster est la somme des multis de ses wilds, globe 1x compris. |
| CLUSTER | GLOBAL_SUM | La somme des multis à l'écran multiplie chaque gain. |
| LINES | WILD_ADD | Les multis > 1 des wilds d'une ligne s'additionnent. |
| LINES | GLOBAL_SUM | La somme des multis multiplie le gain du spin. |
| WAYS | WILD_MULT | Les multis des wilds se multiplient d'un rouleau à l'autre. |
| WAYS | GLOBAL_SUM | La somme des multis multiplie le gain du spin. |

## Différences avec la feuille

- **Bandes de rouleaux** : le SDK tire sur des bandes, pas case par case.
  - Les poids deviennent des nombres d'occurrences sur la bande.
  - Les symboles bonus sont espacés pour qu'il y en ait au plus 1 par rouleau visible. Le bonus naturel est donc un peu plus rare que dans la feuille, et l'exportateur affiche sa vraie fréquence.
- **Cascades** : dans le SDK, les nouveaux symboles viennent de la bande, au-dessus de la grille. Dans la feuille, ils sont tirés case par case avec les mêmes poids. `verifier_sdk.py` vérifie que les deux donnent statistiquement le même gain moyen et le même taux de spins gagnants.
- **RTP final** : c'est l'optimiseur du SDK qui le fixe en pondérant les books. Il vise le RTP cible, avec la répartition base/FS et la fréquence du bonus mesurées par la feuille. Une feuille calée près de 96 % facilite son travail.
