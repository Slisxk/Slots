# Spécification maths : slot 5×5 « clusters + globe multiplicateur + 3 bonus »

> **À lire en premier (pour la conversation qui construit le jeu)**
> - Ce document décrit des **maths finies et validées** pour une slot publiée sur **Stake Engine**.
> - Le front-end ne calcule rien : il **rejoue les résultats** (« books ») que le serveur de Stake lui envoie.
> - La direction artistique est **entièrement libre**. Les symboles n'ont que des codes (`H1`, `L3`, `GL`…) ; à toi de leur donner un thème, des visuels, des animations et des sons.
> - **Ne change pas** les règles, la paytable, les multiplicateurs, les bonus, les prix ni le nombre de free spins décrits ici : ils sont figés dans les fichiers de maths.
> - Le front-end se construit avec le web SDK officiel : [StakeEngine/web-sdk](https://github.com/StakeEngine/web-sdk) (Svelte 5 + PixiJS 8).

---

## 1. Fiche technique

| Élément | Valeur |
|---|---|
| Grille | 5 rouleaux × 5 lignes (25 cases) |
| Gains | **Clusters** : 5 symboles identiques ou plus, reliés horizontalement ou verticalement (pas en diagonale) |
| Cascades | Oui : les clusters gagnants disparaissent, les symboles tombent, de nouveaux arrivent par le haut, et on recommence tant qu'il y a un gain |
| Feature principale | **Globe** : ses 8 cases voisines deviennent des wilds multiplicateurs |
| Bonus | **3 bonus** : 3 symboles bonus → Bonus 1 (10 FS) ; 4 → Bonus 2 « super » (12 FS) ; 5 → Bonus 3, **caché** (5 FS, un globe garanti à chaque FS). Pendant les FS, chaque symbole bonus = **+1 FS** |
| Spins boostés | 1,25 × la mise : bonus environ 1,6 fois plus fréquents (mode `boost`) |
| Bonus buy | Bonus 1 : 59 × la mise ; Bonus 2 : 160 × la mise ; le bonus caché ne s'achète pas |
| RTP | 96,00 % dans les 4 modes (`base`, `boost`, `bonus`, `super`) |
| Max win | **10 000 × la mise** |
| Volatilité | Élevée : écart-type de 25 × la mise par tour en jeu de base ; toutes les limites « 3 étoiles » du SDK sont respectées dans les 4 modes |
| Fréquence de gain | 30,0 % des tours |
| Fréquence des bonus (jeu de base) | Bonus 1 : 1 tour sur 192 ; Bonus 2 : 1 sur 3 300 ; bonus caché : 1 sur 87 000 |

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
| `BN` | **Bonus (scatter)** | ne paie pas | déclenche les bonus (3, 4 ou 5 = bonus 1, 2 ou 3), doit se voir de loin |
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
6. **Les 3 bonus** : le nombre de symboles bonus sur la grille, après les cascades, choisit le bonus :
   - **3 symboles bonus → Bonus 1 « Free spins »** : 10 free spins. Les globes sont plus fréquents qu'en jeu de base et leurs multiplicateurs plus forts.
   - **4 symboles bonus → Bonus 2 « Super free spins »** : 12 free spins, encore plus de globes et des multiplicateurs plus forts (jusqu'à ×100).
   - **5 symboles bonus ou plus → Bonus 3, le bonus caché** : 5 free spins, avec **un globe garanti sur chaque free spin** (s'il n'y en a pas au départ, une case au hasard devient un globe avant que la grille s'affiche). Ses multiplicateurs sont plus petits (×1 à ×5), mais un globe à chaque spin fait de gros gains.
   - Pendant les free spins des 3 bonus, chaque symbole bonus présent à la fin d'un spin ajoute 1 free spin (le bonus ne change pas).
7. **Spins boostés** : pour 1,25 × la mise par spin, les rouleaux ont plus de symboles bonus : les bonus arrivent environ 1,6 fois plus souvent. Tout le reste est identique au jeu de base.
8. **Bonus buy** : Bonus 1 pour 59 × la mise, Bonus 2 pour 160 × la mise. Le tour commence par un spin de déclenchement avec 3 (ou 4) symboles bonus, qui peut lui-même gagner (cascades et globes compris). Le bonus caché ne s'achète pas.
9. **Max win** : le gain d'un tour (spin + free spins) est plafonné à 10 000 × la mise. Quand le plafond est atteint, le tour s'arrête immédiatement.
10. Les gains sont exprimés en multiples de la mise totale. Les mauvais fonctionnements annulent tous les gains et jeux.

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

| Valeur | ×1 | ×2 | ×3 | ×4 | ×5 | ×10 | ×20 | ×50 | ×100 | Moyenne |
|---|---|---|---|---|---|---|---|---|---|---|
| Jeu de base et spins boostés | 30 % | 40 % | 20 % | 6 % | 3 % | 0,8 % | 0,2 % | — | — | ×2,2 |
| Bonus 1 | 15,2 % | 30,5 % | 25,4 % | 12,2 % | 9,1 % | 5,1 % | 2,0 % | 0,5 % | — | ×3,6 |
| Bonus 2 | 6,5 % | 21,6 % | 27,0 % | 17,3 % | 14,0 % | 8,6 % | 3,8 % | 1,1 % | 0,2 % | ×5,1 |
| Bonus 3 (caché) | 50 % | 35 % | 12 % | 2,5 % | 0,5 % | — | — | — | — | ×1,7 |

---

## 6. Modes de mise

| Mode | Coût | Type | Contenu |
|---|---|---|---|
| `base` | 1 × la mise | spin | spin normal (peut déclencher les 3 bonus) |
| `boost` | 1,25 × la mise | spin (option activable, comme une « ante bet ») | spins boostés : bonus environ 1,6 fois plus fréquents |
| `bonus` | 59 × la mise | achat | Bonus 1 « Free spins » directement |
| `super` | 160 × la mise | achat | Bonus 2 « Super free spins » directement |

Le bonus caché ne s'achète pas : il ne se déclenche qu'avec 5 symboles bonus, en mode `base` ou `boost`. Côté interface, `boost` est un interrupteur qui reste activé d'un spin à l'autre ; `bonus` et `super` sont deux boutons d'achat.

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
| `freeSpinTrigger` | déclenchement des FS | anime les symboles bonus (`positions`), annonce `totalFs` ; **`bonus`** (1, 2 ou 3) dit quel bonus démarre : intro, musique et décor propres à chaque bonus, révélation spéciale pour le 3 (caché) |
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

**Champ ajouté à `freeSpinTrigger` : `bonus`**

```json
{"type": "freeSpinTrigger", "totalFs": 5, "bonus": 3,
 "positions": [{"reel": 0, "row": 2}, {"reel": 1, "row": 4}, {"reel": 2, "row": 1}, {"reel": 3, "row": 5}, {"reel": 4, "row": 3}]}
```

Dans le bonus caché, le `board` de chaque `reveal` des free spins contient toujours au moins un `GL` : le front-end n'a rien à calculer, il peut seulement mettre en scène le globe garanti.

*(Des exemples réels de tours complets sont en section 9.)*

---

## 8. Statistiques

Elles sont calculées sur les fichiers générés (20 000 résultats par mode), avec les fonctions de vérification du math SDK. Pour la publication, il faudra relancer avec 100 000 résultats ou plus par mode : les chiffres bougeront un peu, le RTP reste exactement 96,00 %.

**Comment les poids sont calculés.** Les poids des résultats viennent d'une **pondération naturelle** (`ponderation.py`), pas de l'optimiseur Rust du SDK, qui déformait fortement la distribution des gains. Chaque catégorie de résultats (chaque bonus, les gains sans bonus, les tours perdants) garde la probabilité réelle mesurée par la feuille de calcul. Ensuite :
- le RTP est ajusté pour tomber exactement sur 96,00 %, par la plus petite correction possible des gains sans bonus (bruit des résultats) ;
- en bonus buy, les gains de 2 360× et plus (Bonus 1) ou de 6 400× et plus (Bonus 2) sont rendus environ 9 et 6 fois plus rares, pour respecter la limite « 3 étoiles » `etl40b`.

| | `base` (1×) | `boost` (1,25×) | `bonus` (59×) | `super` (160×) |
|---|---|---|---|---|
| RTP | **96,00 %** | **96,00 %** | **96,00 %** | **96,00 %** |
| Gain moyen (× la mise de base) | 0,96 | 1,20 | 56,6 | 153,6 |
| Fréquence de gain | 30,0 % | 29,9 % | 99,9 % | 100 % |
| Écart-type (× la mise) | 25,4 | 30,1 | 225 | 500 |
| Gain médian | 0 | 0 | 7,7× | 10,1× |
| Max win (10 000×) | 1 tour sur 10 000 000 | 1 sur 8 000 000 | 1 achat sur 170 000 | 1 achat sur 41 000 |

**Fréquence et valeur des bonus**

| | `base` | `boost` | Gain moyen du bonus |
|---|---|---|---|
| Bonus 1 « Free spins » (3 symboles bonus) | 1 tour sur 192 | 1 sur 116 | ≈ 56× |
| Bonus 2 « Super free spins » (4) | 1 sur 3 300 | 1 sur 1 660 | ≈ 150× |
| Bonus 3, caché (5) | 1 sur 87 000 | 1 sur 32 000 | ≈ 1 700× |

Le bonus caché paie presque toujours gros (gain médian ≈ 1 600×), car chacun de ses free spins a un globe. Les deux autres bonus sont très « loterie » : la plupart rapportent entre 5× et 20× la mise, et les gros gains viennent des globes.

**Limites « 3 étoiles » du SDK** (`utils/rgs_verification.py`), toutes respectées :

| Critère | Limite | `base` | `boost` | `bonus` | `super` |
|---|---|---|---|---|---|
| `etl40b` (espérance des gains ≥ 40× le coût) | ≤ 0,9 | 0,599 | 0,820 | 0,880 | 0,880 |
| `etl10k` (espérance des gains ≥ 10 000×) | ≤ 0,8 | 0,001 | 0,001 | 0,059 | 0,244 |
| `cvar` (gain moyen des 0,1 % meilleurs tours, en × le coût) | ≤ 800 | 579 | 607 | 43 | 38 |
| `prob5k` / `prob10k` | ≤ 1 % / 0,5 % | ≈ 0 | ≈ 0 | ≈ 0 | 0,1 % / ≈ 0 |
| RTP | ≤ 96,7 % | 96,00 % | 96,00 % | 96,00 % | 96,00 % |

**Distribution des gains par tour (% des tours, gains en × la mise de base)**

| Gain | `base` | `boost` | `bonus` | `super` |
|---|---|---|---|---|
| 0 | 70,0 % | 70,1 % | 0,13 % | 0,04 % |
| 0–1× | 18,0 % | 17,8 % | 0,71 % | 0,27 % |
| 1–5× | 11,1 % | 11,0 % | 25,8 % | 14,8 % |
| 5–20× | 0,75 % | 0,91 % | 61,4 % | 61,7 % |
| 20–100× | 0,049 % | 0,066 % | 4,4 % | 6,8 % |
| 100–1 000× | 0,083 % | 0,110 % | 5,8 % | 11,1 % |
| 1 000–10 000× | 0,019 % | 0,024 % | 1,7 % | 5,3 % |
| 10 000× (max win) | 0,00001 % | 0,00001 % | 0,0006 % | 0,0024 % |

Pour la célébration des gains, `winLevel` (de 1 à 10) suit les seuils du SDK :
- **par spin** : 1 = moins de 0,1×, 2 = jusqu'à 1×, 3 = 1–2×, 4 = 2–5×, 5 = 5–15×, 6 = 15–30×, 7 = 30–50×, 8 = 50–100×, 9 = 100× jusqu'au max win, 10 = max win ;
- **en fin de FS** : 1 = moins de 1×, 2 = 1–5×, 3 = 5–10×, 4 = 10–20×, 5 = 20–50×, 6 = 50–100×, 7 = 100–500×, 8 = 500–2 000×, 9 = 2 000× jusqu'au max win, 10 = max win.

---

## 9. Exemples réels de tours

Ce sont des extraits réels des fichiers générés. Les exemples 9.1 et 9.2 viennent d'une génération précédente (mêmes règles, mêmes événements, bandes différentes) ; 9.3 et 9.4 de la génération actuelle.

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

### 9.3 Bonus 1 déclenché : gain de 186,40× (résumé, `id` 1978 du mode `base`)

```
{"index": 0, "type": "reveal", "board": [[{"name": "L1"}, {"name": "BN", "scatter": true}, {"name": "H3"}, …
{"index": 1, "type": "setTotalWin", "amount": 0}
{"index": 2, "type": "freeSpinTrigger", "totalFs": 10, "positions": [{"reel": 0, "row": 1}, {"reel": 3, "row": 3}, {"reel": 4, "row": 2}], "bonus": 1}
{"index": 3, "type": "updateFreeSpin", "amount": 0, "total": 10}
… (chaque FS : updateFreeSpin → reveal → [globeMultipliers] → [winInfo → updateTumbleWin → tumbleBoard …] → [setWin] → setTotalWin → [freeSpinRetrigger]) …
{"index": 6, "type": "freeSpinRetrigger", "totalFs": 11, "positions": [{"reel": 1, "row": 2}]}
{"index": 17, "type": "freeSpinRetrigger", "totalFs": 13, "positions": [{"reel": 1, "row": 5}, {"reel": 3, "row": 3}]}
… (8 autres retriggers, jusqu'à 22 FS) …
{"index": 121, "type": "freeSpinEnd", "amount": 18640, "winLevel": 7}
{"index": 122, "type": "finalWin", "amount": 18640}
```

### 9.4 Bonus caché : gain de 1 562,70× (résumé, `id` 61 du mode `base`)

5 symboles bonus déclenchent le bonus 3 (`"bonus": 3`). Chaque `reveal` des free spins contient un globe (ici une seule fois par spin), suivi de son `globeMultipliers` (petites valeurs, ×1 à ×4). Deux retriggers portent la session à 7 FS.

```
{"index": 2, "type": "freeSpinTrigger", "totalFs": 5, "positions": [{"reel": 0, "row": 2}, {"reel": 1, "row": 1}, {"reel": 2, "row": 1}, {"reel": 3, "row": 4}, {"reel": 4, "row": 4}], "bonus": 3}
{"index": 3, "type": "updateFreeSpin", "amount": 0, "total": 5}
{"index": 4, "type": "reveal", "gameType": "freegame", …}            globe en (reel 1, row 1)
{"index": 5, "type": "globeMultipliers", …}                          multis 2, 2, 1, 1, 1
{"index": 9, "type": "setWin", "amount": 9040, "winLevel": 8}
… FS 2 et 3 : 8,80× et 42,40× …
{"index": 30, "type": "freeSpinRetrigger", "totalFs": 6, "positions": [{"reel": 1, "row": 2}]}
… FS 4 : 61,10× ; FS 5 : 648,00× ; FS 6 : 88,00× …
{"index": 55, "type": "freeSpinRetrigger", "totalFs": 7, "positions": [{"reel": 1, "row": 5}]}
… FS 7 : 624,00× …
{"index": 64, "type": "freeSpinEnd", "amount": 156270, "winLevel": 8}
{"index": 65, "type": "finalWin", "amount": 156270}
```

---

## 10. Règles d'approbation Stake Engine à respecter pour la DA

D'après les règles d'approbation de Stake Engine ([stakeengine.org/docs/approval-guidelines](https://stakeengine.org/docs/approval-guidelines)) :
- **Originalité** : le jeu doit être original, sans reprendre le thème, le nom ni les visuels d'un jeu existant.
- **Mineurs** : rien qui puisse attirer les mineurs. Pas d'enfants ni de personnages enfantins, pas de thème scolaire ou enfantin.
- **Contenu** : pas de contenu choquant ou de mauvais goût, et une qualité visuelle suffisante.
- **Jeu sans état** : chaque tour est indépendant, sans jackpot, sans quitte-ou-double ni encaissement anticipé. Les maths respectent déjà cette règle.
- **Page de règles** : le jeu doit avoir une page de règles claire, à partir de la section 3, avec la paytable, le RTP de 96,00 % (identique dans les 4 modes : jeu de base, spins boostés et les deux bonus buy), le max win de 10 000x, et la description des 3 bonus.
- **Bonus caché** : « caché » veut dire qu'il n'est pas mis en avant à l'écran (pas de bouton, pas de compteur). Il doit quand même être décrit dans la page de règles (5 symboles bonus, 5 FS, globe garanti) : un joueur doit pouvoir savoir qu'il existe.

---

## 11. Fichiers de maths (dans ce repo)

| Fichier | Rôle |
|---|---|
| `modele_maths/modele_maths.xlsx` + `simulateur.py` | Conception et réglage des maths (feuille de calcul + simulateur) |
| `stake_math/games/0_0_globe/` | Le jeu pour le math SDK de Stake Engine (`params.json`, bandes `reels/*.csv`, logique Python) |
| `<math-sdk>/games/0_0_globe/library/publish_files/` | **À déposer sur Stake Engine** : `index.json`, et pour chacun des 4 modes (`base`, `boost`, `bonus`, `super`) `books_<mode>.jsonl.zst` et `lookUpTable_<mode>_0.csv` (générés par `run.py`) |
| `stake_math/sortie/config_fe_0_0_globe.json` | Config pour le front-end : symboles, paytable, bandes d'animation des rouleaux, les 4 modes et leurs coûts (copie de `<math-sdk>/games/0_0_globe/library/configs/`) |
| `stake_math/sortie/statistiques/` | Statistiques produites par le SDK |
