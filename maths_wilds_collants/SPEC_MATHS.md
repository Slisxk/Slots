# Spécification maths : slot 5×4 ways « symboles géants + wilds multiplicateurs collants »

> **À lire en premier (pour la conversation qui construit le jeu)**
> - Ce document décrit des **maths finies et validées** pour une slot publiée sur **Stake Engine**.
> - Le front-end ne calcule rien : il **rejoue les résultats** (« books ») que le serveur de Stake lui envoie.
> - La direction artistique est **entièrement libre**. Les symboles n'ont que des codes (`H1`, `L3`, `W`, `S`…) ; à toi de leur donner un thème, des visuels, des animations et des sons.
> - **Ne change pas** les règles, la paytable, les multis, les bonus ni les prix décrits ici : ils sont figés dans les fichiers de maths.
> - Le front-end se construit avec le web SDK officiel : [engineio/web-sdk](https://github.com/engineio/web-sdk) (Svelte 5 + PixiJS 8).

---

## 1. Fiche technique

| Élément | Valeur |
|---|---|
| Grille | 5 rouleaux × 4 lignes, **1 024 ways** |
| Gains | Ways de gauche à droite : le même symbole sur des rouleaux consécutifs à partir du rouleau 1 (3, 4 ou 5 rouleaux) |
| **Symboles géants** | Les symboles payants arrivent en blocs de **1, 2 ou 3 cases de haut** sur un rouleau |
| **Wilds multiplicateurs** | Wild `W` (rouleaux 2 à 5) avec un multi x2, x3 ou x5 ; les multis se **multiplient** d'un rouleau à l'autre |
| Bonus 1 « Free spins » | 3 scatters → 10 free spins, wilds **collants qui avancent** d'un rouleau vers la gauche à chaque spin |
| Bonus 2 « Super free spins » | 4 ou 5 scatters → 10 free spins, wilds **collants fixes** jusqu'à la fin du bonus |
| Retrigger | 3 scatters ou plus pendant les free spins → +5 free spins |
| Bonus buy | Bonus 1 : 97 × la mise · Bonus 2 : 465 × la mise |
| RTP | 96,20 % dans les 3 modes |
| Max win | **10 000 × la mise** |
| Fréquence de gain | 32,2 % des tours (1 sur 3,1) |

*(Les statistiques détaillées sont en section 8.)*

---

## 2. Symboles

| Code | Rôle | Conseil visuel |
|---|---|---|
| `H1` | Premium 1, le plus fort | symbole le plus prestigieux du thème |
| `H2`, `H3`, `H4` | Premiums | |
| `L1` … `L5` | Bas (équivalents A, K, Q, J, 10) | simples et très lisibles |
| `W` | **Wild multiplicateur** (x2, x3, x5) : remplace les symboles payants, jamais sur le rouleau 1 au départ | la valeur du multi doit être bien visible |
| `S` | **Scatter** : déclenche les bonus. Au plus 1 par rouleau | doit se voir de loin |

**Symboles géants** : chaque symbole payant peut occuper 1, 2 ou 3 cases verticales d'un même rouleau. Dessine-le comme **un seul grand symbole** (illustration étirée sur 2 ou 3 cases), pas comme plusieurs petits. Un géant peut dépasser en haut ou en bas de l'écran : on n'en voit alors qu'une partie.

| Symboles | 1 case | 2 cases | 3 cases |
|---|---|---|---|
| `H1` à `H4` | 50 % des blocs | 30 % | 20 % |
| `L1` à `L5` | 60 % | 25 % | 15 % |

---

## 3. Règles du jeu (base du texte de la page de règles)

1. **Ways** : un gain se forme avec au moins 3 symboles identiques sur des rouleaux consécutifs, en partant du rouleau le plus à gauche, quelle que soit leur ligne. Chaque case compte : un symbole géant de 3 cases compte pour 3. Nombre de ways = produit du nombre de symboles qui comptent sur chaque rouleau. Gain = valeur de la paytable × nombre de ways.
2. **Wild multiplicateur** : `W` remplace tous les symboles payants. Il porte un multi (x2, x3 ou x5) : dans le calcul des ways, il compte pour sa valeur au lieu de 1. Les multis de rouleaux différents se multiplient donc entre eux. Exemple : H1 sur les rouleaux 1, 2, 3, avec un wild x2 au rouleau 2 et un wild x3 au rouleau 3 = 0,8 × 2 × 3 = 4,8 × la mise.
3. **Bonus 1 « Free spins »** : 3 scatters = 10 free spins. Chaque wild qui tombe devient **collant** et, au début de chaque free spin suivant, **avance d'un rouleau vers la gauche**, en gardant son multi. Arrivé au rouleau 1, il sort au spin suivant.
4. **Bonus 2 « Super free spins »** : 4 ou 5 scatters = 10 free spins. Chaque wild qui tombe devient **collant** et **reste à sa place** jusqu'à la fin du bonus, avec son multi.
5. Pendant les free spins, les wilds collants recouvrent ce qui arrive sous eux (y compris un scatter).
6. **Retrigger** : pendant les free spins des deux bonus, 3 scatters ou plus = +5 free spins.
7. **Bonus buy** : Bonus 1 pour 97 × la mise, Bonus 2 pour 465 × la mise. Le tour commence par un spin de déclenchement avec 3 (ou 4) scatters, qui peut lui-même gagner.
8. **Max win** : le gain d'un tour (spin + free spins) est plafonné à 10 000 × la mise. Quand le plafond est atteint, le tour s'arrête.
9. Les gains sont exprimés en multiples de la mise totale. Les mauvais fonctionnements annulent tous les gains et jeux.

---

## 4. Paytable (× la mise totale, par way)

| Symbole | 3 rouleaux | 4 rouleaux | 5 rouleaux |
|---|---|---|---|
| `H1` | 0,8 | 2 | 8 |
| `H2` | 0,6 | 1,7 | 4,8 |
| `H3` | 0,4 | 1,2 | 3,2 |
| `H4` | 0,3 | 0,8 | 2 |
| `L1` | 0,2 | 0,6 | 1,2 |
| `L2` | 0,2 | 0,4 | 0,8 |
| `L3` | 0,2 | 0,3 | 0,6 |
| `L4` | 0,1 | 0,2 | 0,6 |
| `L5` | 0,1 | 0,2 | 0,6 |

Gain affiché = valeur × nombre de ways (où chaque wild compte pour son multi).

---

## 5. Wilds

**Fréquence** : les wilds sont rares en jeu de base (environ 0,3 % des cases des rouleaux 2 à 5), plus fréquents en free spins (environ 2,3 % des cases au bonus 1, 1,9 % au bonus 2).

**Multis**

| | x2 | x3 | x5 | Moyenne |
|---|---|---|---|---|
| Jeu de base | 70 % | 30 % | — | x2,3 |
| Bonus 1 (collants qui avancent) | 60,5 % | 35 % | 4,5 % | x2,5 |
| Bonus 2 (collants fixes) | 70 % | 30 % | — | x2,3 |

---

## 6. Modes de mise

| Mode | Coût | Type | Contenu |
|---|---|---|---|
| `base` | 1 × la mise | spin | spin normal (peut déclencher les deux bonus) |
| `bonus` | 97 × la mise | achat | Bonus 1 « Free spins » directement |
| `super` | 465 × la mise | achat | Bonus 2 « Super free spins » directement |

Les deux achats coûtent plus de 2 × la mise : la règle Stake impose une **confirmation** avant l'achat.

---

## 7. Ce que le front-end reçoit (format Stake Engine)

Chaque tour est un objet JSON (un « book ») :

```json
{ "id": 12, "payoutMultiplier": 480, "events": [ ... ] }
```

**Conventions**
- `payoutMultiplier` et tous les montants sont des **entiers en centièmes de mise** (`480` = 4,80 × la mise), toujours des multiples de 10.
- `board[reel][row]` : `reel` de 0 à 4 ; `row` de 0 à 5, où **0 et 5 sont des symboles de padding hors écran**. Les lignes visibles sont 1 à 4.
- Toutes les positions `{"reel", "row"}` utilisent cette numérotation, padding compris.
- Un wild s'écrit `{"name": "W", "wild": true, "multiplier": 3}`.

**Événements, dans l'ordre où ils arrivent**

| Événement | Quand | Ce que le front-end fait |
|---|---|---|
| `reveal` | début de chaque spin | affiche la grille (`board`). En free spins, la grille contient déjà les wilds collants à leur nouvelle place |
| `giantSymbols` | juste après le `reveal`, s'il y a des symboles géants | dessine chaque bloc `{"reel", "row", "height", "symbol"}` comme un seul grand symbole : `row` = ligne du haut du bloc (0 ou moins s'il commence au-dessus de l'écran), `height` = 2 ou 3 |
| `stickyWilds` | en free spins, après le `reveal` | liste tous les wilds collants (`wilds` : `reel`, `row`, `multiplier`, `new`). `mode` = `MARCHE` : anime d'abord le déplacement d'un rouleau vers la gauche des wilds déjà présents (ceux qui ont `new: false`), puis l'arrivée des nouveaux ; `FIXE` : les anciens ne bougent pas |
| `winInfo` | si le spin gagne | surligne chaque gain (`positions`, wilds compris), affiche `win`. `meta.ways` = nombre de ways (multis des wilds compris) |
| `setWin` | fin d'un spin gagnant | gain du spin (`winLevel` de 1 à 10) |
| `setTotalWin` | fin de chaque spin | gain total du tour |
| `freeSpinTrigger` | déclenchement d'un bonus | anime les scatters, annonce `totalFs`. **`bonus`** = 1 ou 2, **`wilds`** = `MARCHE` ou `FIXE` : intro et décor propres à chaque bonus |
| `updateFreeSpin` | début de chaque FS | compteur : `amount` = FS déjà joués, `total` |
| `freeSpinRetrigger` | 3 scatters ou plus en FS | +5 FS |
| `freeSpinEnd` | fin des FS | écran récapitulatif |
| `wincap` | max win atteint | célébration « MAX WIN », le tour s'arrête |
| `finalWin` | fin du tour | gain final |

**Événements propres à ce jeu**

```json
{"type": "giantSymbols", "blocks": [{"reel": 0, "row": 2, "height": 3, "symbol": "H1"},
                                     {"reel": 3, "row": 0, "height": 2, "symbol": "L2"}]}
{"type": "stickyWilds", "mode": "MARCHE",
 "wilds": [{"reel": 1, "row": 3, "multiplier": 2, "new": false},
           {"reel": 4, "row": 1, "multiplier": 3, "new": true}]}
```

Dans le premier exemple, le `L2` géant du rouleau 4 commence au-dessus de l'écran (`row` 0 = padding) : seule sa case du bas est visible, en ligne 1.

*(Des exemples réels de tours sont en section 9.)*

---

## 8. Statistiques

Calculées sur les fichiers générés par le math SDK officiel (version de novembre 2026), avec 20 000 résultats par mode. Pour la publication, il faudra relancer avec 100 000 résultats ou plus par mode : les chiffres bougeront un peu, le RTP reste exactement 96,20 %.

Les poids des résultats viennent d'une **pondération naturelle** : chaque bonus garde sa probabilité exacte (calculée sur toutes les positions des rouleaux), la fréquence de gain et celle du max win gardent leur valeur simulée, et seul le bruit des résultats est corrigé pour tomber pile sur 96,20 %.

| | `base` (1×) | `bonus` (97×) | `super` (465×) |
|---|---|---|---|
| RTP | **96,20 %** | **96,20 %** | **96,20 %** |
| Gain moyen (× la mise de base) | 0,96 | 93,3 | 447 |
| Fréquence de gain | 32,2 % (1 sur 3,1) | 99,9 % | 99,5 % |
| Écart-type (× la mise) | 17,8 | 231 | 1 125 |
| Gain médian | 0 | 34,5× | 85× |
| Max win (10 000×) | ≈ 1 tour sur 1 700 000 | ≈ 1 achat sur 45 000 | ≈ 1 achat sur 265 |

**Les bonus en jeu de base**

| | Fréquence | Gain moyen | Part du RTP |
|---|---|---|---|
| Spins | chaque spin | 0,60× | ≈ 62 % |
| Bonus 1 « Free spins » (wilds qui avancent) | 1 tour sur 305 | ≈ 93× | ≈ 32 % |
| Bonus 2 « Super free spins » (wilds fixes) | 1 tour sur 7 700 | ≈ 450× | ≈ 6 % |

**Contrôles du math SDK** (`utils/rgs_verification.py`), tous respectés :

| Contrôle | Limite | `base` | `bonus` | `super` |
|---|---|---|---|---|
| RTP de chaque mode (soumission) | 96,0 à 96,7 % | 96,20 % | 96,20 % | 96,20 % |
| Écart-type du jeu de base (soumission) | ≥ 0,6 | 17,8 | | |
| Écart-type / coût (risque) | ≤ 60 | 17,8 | 2,4 | 2,4 |
| Part du RTP venant des gains ≥ 40× le coût | ≤ 0,9 | 0,38 | 0,02 | 0 |
| Part du RTP venant des gains ≥ 10 000× | ≤ 0,8 | 0,006 | 0,002 | 0,081 |
| `cvar` : gain moyen des 0,1 % meilleurs tours / coût | ≤ 700 | 283 | 45 | 22 |
| Gains de 5 000× et plus | ≤ 5 % | ≈ 0 | 0,03 % | 1,5 % |
| Mise maximale autorisée | | **1 000 $** (6 contrôles de risque sur 6) | | |

Les « étoiles » de Stake (0 à 3) sont une note de qualité donnée par 3 relecteurs (créativité, finition) : elles ne dépendent pas des maths.

**Distribution des gains par tour (% des tours, gains en × la mise de base)**

| Gain | `base` | `bonus` | `super` |
|---|---|---|---|
| 0 | 67,8 % | 0,11 % | 0,50 % |
| 0–1× | 19,2 % | 0,86 % | 1,5 % |
| 1–5× | 10,4 % | 7,9 % | 6,5 % |
| 5–20× | 2,2 % | 26,0 % | 15,6 % |
| 20–100× | 0,44 % | 42,7 % | 29,1 % |
| 100–1 000× | 0,082 % | 21,5 % | 36,1 % |
| 1 000–10 000× | 0,0032 % | 0,93 % | 10,3 % |
| 10 000× (max win) | 0,00006 % | 0,0022 % | 0,38 % |

Pour la célébration des gains, `winLevel` (de 1 à 10) suit les seuils du SDK :
- **par spin** : 1 = moins de 0,1×, 2 = jusqu'à 1×, 3 = 1–2×, 4 = 2–5×, 5 = 5–15×, 6 = 15–30×, 7 = 30–50×, 8 = 50–100×, 9 = 100× jusqu'au max win, 10 = max win ;
- **en fin de FS** : 1 = moins de 1×, 2 = 1–5×, 3 = 5–10×, 4 = 10–20×, 5 = 20–50×, 6 = 50–100×, 7 = 100–500×, 8 = 500–2 000×, 9 = 2 000× jusqu'au max win, 10 = max win.

---

## 9. Exemples réels de tours

Extraits des fichiers générés.

### 9.1 Jeu de base, symboles géants et deux wilds x3 : gain de 5,40× (`id` 46 du mode `base`)

Au rouleau 2, un `L3` géant de 3 cases commence au-dessus de l'écran (`row` 0) : on voit ses 2 cases du bas. Les deux wilds x3 (rouleaux 3 et 4) comptent chacun pour 3 : `L4` sur 4 rouleaux fait 1 × 1 × 3 × 3 = 9 ways × 0,2 = 1,80×, et `L2` 9 ways × 0,4 = 3,60×.

```json
{"id": 46, "payoutMultiplier": 540, "events": [
  {"index": 0, "type": "reveal", "board": [[{"name": "L3"}, {"name": "L5"}, {"name": "L1"}, {"name": "L4"}, {"name": "L2"}, {"name": "H3"}], [{"name": "L3"}, {"name": "L3"}, {"name": "L3"}, {"name": "L2"}, {"name": "L4"}, {"name": "L4"}], [{"name": "H4"}, {"name": "L5"}, {"name": "W", "wild": true, "multiplier": 3}, {"name": "H4"}, {"name": "H3"}, {"name": "L4"}], [{"name": "L1"}, {"name": "L3"}, {"name": "L3"}, {"name": "H4"}, {"name": "W", "wild": true, "multiplier": 3}, {"name": "H4"}], [{"name": "L4"}, {"name": "L1"}, {"name": "H4"}, {"name": "L5"}, {"name": "L1"}, {"name": "L5"}]], "paddingPositions": [20, 8644, 15779, 17913, 299], "gameType": "basegame", "anticipation": [0, 0, 0, 0, 0]},
  {"index": 1, "type": "giantSymbols", "blocks": [{"reel": 1, "row": 0, "height": 3, "symbol": "L3"}, {"reel": 1, "row": 4, "height": 2, "symbol": "L4"}, {"reel": 3, "row": 1, "height": 2, "symbol": "L3"}]},
  {"index": 2, "type": "winInfo", "totalWin": 540, "wins": [
    {"symbol": "L4", "kind": 4, "win": 180, "positions": [{"reel": 0, "row": 3}, {"reel": 1, "row": 4}, {"reel": 2, "row": 2}, {"reel": 3, "row": 4}], "meta": {"ways": 9, "globalMult": 1, "winWithoutMult": 180, "symbolMult": 6}},
    {"symbol": "L2", "kind": 4, "win": 360, "positions": [{"reel": 0, "row": 4}, {"reel": 1, "row": 3}, {"reel": 2, "row": 2}, {"reel": 3, "row": 4}], "meta": {"ways": 9, "globalMult": 1, "winWithoutMult": 360, "symbolMult": 6}}]},
  {"index": 3, "type": "setWin", "amount": 540, "winLevel": 5},
  {"index": 4, "type": "setTotalWin", "amount": 540},
  {"index": 5, "type": "finalWin", "amount": 540}]}
```

### 9.2 Bonus 1 acheté, wilds collants qui avancent : gain de 131,00× (`id` 4 du mode `bonus`, résumé)

Suis le wild x2 tombé au rouleau 5 (`reel` 4, `row` 3) : il avance d'un rouleau vers la gauche à chaque free spin (`reel` 3, puis 2, puis 1, puis 0), puis il sort.

```
{"index": 5, "type": "freeSpinTrigger", "totalFs": 10, "positions": [...3 scatters...], "bonus": 1, "wilds": "MARCHE"}
{"index": 13, "type": "stickyWilds", "mode": "MARCHE", "wilds": [{"reel": 4, "row": 3, "multiplier": 2, "new": true}]}
{"index": 20, "type": "stickyWilds", "mode": "MARCHE", "wilds": [{"reel": 3, "row": 3, "multiplier": 2, "new": false}]}
{"index": 25, "type": "stickyWilds", "mode": "MARCHE", "wilds": [{"reel": 1, "row": 4, "multiplier": 5, "new": true}, {"reel": 2, "row": 3, "multiplier": 2, "new": false}]}
{"index": 27, "type": "setWin", "amount": 1720, "winLevel": 6}
{"index": 32, "type": "stickyWilds", "mode": "MARCHE", "wilds": [{"reel": 0, "row": 4, "multiplier": 5, "new": false}, {"reel": 1, "row": 3, "multiplier": 2, "new": false}]}
…
{"index": 53, "type": "stickyWilds", "mode": "MARCHE", "wilds": [{"reel": 1, "row": 2, "multiplier": 3, "new": false}, {"reel": 2, "row": 3, "multiplier": 2, "new": false}, {"reel": 3, "row": 2, "multiplier": 2, "new": false}]}
{"index": 55, "type": "setWin", "amount": 5760, "winLevel": 8}
…
{"index": 69, "type": "freeSpinEnd", "amount": 12860, "winLevel": 7}
{"index": 70, "type": "finalWin", "amount": 13100}
```

`finalWin` (131,00×) = gain du spin de déclenchement (2,40×) + gain des free spins (128,60×).

---

## 10. Règles d'approbation Stake Engine à respecter pour la DA

D'après la doc officielle ([github.com/engineio/docs](https://github.com/engineio/docs), section « Approval ») :
- **Originalité** : jeu original, sans reprendre le thème, le nom ni les visuels d'un jeu existant (pas de chiens ni de niche façon Dog House). Le titre ne doit pas contenir « Megaways » ou « Xways ».
- **Mineurs** : rien qui puisse attirer les mineurs (pas d'enfants ni de personnages enfantins).
- **Contenu** : pas de contenu choquant ; qualité suffisante pour obtenir au moins 1 étoile de la part des 3 relecteurs.
- **Jeu sans état** : chaque tour est indépendant, sans jackpot, quitte-ou-double ni encaissement anticipé (les maths le respectent : les wilds collants ne durent que le temps d'un bonus).
- **Page de règles** : gain de chaque symbole, ways, symboles géants, wilds multiplicateurs, wilds collants de chaque bonus, déclenchement des bonus et des retriggers, coût de chaque mode, RTP et max win de chaque mode, et le texte légal : « Malfunction voids all pays and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted bets. The expected return is calculated over many spins. Animations are not representative of any physical device, and are for illustrative purposes only. »
- **Interface** : confirmation avant un mode qui coûte plus de 2× la mise (les deux achats), autoplay avec confirmation, barre espace pour spinner, son désactivable, mode replay, mode social de Stake.us (pas de « bet », « buy »…).

---

## 11. Fichiers de maths (dans ce dossier)

| Fichier | Rôle |
|---|---|
| `classeur_maths.xlsx` + `simulateur.py` | Conception et réglage des maths |
| `stake/games/0_0_wilds/` | Le jeu pour le math SDK de Stake Engine |
| `<math-sdk>/games/0_0_wilds/library/publish_files/` | **À déposer sur Stake Engine** : `index.json`, et pour chaque mode (`base`, `bonus`, `super`) `books_<mode>.jsonl.zst` et `lookUpTable_<mode>_0.csv` (générés par `run.py`, voir `INSTALLATION_MAC.md`) |
| `sortie/config_fe_0_0_wilds.json` | Config pour le front-end |
| `sortie/statistiques/` | Statistiques produites par le SDK |
