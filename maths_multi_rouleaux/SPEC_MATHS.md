# Spécification maths : slot 5×3 ways « multis de colonne », bonus collant ou non

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
| Grille | 5 rouleaux × 3 lignes, **243 ways** |
| Gains | Ways de gauche à droite : le même symbole sur des rouleaux consécutifs à partir du rouleau 1 (3, 4 ou 5 rouleaux) |
| Feature principale | **Multi de colonne** : un multi de **x2 à x500** couvre un rouleau entier, de haut en bas |
| Bonus 1 « Free spins » | 3 scatters → 10 free spins, multis **non collants** |
| Bonus 2 « Super free spins » | 4 ou 5 scatters → 10 free spins, multis **collants** qui s'additionnent |
| Retrigger | 3 scatters ou plus pendant les free spins → +5 free spins |
| Bonus buy | Bonus 1 : 101 × la mise · Bonus 2 : 490 × la mise |
| RTP | 96,20 % dans les 3 modes |
| Max win | **10 000 × la mise** |
| Fréquence de gain | 30,4 % des tours (1 sur 3,3) |

*(Les statistiques détaillées sont en section 8.)*

---

## 2. Symboles

| Code | Rôle | Conseil visuel |
|---|---|---|
| `H1` | Premium 1, le plus fort | symbole le plus prestigieux du thème |
| `H2`, `H3`, `H4` | Premiums | |
| `L1` … `L5` | Bas (équivalents A, K, Q, J, 10) | simples et très lisibles |
| `W` | **Wild** : remplace les symboles payants. Jamais sur le rouleau 1 | |
| `S` | **Scatter** : déclenche les bonus. Au plus 1 par rouleau | doit se voir de loin |

Le multi de colonne n'est pas un symbole : c'est un effet posé sur un rouleau entier (par exemple un éclair ou une colonne lumineuse avec sa valeur « x25 » affichée).

---

## 3. Règles du jeu (base du texte de la page de règles)

1. **Ways** : un gain se forme avec au moins 3 symboles identiques sur des rouleaux consécutifs, en partant du rouleau le plus à gauche, quelle que soit leur ligne. Le nombre de ways d'un gain = produit du nombre de symboles qui comptent sur chaque rouleau (exemple : 2 × 1 × 3 = 6 ways). Gain = valeur de la paytable × nombre de ways.
2. **Wild** : `W` remplace tous les symboles payants, sauf sur le rouleau 1 où il n'apparaît pas.
3. **Multi de colonne** : après l'arrivée de la grille, un ou plusieurs rouleaux peuvent recevoir un multi qui couvre toute la colonne (x2 à x500). Un gain est multiplié par la **somme des multis des colonnes qu'il traverse**. Sans multi sur ses colonnes, il est multiplié par 1. Exemple : un gain sur les rouleaux 1 à 4 avec un x5 sur le rouleau 2 et un x20 sur le rouleau 4 est multiplié par 25. Un multi sur le rouleau 5 ne compte pas pour un gain de 4 rouleaux.
4. **Jeu de base** : les multis sont rares et disparaissent après chaque spin.
5. **Bonus 1 « Free spins »** : 3 scatters = 10 free spins. Les multis sont fréquents (environ 1 colonne sur 3 à chaque spin) et **disparaissent après chaque spin**.
6. **Bonus 2 « Super free spins »** : 4 ou 5 scatters = 10 free spins. Les multis sont **collants** : un multi reste sur sa colonne jusqu'à la fin du bonus, et chaque nouveau multi qui tombe sur cette colonne **s'ajoute** à sa valeur (exemple : x5, puis +x10, la colonne vaut x15).
7. **Retrigger** : pendant les free spins des deux bonus, 3 scatters ou plus = +5 free spins. Le bonus ne change pas.
8. **Bonus buy** : Bonus 1 pour 101 × la mise, Bonus 2 pour 490 × la mise. Le tour commence par un spin de déclenchement avec 3 (ou 4) scatters, qui peut lui-même gagner.
9. **Max win** : le gain d'un tour (spin + free spins) est plafonné à 10 000 × la mise. Quand le plafond est atteint, le tour s'arrête.
10. Les gains sont exprimés en multiples de la mise totale. Les mauvais fonctionnements annulent tous les gains et jeux.

---

## 4. Paytable (× la mise totale, par way)

| Symbole | 3 rouleaux | 4 rouleaux | 5 rouleaux |
|---|---|---|---|
| `H1` | 2 | 5,5 | 18 |
| `H2` | 1,4 | 3,7 | 13 |
| `H3` | 1,1 | 2,8 | 8,3 |
| `H4` | 0,9 | 2,3 | 5,5 |
| `L1` | 0,5 | 1,5 | 3 |
| `L2` | 0,5 | 1,1 | 2,2 |
| `L3` | 0,4 | 0,9 | 1,8 |
| `L4` | 0,3 | 0,8 | 1,5 |
| `L5` | 0,3 | 0,7 | 1,5 |

Gain affiché = valeur × nombre de ways × multi de colonne.

---

## 5. Multis de colonne

**Probabilité qu'une colonne reçoive un multi, à chaque spin (même valeur pour les 5 rouleaux)**

| Jeu de base | Bonus 1 (non collant) | Bonus 2 (collant) |
|---|---|---|
| 1,6 % (≈ 1 spin sur 13 a au moins un multi) | 31,2 % | 22 % |

**Valeur d'un multi**

| Valeur | x2 | x3 | x4 | x5 | x10 | x20 | x50 | x100 | x250 | x500 | Moyenne |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jeu de base | 40 % | 25 % | 15 % | 10 % | 6 % | 2,5 % | 1 % | 0,4 % | 0,1 % | — | x4,9 |
| Bonus 1 | 29,1 % | 21,3 % | 15,5 % | 12,6 % | 10,7 % | 6,8 % | 2,9 % | 0,97 % | 0,19 % | 0,05 % | x8,0 |
| Bonus 2 | 30,5 % | 20,4 % | 15,3 % | 12,2 % | 10,2 % | 6,1 % | 3,1 % | 1,5 % | 0,51 % | 0,20 % | x10,0 |

Les grosses valeurs sont rares : prévois une mise en scène spéciale pour x100, x250 et x500.

---

## 6. Modes de mise

| Mode | Coût | Type | Contenu |
|---|---|---|---|
| `base` | 1 × la mise | spin | spin normal (peut déclencher les deux bonus) |
| `bonus` | 101 × la mise | achat | Bonus 1 « Free spins » directement |
| `super` | 490 × la mise | achat | Bonus 2 « Super free spins » directement |

Les deux achats coûtent plus de 2 × la mise : la règle Stake impose une **confirmation** avant l'achat.

---

## 7. Ce que le front-end reçoit (format Stake Engine)

Chaque tour est un objet JSON (un « book ») :

```json
{ "id": 34, "payoutMultiplier": 560, "events": [ ... ] }
```

**Conventions**
- `payoutMultiplier` et tous les montants (`amount`, `win`, `totalWin`) sont des **entiers en centièmes de mise** : `560` = 5,60 × la mise. Ce sont toujours des multiples de 10 (gains par pas de 0,1 × la mise).
- `board[reel][row]` : `reel` de 0 à 4, de gauche à droite ; `row` de 0 à 4, de haut en bas, où **0 et 4 sont des symboles de padding hors écran**. Les lignes visibles sont 1, 2 et 3.
- Toutes les positions `{"reel", "row"}` utilisent cette numérotation, padding compris.

**Événements, dans l'ordre où ils arrivent**

| Événement | Quand | Ce que le front-end fait |
|---|---|---|
| `reveal` | début de chaque spin (base ou FS) | affiche la grille (`board`), `gameType` = `basegame` ou `freegame` |
| `columnMultipliers` | juste après le `reveal`, si au moins une colonne a un multi | pose les nouveaux multis (`new`), affiche la valeur de chaque colonne (`columns`, 0 = pas de multi). En bonus collant (`sticky: true`), `columns` contient la valeur **cumulée** : anime l'addition sur les colonnes qui avaient déjà un multi |
| `winInfo` | si le spin gagne | surligne chaque gain (`positions`), affiche `win`. `meta.ways` = nombre de ways, `meta.winWithoutMult` = gain avant multi, `meta.columnMult` = multi appliqué (somme des colonnes traversées) |
| `setWin` | fin d'un spin gagnant | gain du spin (`winLevel` de 1 à 10 pour choisir la célébration) |
| `setTotalWin` | fin de chaque spin | gain total du tour |
| `freeSpinTrigger` | déclenchement d'un bonus | anime les scatters (`positions`), annonce `totalFs`. **`bonus`** = 1 ou 2, **`sticky`** = multis collants ou non : intro, musique et décor propres à chaque bonus |
| `updateFreeSpin` | début de chaque FS | compteur : `amount` = FS déjà joués (0 au premier), `total` |
| `freeSpinRetrigger` | 3 scatters ou plus pendant les FS | +5 FS, `totalFs` mis à jour |
| `freeSpinEnd` | fin des FS | écran récapitulatif (`amount`, `winLevel`) |
| `wincap` | max win atteint | célébration « MAX WIN », le tour s'arrête |
| `finalWin` | fin du tour | gain final |

**Événement propre à ce jeu : `columnMultipliers`**

```json
{"type": "columnMultipliers",
 "new": [{"reel": 3, "multiplier": 10}],
 "columns": [5, 0, 0, 25, 0],
 "sticky": true}
```

Ici, en bonus collant : la colonne 1 garde son x5, la colonne 4 avait x15 et reçoit +x10, elle vaut donc x25.

*(Des exemples réels de tours sont en section 9.)*

---

## 8. Statistiques

Calculées sur les fichiers générés par le math SDK officiel (version de novembre 2026), avec 20 000 résultats par mode. Pour la publication, il faudra relancer avec 100 000 résultats ou plus par mode : les chiffres bougeront un peu, le RTP reste exactement 96,20 %.

Les poids des résultats viennent d'une **pondération naturelle** : chaque bonus garde sa probabilité exacte, la fréquence de gain et la fréquence du max win gardent leur valeur simulée, et seul le bruit des résultats est corrigé pour tomber pile sur 96,20 %. Aucun gros gain n'est rendu artificiellement plus rare.

| | `base` (1×) | `bonus` (101×) | `super` (490×) |
|---|---|---|---|
| RTP | **96,20 %** | **96,20 %** | **96,20 %** |
| Gain moyen (× la mise de base) | 0,96 | 97,2 | 471 |
| Fréquence de gain | 30,4 % (1 sur 3,3) | 99,3 % | 99,2 % |
| Écart-type (× la mise) | 20,9 | 213 | 885 |
| Gain médian | 0 | 43× | 197× |
| Max win (10 000×) | ≈ 1 tour sur 3 000 000 | ≈ 1 achat sur 28 000 | ≈ 1 achat sur 850 |

**Les bonus en jeu de base**

| | Fréquence | Gain moyen | Part du RTP |
|---|---|---|---|
| Spins (multis compris) | chaque spin | 0,62× | ≈ 64 % |
| Bonus 1 « Free spins » (3 scatters) | 1 tour sur 334 | ≈ 97× | ≈ 30 % |
| Bonus 2 « Super free spins » (4 ou 5) | 1 tour sur 8 700 | ≈ 480× | ≈ 6 % |

**Contrôles du math SDK** (`utils/rgs_verification.py`), tous respectés :

| Contrôle | Limite | `base` | `bonus` | `super` |
|---|---|---|---|---|
| RTP de chaque mode (soumission) | 96,0 à 96,7 % | 96,20 % | 96,20 % | 96,20 % |
| Écart-type du jeu de base (soumission) | ≥ 0,6 | 20,9 | | |
| Écart-type / coût (risque) | ≤ 60 | 20,9 | 2,2 | 1,9 |
| Part du RTP venant des gains ≥ 40× le coût | ≤ 0,9 | 0,39 | 0,02 | 0 |
| Part du RTP venant des gains ≥ 10 000× | ≤ 0,8 | 0,003 | 0,004 | 0,024 |
| `cvar` : gain moyen des 0,1 % meilleurs tours / coût | ≤ 700 | 314 | 40 | 20 |
| Gains de 5 000× et plus | ≤ 5 % | ≈ 0 | 0,02 % | 0,81 % |
| Mise maximale autorisée | | **1 000 $** (6 contrôles de risque sur 6) | | |

Les « étoiles » de Stake (0 à 3) sont une note de qualité donnée par 3 relecteurs (créativité, finition) : elles ne dépendent pas des maths.

**Distribution des gains par tour (% des tours, gains en × la mise de base)**

| Gain | `base` | `bonus` | `super` |
|---|---|---|---|
| 0 | 69,6 % | 0,68 % | 0,84 % |
| 0–1× | 14,6 % | 0,87 % | 0,31 % |
| 1–5× | 13,3 % | 5,9 % | 1,5 % |
| 5–20× | 2,1 % | 21,2 % | 5,4 % |
| 20–100× | 0,33 % | 46,2 % | 23,8 % |
| 100–1 000× | 0,085 % | 24,4 % | 57,2 % |
| 1 000–10 000× | 0,0045 % | 0,71 % | 11,0 % |
| 10 000× (max win) | 0,00003 % | 0,0036 % | 0,12 % |

Pour la célébration des gains, `winLevel` (de 1 à 10) suit les seuils du SDK :
- **par spin** : 1 = moins de 0,1×, 2 = jusqu'à 1×, 3 = 1–2×, 4 = 2–5×, 5 = 5–15×, 6 = 15–30×, 7 = 30–50×, 8 = 50–100×, 9 = 100× jusqu'au max win, 10 = max win ;
- **en fin de FS** : 1 = moins de 1×, 2 = 1–5×, 3 = 5–10×, 4 = 10–20×, 5 = 20–50×, 6 = 50–100×, 7 = 100–500×, 8 = 500–2 000×, 9 = 2 000× jusqu'au max win, 10 = max win.

---

## 9. Exemples réels de tours

Extraits des fichiers générés.

### 9.1 Jeu de base avec un multi de colonne : gain de 5,60× (`id` 34 du mode `base`)

Un x4 tombe sur le rouleau 2. Deux gains de 3 rouleaux le traversent : H3 (1 way × 1,1 = 1,10×, multiplié par 4 = 4,40×) et L4 (1 way × 0,3 = 0,30×, multiplié par 4 = 1,20×).

```json
{"id": 34, "payoutMultiplier": 560, "events": [
  {"index": 0, "type": "reveal", "board": [[{"name": "L2"}, {"name": "H4"}, {"name": "H3"}, {"name": "L4"}, {"name": "H4"}], [{"name": "S", "scatter": true}, {"name": "L4"}, {"name": "L3"}, {"name": "H3"}, {"name": "L1"}], [{"name": "L5"}, {"name": "L4"}, {"name": "L5"}, {"name": "H3"}, {"name": "L4"}], [{"name": "L3"}, {"name": "L3"}, {"name": "L1"}, {"name": "H4"}, {"name": "L4"}], [{"name": "H4"}, {"name": "L4"}, {"name": "L5"}, {"name": "L1"}, {"name": "H3"}]], "paddingPositions": [12013, 19179, 3169, 11937, 282], "gameType": "basegame", "anticipation": [0, 0, 0, 0, 0]},
  {"index": 1, "type": "columnMultipliers", "new": [{"reel": 1, "multiplier": 4}], "columns": [0, 4, 0, 0, 0], "sticky": false},
  {"index": 2, "type": "winInfo", "totalWin": 560, "wins": [
    {"symbol": "H3", "kind": 3, "win": 440, "positions": [{"reel": 0, "row": 2}, {"reel": 1, "row": 3}, {"reel": 2, "row": 3}], "meta": {"ways": 1, "globalMult": 4, "winWithoutMult": 110, "symbolMult": 0, "columnMult": 4}},
    {"symbol": "L4", "kind": 3, "win": 120, "positions": [{"reel": 0, "row": 3}, {"reel": 1, "row": 1}, {"reel": 2, "row": 1}], "meta": {"ways": 1, "globalMult": 4, "winWithoutMult": 30, "symbolMult": 0, "columnMult": 4}}]},
  {"index": 3, "type": "setWin", "amount": 560, "winLevel": 5},
  {"index": 4, "type": "setTotalWin", "amount": 560},
  {"index": 5, "type": "finalWin", "amount": 560}]}
```

### 9.2 Bonus 2 acheté, multis collants : gain de 202,50× (`id` 0 du mode `super`, résumé)

Les multis s'accumulent colonne par colonne : la colonne 2 passe de x10 à x12 puis x14, la colonne 4 de x2 à x4 puis x7.

```
{"index": 1, "type": "columnMultipliers", "new": [{"reel": 0, "multiplier": 5}], "columns": [5, 0, 0, 0, 0], "sticky": false}   ← spin de déclenchement
{"index": 3, "type": "freeSpinTrigger", "totalFs": 10, "positions": [...4 scatters...], "bonus": 2, "sticky": true}
{"index": 4, "type": "updateFreeSpin", "amount": 0, "total": 10}
{"index": 14, "type": "columnMultipliers", "new": [{"reel": 3, "multiplier": 2}], "columns": [0, 0, 0, 2, 0], "sticky": true}
{"index": 24, "type": "columnMultipliers", "new": [{"reel": 2, "multiplier": 2}, {"reel": 3, "multiplier": 2}], "columns": [0, 0, 2, 4, 0], "sticky": true}
{"index": 28, "type": "columnMultipliers", "new": [{"reel": 4, "multiplier": 5}], "columns": [0, 0, 2, 4, 5], "sticky": true}
{"index": 32, "type": "columnMultipliers", "new": [{"reel": 1, "multiplier": 10}, {"reel": 3, "multiplier": 3}], "columns": [0, 10, 2, 7, 5], "sticky": true}
{"index": 36, "type": "columnMultipliers", "new": [{"reel": 1, "multiplier": 2}, {"reel": 2, "multiplier": 4}], "columns": [0, 12, 6, 7, 5], "sticky": true}
{"index": 38, "type": "setWin", "amount": 7020, "winLevel": 8}
{"index": 44, "type": "setWin", "amount": 8000, "winLevel": 8}
{"index": 48, "type": "columnMultipliers", "new": [{"reel": 1, "multiplier": 2}], "columns": [0, 14, 6, 7, 5], "sticky": true}
{"index": 50, "type": "setWin", "amount": 4860, "winLevel": 7}
{"index": 52, "type": "freeSpinEnd", "amount": 20250, "winLevel": 7}
{"index": 53, "type": "finalWin", "amount": 20250}
```

Pendant un spin collant sans nouveau multi, `columnMultipliers` arrive quand même avec `"new": []` : les colonnes gardent leurs valeurs.

---

## 10. Règles d'approbation Stake Engine à respecter pour la DA

D'après la doc officielle ([github.com/engineio/docs](https://github.com/engineio/docs), section « Approval ») :
- **Originalité** : jeu original, sans reprendre le thème, le nom ni les visuels d'un jeu existant. Le titre ne doit pas contenir « Megaways » ou « Xways ».
- **Mineurs** : rien qui puisse attirer les mineurs (pas d'enfants ni de personnages enfantins).
- **Contenu** : pas de contenu choquant ; qualité suffisante pour obtenir au moins 1 étoile de la part des 3 relecteurs.
- **Jeu sans état** : chaque tour est indépendant, sans jackpot, quitte-ou-double ni encaissement anticipé (les maths le respectent).
- **Page de règles** : gain de chaque symbole, ways, multis de colonne (collants ou non), déclenchement des bonus et des retriggers, coût de chaque mode, RTP et max win de chaque mode, et le texte légal : « Malfunction voids all pays and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted bets. The expected return is calculated over many spins. Animations are not representative of any physical device, and are for illustrative purposes only. »
- **Interface** : confirmation avant un mode qui coûte plus de 2× la mise (les deux achats), autoplay avec confirmation, barre espace pour spinner, son désactivable, mode replay, mode social de Stake.us (pas de « bet », « buy »…).

---

## 11. Fichiers de maths (dans ce dossier)

| Fichier | Rôle |
|---|---|
| `classeur_maths.xlsx` + `simulateur.py` | Conception et réglage des maths |
| `stake/games/0_0_colonnes/` | Le jeu pour le math SDK de Stake Engine |
| `<math-sdk>/games/0_0_colonnes/library/publish_files/` | **À déposer sur Stake Engine** : `index.json`, et pour chaque mode (`base`, `bonus`, `super`) `books_<mode>.jsonl.zst` et `lookUpTable_<mode>_0.csv` (générés par `run.py`, voir `INSTALLATION_MAC.md`) |
| `sortie/config_fe_0_0_colonnes.json` | Config pour le front-end |
| `sortie/statistiques/` | Statistiques produites par le SDK |
