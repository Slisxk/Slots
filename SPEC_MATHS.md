# Spécification maths : slot 5×5 « clusters + globe multiplicateur »

> **À lire en premier (pour la conversation qui construit le jeu)**
> - Ce document décrit des **maths finies et validées** pour une slot publiée sur **Stake Engine**.
> - Le front-end ne calcule rien : il **rejoue les résultats** (« books ») que le serveur de Stake lui envoie.
> - La direction artistique est **entièrement libre**. Les symboles n'ont que des codes (`H1`, `L3`, `GL`…) ; à toi de leur donner un thème, des visuels, des animations et des sons.
> - **Ne change pas** les règles, la paytable, les multiplicateurs ni le nombre de free spins décrits ici : ils sont figés dans les fichiers de maths.
> - Le front-end se construit avec le web SDK officiel : [StakeEngine/web-sdk](https://github.com/StakeEngine/web-sdk) (Svelte 5 + PixiJS 8).

---

## 1. Fiche technique

| Élément | Valeur |
|---|---|
| Grille | 5 rouleaux × 5 lignes (25 cases) |
| Gains | **Clusters** : 5 symboles identiques ou plus, reliés horizontalement ou verticalement (pas en diagonale) |
| Cascades | Oui : les clusters gagnants disparaissent, les symboles tombent, de nouveaux arrivent par le haut, et on recommence tant qu'il y a un gain |
| Feature principale | **Globe** : ses 8 cases voisines deviennent des wilds multiplicateurs |
| Free spins | 3 / 4 / 5+ symboles bonus → 10 / 12 / 15 FS ; pendant les FS, chaque symbole bonus = **+1 FS** |
| Bonus buy | 59 × la mise → 10 free spins |
| RTP | 96,00 % (mode base et mode bonus buy) |
| Max win | **10 000 × la mise** |
| Volatilité | Élevée (écart-type ≈ 24 × la mise par tour) |
| Fréquence de gain | ≈ 30 % des tours |
| Fréquence du bonus | ≈ 1 tour sur 150 |

*(Les chiffres définitifs après optimisation sont en section 8.)*

---

## 2. Symboles

| Code | Rôle | Gain | Conseil visuel |
|---|---|---|---|
| `H1` | Premium 1 | le plus fort | symbole le plus prestigieux du thème |
| `H2` | Premium 2 | fort | |
| `H3` | Premium 3 | fort | |
| `M1` | Moyen | moyen | |
| `L1` | Bas 1 | faible | symboles simples, très lisibles (ils tombent souvent) |
| `L2` | Bas 2 | faible | |
| `L3` | Bas 3 | le plus faible | |
| `BN` | **Bonus (scatter)** | ne paie pas | déclenche les free spins, doit se voir de loin |
| `GL` | **Globe (spécial)** | ne paie pas seul | wild ×1 ; déclenche la transformation de ses voisins |
| `W` | **Wild multiplicateur** | ne paie pas seul | n'existe pas sur les rouleaux : créé par le globe, porte une valeur (×1 à ×50) |

Les symboles bonus `BN`, les globes `GL` et les wilds `W` déjà posés ne sont jamais transformés par un globe.

---

## 3. Règles du jeu (base du texte de la page de règles)

1. **Clusters** : 5 symboles identiques ou plus, qui se touchent horizontalement ou verticalement, forment un cluster gagnant. Le gain dépend de la taille du cluster (section 4).
2. **Wilds** : `GL` et `W` remplacent n'importe quel symbole payant et relient les clusters. Un même wild peut compter dans plusieurs clusters de symboles différents.
3. **Multiplicateur d'un cluster** : c'est la somme des multiplicateurs des wilds du cluster (globe = ×1). Sans wild, il vaut ×1. Par exemple, un cluster qui contient un `W` ×5, un `W` ×3 et le globe est multiplié par 9.
4. **Cascades** : après chaque gain, les cases gagnantes (wilds compris) disparaissent. Les symboles au-dessus tombent et de nouveaux symboles arrivent par le haut. On réévalue les gains et on recommence jusqu'à ce qu'il n'y en ait plus.
5. **Globe** : chaque fois qu'un globe arrive sur la grille (au départ ou pendant une cascade), ses 8 cases voisines deviennent des wilds multiplicateurs `W` avec une valeur tirée au hasard (section 5). Les symboles bonus et les globes ne sont pas transformés.
6. **Free spins** : 3, 4, ou 5 symboles bonus et plus sur la grille, après les cascades, donnent 10, 12 ou 15 free spins. Pendant les free spins, chaque symbole bonus présent à la fin d'un spin ajoute 1 free spin. Les globes y sont plus fréquents et leurs multiplicateurs plus forts.
7. **Bonus buy** : pour 59 × la mise, on obtient directement 10 free spins.
8. **Max win** : le gain d'un tour (spin + free spins) est plafonné à 10 000 × la mise. Quand le plafond est atteint, le tour s'arrête immédiatement.
9. Les gains sont exprimés en multiples de la mise totale. Les mauvais fonctionnements annulent tous les gains et jeux.

---

## 4. Paytable (× la mise totale, par cluster)

| Taille du cluster | 5 | 6 | 7 | 8 | 9–10 | 11–12 | 13–15 | 16–25 |
|---|---|---|---|---|---|---|---|---|
| `H1` | 2,5 | 3,5 | 5 | 7 | 12 | 25 | 60 | 180 |
| `H2` | 1,8 | 2,5 | 3,5 | 5 | 8 | 18 | 40 | 120 |
| `H3` | 1,2 | 1,8 | 2,5 | 3,5 | 6 | 12 | 30 | 90 |
| `M1` | 1 | 1,2 | 1,8 | 2,5 | 5 | 10 | 25 | 60 |
| `L1` | 0,6 | 0,8 | 1,2 | 1,8 | 3,5 | 7 | 18 | 50 |
| `L2` | 0,5 | 0,7 | 1 | 1,5 | 3 | 6 | 15 | 35 |
| `L3` | 0,4 | 0,6 | 0,8 | 1,2 | 2,5 | 5 | 12 | 30 |

Gain d'un cluster = valeur ci-dessus × multiplicateur du cluster.

---

## 5. Multiplicateurs posés par le globe (`W`)

| Valeur | ×1 | ×2 | ×3 | ×4 | ×5 | ×10 | ×20 | ×50 |
|---|---|---|---|---|---|---|---|---|
| Probabilité, jeu de base | 30 % | 40 % | 20 % | 6 % | 3 % | 0,8 % | 0,2 % | — |
| Probabilité, free spins | 15,2 % | 30,5 % | 25,4 % | 12,2 % | 9,1 % | 5,1 % | 2,0 % | 0,5 % |

Le multiplicateur moyen vaut ×2,2 en jeu de base et ×3,6 en free spins.

---

## 6. Modes de mise

| Mode | Coût | Contenu |
|---|---|---|
| `base` | 1 × la mise | spin normal (peut déclencher les free spins) |
| `bonus` | 59 × la mise | bonus buy : 10 free spins directement |

---

## 7. Ce que le front-end reçoit (format Stake Engine)

Chaque tour est un objet JSON (un « book ») envoyé par le serveur RGS de Stake :

```json
{ "id": 123, "payoutMultiplier": 2790, "events": [ ... ] }
```

**Conventions**
- `payoutMultiplier` et tous les montants (`amount`, `win`, `totalWin`) sont des **entiers en centièmes de mise** : `2790` = 27,90 × la mise.
- `board[reel][row]` : `reel` va de 0 à 4, de gauche à droite. `row` va de 0 à 6, de haut en bas, où **0 et 6 sont des symboles de padding hors écran**. Les lignes visibles vont donc de 1 à 5.
- Toutes les positions (`{"reel", "row"}`) des événements utilisent cette même numérotation, padding compris.
- Un symbole s'écrit `{"name": "H1"}`. Les symboles spéciaux portent des attributs en plus, par exemple `{"name": "GL", "wild": true, "multiplier": 1, "globe": true}` ou `{"name": "BN", "scatter": true}`.

**Événements, dans l'ordre où ils arrivent**

| Événement | Quand | Ce que le front-end fait |
|---|---|---|
| `reveal` | début de chaque spin (base ou FS) | affiche la grille (`board`), `gameType` = `basegame` ou `freegame` |
| `globeMultipliers` | juste après un `reveal` ou un `tumbleBoard` qui fait arriver un globe | anime chaque globe, puis transforme les cases de `multipliers` en wilds `W` avec leur valeur |
| `winInfo` | après chaque évaluation gagnante | surligne chaque cluster (`positions`), affiche le gain (`win`) et le multiplicateur du cluster (`meta.clusterMult`) ; `meta.overlay` donne la case où afficher le montant |
| `updateTumbleWin` | après chaque `winInfo` | met à jour le compteur de gains de la cascade |
| `tumbleBoard` | après un gain | fait exploser `explodingSymbols` et tomber les symboles, puis fait arriver `newSymbols` par le haut |
| `setWin` | fin des cascades d'un spin gagnant | affiche le gain du spin (`winLevel` de 1 à 10, pour choisir l'animation de célébration) |
| `setTotalWin` | fin de chaque spin | met à jour le gain total du tour |
| `freeSpinTrigger` | déclenchement des FS | anime les symboles bonus (`positions`), annonce `totalFs` |
| `updateFreeSpin` | début de chaque FS | compteur « FS `amount` / `total` » |
| `freeSpinRetrigger` | un symbole bonus pendant les FS | +1 FS par symbole bonus, `totalFs` mis à jour |
| `freeSpinEnd` | fin des FS | écran récapitulatif (`amount`, `winLevel`) |
| `wincap` | max win atteint | célébration « MAX WIN », le tour s'arrête |
| `finalWin` | fin du tour | gain final (`amount`) |

**Événement propre à ce jeu : `globeMultipliers`**

```json
{
  "type": "globeMultipliers",
  "globes": [{"reel": 2, "row": 3, "multiplier": 1}],
  "multipliers": [
    {"reel": 1, "row": 2, "multiplier": 3, "symbol": "W"},
    {"reel": 2, "row": 2, "multiplier": 2, "symbol": "W"}
  ]
}
```

Le `board` des événements suivants contient déjà les `W` avec leur multiplicateur.

*(Des exemples réels de tours complets sont en section 9.)*

---

## 8. Statistiques

*(Complété à la fin de la génération des fichiers Stake Engine.)*

---

## 9. Exemples réels de tours

*(Complété à la fin de la génération des fichiers Stake Engine.)*

---

## 10. Règles d'approbation Stake Engine à respecter pour la DA

D'après les règles d'approbation de Stake Engine ([stakeengine.org/docs/approval-guidelines](https://stakeengine.org/docs/approval-guidelines)) :
- **Originalité** : le jeu doit être original, sans reprendre le thème, le nom ni les visuels d'un jeu existant.
- **Mineurs** : rien qui puisse attirer les mineurs. Pas d'enfants ni de personnages enfantins, pas de thème scolaire ou enfantin.
- **Contenu** : pas de contenu choquant ou de mauvais goût, et une qualité visuelle suffisante.
- **Jeu sans état** : chaque tour est indépendant, sans jackpot, sans quitte-ou-double ni encaissement anticipé. Les maths respectent déjà cette règle.
- **Page de règles** : le jeu doit avoir une page de règles claire, à partir de la section 3, avec la paytable, le RTP de 96,00 % et le max win de 10 000x.

---

## 11. Fichiers de maths (dans ce repo)

| Fichier | Rôle |
|---|---|
| `modele_maths/modele_maths.xlsx` + `simulateur.py` | Conception et réglage des maths (feuille de calcul + simulateur) |
| `stake_math/games/0_0_globe/` | Le jeu pour le math SDK de Stake Engine (`params.json`, bandes `reels/*.csv`, logique Python) |
| `<math-sdk>/games/0_0_globe/library/publish_files/` | **À déposer sur Stake Engine** : `index.json`, `books_base.jsonl.zst`, `books_bonus.jsonl.zst`, `lookUpTable_base_0.csv`, `lookUpTable_bonus_0.csv` (générés par `run.py`) |
| `<math-sdk>/games/0_0_globe/library/configs/config_fe_0_0_globe.json` | Config pour le front-end : symboles, padding, modes |
