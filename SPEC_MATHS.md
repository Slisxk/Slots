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
| Volatilité | Élevée (écart-type ≈ 8,8 × la mise par tour après optimisation) |
| Fréquence de gain | 30,7 % des tours |
| Fréquence du bonus | 1 tour sur 153 |

*(Le détail est en section 8.)*

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
7. **Bonus buy** : pour 59 × la mise, on obtient directement 10 free spins. Le tour commence par un spin de déclenchement avec 3 symboles bonus, qui peut lui-même gagner (cascades et globes compris).
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
| `tumbleBoard` | après un gain | fait exploser `explodingSymbols` (une case peut y apparaître plusieurs fois si elle était dans plusieurs clusters : dédoublonner) et tomber les symboles, puis fait arriver `newSymbols` par le haut. `newSymbols[reel]` liste les nouveaux symboles de haut en bas, le premier est le nouveau padding du haut |
| `setWin` | fin des cascades d'un spin gagnant | affiche le gain du spin (`winLevel` de 1 à 10, pour choisir l'animation de célébration) |
| `setTotalWin` | fin de chaque spin | met à jour le gain total du tour |
| `freeSpinTrigger` | déclenchement des FS | anime les symboles bonus (`positions`), annonce `totalFs` |
| `updateFreeSpin` | début de chaque FS | compteur de FS : `amount` = nombre de FS déjà joués (0 au premier), `total` = nombre total |
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

Elles sont calculées sur les fichiers publiés (40 000 résultats par mode, après l'optimiseur du math SDK). Pour la publication, il faudra relancer avec 100 000 résultats ou plus par mode.

| | Mode `base` (1×) | Mode `bonus` (59×) |
|---|---|---|
| RTP | **96,00 %** | **96,00 %** |
| Fréquence de gain | 30,7 % des tours | 100 % |
| Gain moyen | 0,96 × la mise | 56,6 × la mise |
| Écart-type | 8,8 × la mise | 81,8 × la mise |
| Max win (10 000×) | ≈ 1 tour sur 10 000 000 | ≈ 1 achat sur 170 000 |

**Mode base, détail**
- Free spins : 1 tour sur 153, environ 26 FS par bonus, 56× la mise en moyenne. Ils pèsent 36,6 % du RTP.
- Jeu de base sans bonus : un gain tous les 3,3 tours, 2× la mise en moyenne. Il pèse 59,4 % du RTP.

**Distribution des gains par tour (% des tours)**

| Gain | Mode base | Mode bonus |
|---|---|---|
| 0 | 69,3 % | 0 % |
| 0–1× | 25,7 % | 1,5 % |
| 1–5× | 1,9 % | 9,3 % |
| 5–20× | 2,3 % | 37,0 % |
| 20–100× | 0,79 % | 28,7 % |
| 100–1 000× | 0,065 % | 23,4 % |
| 1 000–10 000× | 0,0006 % | 0,034 % |
| 10 000× (max win) | 0,00001 % | 0,0006 % |

Pour la célébration des gains, `winLevel` (de 1 à 10) suit les seuils du SDK :
- **par spin** : 1 = moins de 0,1×, 2 = jusqu'à 1×, 3 = 1–2×, 4 = 2–5×, 5 = 5–15×, 6 = 15–30×, 7 = 30–50×, 8 = 50–100×, 9 = 100× jusqu'au max win, 10 = max win ;
- **en fin de FS** : 1 = moins de 1×, 2 = 1–5×, 3 = 5–10×, 4 = 10–20×, 5 = 20–50×, 6 = 50–100×, 7 = 100–500×, 8 = 500–2 000×, 9 = 2 000× jusqu'au max win, 10 = max win.

---

## 9. Exemples réels de tours

Ce sont des extraits réels des fichiers générés.

### 9.1 Globe + cascade : gain de 700,40× (`payoutMultiplier` = 70040)

Le globe tombe sur le rouleau 4 (`reel` 3, `row` 4) et pose 8 wilds multiplicateurs. Trois clusters (`M1`, `H1` et `L1`) partagent ces wilds. Chacun a un multiplicateur ×20 : 5+1+3+2+1+2+4+1 pour les wilds, plus 1 pour le globe. Viennent ensuite deux cascades.

```json
{
  "id": 902, "payoutMultiplier": 70040,
  "events": [
    {"index": 0, "type": "reveal", "board": [[{"name": "L2"}, {"name": "L3"}, {"name": "H2"}, {"name": "L3"}, {"name": "L3"}, {"name": "L2"}, {"name": "H3"}], [{"name": "L1"}, {"name": "M1"}, {"name": "H1"}, {"name": "L1"}, {"name": "L1"}, {"name": "M1"}, {"name": "L1"}], [{"name": "L3"}, {"name": "L2"}, {"name": "L1"}, {"name": "L1"}, {"name": "M1"}, {"name": "M1"}, {"name": "L3"}], [{"name": "L3"}, {"name": "L1"}, {"name": "L1"}, {"name": "H2"}, {"name": "GL", "wild": true, "multiplier": 1, "globe": true}, {"name": "L3"}, {"name": "L3"}], [{"name": "H3"}, {"name": "M1"}, {"name": "H1"}, {"name": "L3"}, {"name": "L2"}, {"name": "L2"}, {"name": "L1"}]], "paddingPositions": [49098, 28607, 58521, 21592, 15687], "gameType": "basegame", "anticipation": [0, 0, 0, 0, 0]},
    {"index": 1, "type": "globeMultipliers", "globes": [{"reel": 3, "row": 4, "multiplier": 1}], "multipliers": [{"reel": 2, "row": 3, "multiplier": 5, "symbol": "W"}, {"reel": 3, "row": 3, "multiplier": 1, "symbol": "W"}, {"reel": 4, "row": 3, "multiplier": 3, "symbol": "W"}, {"reel": 2, "row": 4, "multiplier": 2, "symbol": "W"}, {"reel": 4, "row": 4, "multiplier": 1, "symbol": "W"}, {"reel": 2, "row": 5, "multiplier": 2, "symbol": "W"}, {"reel": 3, "row": 5, "multiplier": 4, "symbol": "W"}, {"reel": 4, "row": 5, "multiplier": 1, "symbol": "W"}]},
    {"index": 2, "type": "winInfo", "totalWin": 70000, "wins": [{"symbol": "M1", "clusterSize": 10, "win": 10000, "positions": [{"reel": 1, "row": 5}, {"reel": 2, "row": 5}, {"reel": 3, "row": 5}, {"reel": 4, "row": 5}, {"reel": 4, "row": 4}, {"reel": 4, "row": 3}, {"reel": 3, "row": 3}, {"reel": 2, "row": 3}, {"reel": 3, "row": 4}, {"reel": 2, "row": 4}], "meta": {"globalMult": 1, "clusterMult": 20, "winWithoutMult": 500, "overlay": {"reel": 3, "row": 4}}}, {"symbol": "H1", "clusterSize": 10, "win": 24000, "positions": [{"reel": 4, "row": 2}, {"reel": 4, "row": 3}, {"reel": 3, "row": 3}, {"reel": 2, "row": 3}, {"reel": 2, "row": 4}, {"reel": 2, "row": 5}, {"reel": 3, "row": 5}, {"reel": 4, "row": 5}, {"reel": 3, "row": 4}, {"reel": 4, "row": 4}], "meta": {"globalMult": 1, "clusterMult": 20, "winWithoutMult": 1200, "overlay": {"reel": 3, "row": 4}}}, {"symbol": "L1", "clusterSize": 14, "win": 36000, "positions": [{"reel": 1, "row": 3}, {"reel": 2, "row": 3}, {"reel": 3, "row": 3}, {"reel": 4, "row": 3}, {"reel": 4, "row": 4}, {"reel": 4, "row": 5}, {"reel": 3, "row": 5}, {"reel": 2, "row": 5}, {"reel": 3, "row": 2}, {"reel": 3, "row": 1}, {"reel": 3, "row": 4}, {"reel": 2, "row": 2}, {"reel": 2, "row": 4}, {"reel": 1, "row": 4}], "meta": {"globalMult": 1, "clusterMult": 20, "winWithoutMult": 1800, "overlay": {"reel": 3, "row": 3}}}]},
    {"index": 3, "type": "updateTumbleWin", "amount": 70000},
    {"index": 4, "type": "tumbleBoard", "newSymbols": [[], [{"name": "H3"}, {"name": "L2"}, {"name": "L3"}], [{"name": "L3"}, {"name": "L2"}, {"name": "L3"}, {"name": "L3"}], [{"name": "L1"}, {"name": "L2"}, {"name": "L3"}, {"name": "M1"}, {"name": "L1"}], [{"name": "L3"}, {"name": "L2"}, {"name": "H2"}, {"name": "L2"}]], "explodingSymbols": [{"reel": 1, "row": 5}, {"reel": 1, "row": 3}, {"reel": 1, "row": 4}, {"reel": 2, "row": 5}, {"reel": 2, "row": 3}, {"reel": 2, "row": 4}, {"reel": 2, "row": 3}, {"reel": 2, "row": 4}, {"reel": 2, "row": 5}, {"reel": 2, "row": 3}, {"reel": 2, "row": 5}, {"reel": 2, "row": 2}, {"reel": 2, "row": 4}, {"reel": 3, "row": 5}, {"reel": 3, "row": 3}, {"reel": 3, "row": 4}, {"reel": 3, "row": 3}, {"reel": 3, "row": 5}, {"reel": 3, "row": 4}, {"reel": 3, "row": 3}, {"reel": 3, "row": 5}, {"reel": 3, "row": 2}, {"reel": 3, "row": 1}, {"reel": 3, "row": 4}, {"reel": 4, "row": 5}, {"reel": 4, "row": 4}, {"reel": 4, "row": 3}, {"reel": 4, "row": 2}, {"reel": 4, "row": 3}, {"reel": 4, "row": 5}, {"reel": 4, "row": 4}, {"reel": 4, "row": 3}, {"reel": 4, "row": 4}, {"reel": 4, "row": 5}]},
    {"index": 5, "type": "winInfo", "totalWin": 40, "wins": [{"symbol": "L3", "clusterSize": 5, "win": 40, "positions": [{"reel": 1, "row": 2}, {"reel": 2, "row": 2}, {"reel": 3, "row": 2}, {"reel": 2, "row": 3}, {"reel": 2, "row": 4}], "meta": {"globalMult": 1, "clusterMult": 1, "winWithoutMult": 40, "overlay": {"reel": 2, "row": 3}}}]},
    {"index": 6, "type": "updateTumbleWin", "amount": 70040},
    {"index": 7, "type": "tumbleBoard", "newSymbols": [[], [{"name": "M1"}], [{"name": "L3"}, {"name": "L1"}, {"name": "L3"}], [{"name": "L3"}], []], "explodingSymbols": [{"reel": 1, "row": 2}, {"reel": 2, "row": 2}, {"reel": 2, "row": 3}, {"reel": 2, "row": 4}, {"reel": 3, "row": 2}]},
    {"index": 8, "type": "setWin", "amount": 70040, "winLevel": 9},
    {"index": 9, "type": "setTotalWin", "amount": 70040},
    {"index": 10, "type": "finalWin", "amount": 70040}
  ]
}
```

### 9.2 Cascade simple sans globe : gain de 3,40×

```json
{
  "id": 7, "payoutMultiplier": 340,
  "events": [
    {"index": 0, "type": "reveal", "board": [[{"name": "L2"}, {"name": "L1"}, {"name": "L1"}, {"name": "H1"}, {"name": "L3"}, {"name": "H1"}, {"name": "BN", "scatter": true}], [{"name": "H1"}, {"name": "H2"}, {"name": "L2"}, {"name": "L2"}, {"name": "L3"}, {"name": "L2"}, {"name": "L3"}], [{"name": "L3"}, {"name": "L2"}, {"name": "L2"}, {"name": "M1"}, {"name": "L2"}, {"name": "L2"}, {"name": "L1"}], [{"name": "L3"}, {"name": "L2"}, {"name": "L2"}, {"name": "L2"}, {"name": "L3"}, {"name": "H3"}, {"name": "L1"}], [{"name": "H1"}, {"name": "H2"}, {"name": "L2"}, {"name": "L2"}, {"name": "H1"}, {"name": "L3"}, {"name": "L2"}]], "paddingPositions": [42199, 55279, 32416, 33005, 40893], "gameType": "basegame", "anticipation": [0, 0, 0, 0, 0]},
    {"index": 1, "type": "winInfo", "totalWin": 300, "wins": [{"symbol": "L2", "clusterSize": 9, "win": 300, "positions": [{"reel": 1, "row": 2}, {"reel": 2, "row": 2}, {"reel": 3, "row": 2}, {"reel": 4, "row": 2}, {"reel": 4, "row": 3}, {"reel": 3, "row": 1}, {"reel": 3, "row": 3}, {"reel": 2, "row": 1}, {"reel": 1, "row": 3}], "meta": {"globalMult": 1, "clusterMult": 1, "winWithoutMult": 300, "overlay": {"reel": 3, "row": 2}}}]},
    {"index": 2, "type": "updateTumbleWin", "amount": 300},
    {"index": 3, "type": "tumbleBoard", "newSymbols": [[], [{"name": "L1"}, {"name": "H2"}], [{"name": "H1"}, {"name": "L3"}], [{"name": "L3"}, {"name": "L1"}, {"name": "L3"}], [{"name": "L3"}, {"name": "H3"}]], "explodingSymbols": [{"reel": 1, "row": 2}, {"reel": 1, "row": 3}, {"reel": 2, "row": 2}, {"reel": 2, "row": 1}, {"reel": 3, "row": 2}, {"reel": 3, "row": 1}, {"reel": 3, "row": 3}, {"reel": 4, "row": 2}, {"reel": 4, "row": 3}]},
    {"index": 4, "type": "winInfo", "totalWin": 40, "wins": [{"symbol": "L3", "clusterSize": 5, "win": 40, "positions": [{"reel": 2, "row": 1}, {"reel": 2, "row": 2}, {"reel": 3, "row": 2}, {"reel": 3, "row": 3}, {"reel": 3, "row": 4}], "meta": {"globalMult": 1, "clusterMult": 1, "winWithoutMult": 40, "overlay": {"reel": 3, "row": 2}}}]},
    {"index": 5, "type": "updateTumbleWin", "amount": 340},
    {"index": 6, "type": "tumbleBoard", "newSymbols": [[], [], [{"name": "H2"}, {"name": "L1"}], [{"name": "L3"}, {"name": "L2"}, {"name": "L3"}], []], "explodingSymbols": [{"reel": 2, "row": 1}, {"reel": 2, "row": 2}, {"reel": 3, "row": 2}, {"reel": 3, "row": 3}, {"reel": 3, "row": 4}]},
    {"index": 7, "type": "setWin", "amount": 340, "winLevel": 4},
    {"index": 8, "type": "setTotalWin", "amount": 340},
    {"index": 9, "type": "finalWin", "amount": 340}
  ]
}
```

### 9.3 Free spins déclenchés : gain de 153,40× (résumé)

```
{"index": 0, "type": "reveal", "board": [[{"name": "L2"}, {"name": "L1"}, {"name": "L3"}, {"name": "L2"}, {"name": "L1"}, {"name": "L2"}, {"name": "L1"}], [{"name": "L3"}, {"name": "H1"}, {"name": "M1"}, {"name": "L2"},  …
{"index": 1, "type": "setTotalWin", "amount": 0}
{"index": 2, "type": "freeSpinTrigger", "totalFs": 10, "positions": [{"reel": 1, "row": 5}, {"reel": 2, "row": 5}, {"reel": 3, "row": 5}]}
{"index": 3, "type": "updateFreeSpin", "amount": 0, "total": 10}
… (10 free spins : updateFreeSpin → reveal → [globeMultipliers] → [winInfo → updateTumbleWin → tumbleBoard …] → [setWin] → setTotalWin → [freeSpinRetrigger]) …
{"index": 31, "type": "freeSpinRetrigger", "totalFs": 11, "positions": [{"reel": 0, "row": 2}]}
{"index": 46, "type": "freeSpinEnd", "amount": 15340, "winLevel": 7}
{"index": 47, "type": "finalWin", "amount": 15340}
```

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
| `stake_math/sortie/config_fe_0_0_globe.json` | Config pour le front-end : symboles, paytable, bandes d'animation des rouleaux, modes (copie de `<math-sdk>/games/0_0_globe/library/configs/`) |
| `stake_math/sortie/statistiques/` | Statistiques détaillées produites par le SDK |
