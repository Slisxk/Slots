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
| Bonus buy | Bonus 1 : 101 × la mise · Bonus 2 : 500 × la mise |
| RTP | 96,20 % dans les 3 modes |
| Max win | **10 000 × la mise** |
| Fréquence de gain | ≈ 30 % des tours (1 sur 3,3) |

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
8. **Bonus buy** : Bonus 1 pour 101 × la mise, Bonus 2 pour 500 × la mise. Le tour commence par un spin de déclenchement avec 3 (ou 4) scatters, qui peut lui-même gagner.
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
| `super` | 500 × la mise | achat | Bonus 2 « Super free spins » directement |

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
