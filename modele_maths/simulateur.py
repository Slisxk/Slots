#!/usr/bin/env python3
"""
Simulateur Monte Carlo pour le modèle de maths (grille 5 rouleaux, clusters + cascades,
ou lignes / ways ; globe qui fait apparaître des multiplicateurs autour de lui ;
3 bonus déclenchés par 3 / 4 / 5 symboles bonus, dont un bonus caché ; spins boostés).

Il lit tous les paramètres dans le classeur Excel (plages nommées) et réécrit
les résultats dans l'onglet « Simulation ».

    python simulateur.py modele_maths.xlsx
    python simulateur.py modele_maths.xlsx --spins 500000 --boost 200000 --buy 20000
    python simulateur.py modele_maths.xlsx --no-write   # affiche seulement
"""
import argparse
import datetime as dt
import sys

import numpy as np
from openpyxl import load_workbook

MODES = ("WILD_ADD", "WILD_MULT", "GLOBAL_SUM")
MODES_GAIN = ("CLUSTER", "LINES", "WAYS")
MULTI = -2                       # code d'une case multiplicateur posée par le globe (mode CLUSTER)
MAX_FS_PAR_SESSION = 2000          # garde-fou contre une boucle de retrigger infinie
DIST_BORNES = [0, 1, 5, 20, 100, 1000]   # tranches de la distribution des gains (x mise)


# --------------------------------------------------------------------------- #
# Lecture des paramètres
# --------------------------------------------------------------------------- #
def _name_range(wb, name):
    """Renvoie les valeurs (liste de lignes) d'une plage nommée."""
    if name not in wb.defined_names:
        sys.exit(f"Plage nommée introuvable dans le classeur : {name}")
    sheet, ref = next(iter(wb.defined_names[name].destinations))
    cells = wb[sheet][ref.replace("$", "")]
    if not isinstance(cells, tuple):
        return [[cells.value]]
    if not isinstance(cells[0], tuple):
        cells = (cells,)
    return [[c.value for c in row] for row in cells]


def _name_value(wb, name):
    return _name_range(wb, name)[0][0]


def _oui(v):
    return str(v).strip().upper() in ("OUI", "YES", "TRUE", "1")


def load_params(path):
    wb = load_workbook(path)  # pas data_only : les entrées sont des constantes
    pay_rows = [r for r in _name_range(wb, "PAYTABLE") if r[0] not in (None, "")]
    n_sym = len(pay_rows)

    def weights(name):
        rows = _name_range(wb, name)[:n_sym]
        w = np.array([[float(v or 0) for v in r[2:7]] for r in rows])
        if w.shape != (n_sym, 5):
            sys.exit(f"{name} : il faut 5 colonnes de poids et {n_sym} symboles "
                     f"(même ordre que la Paytable).")
        return w

    multis = [r for r in _name_range(wb, "MULTIS") if r[0] not in (None, "")]
    bonus = []
    for r in _name_range(wb, "BONUS"):
        if r[0] in (None, "") or r[1] in (None, ""):
            continue
        bonus.append({"nom": str(r[0]), "bn": int(r[1]), "fs": int(r[2]), "globe_garanti": _oui(r[3]),
                      "prix": float(r[4]) if r[4] not in (None, "", 0) else None})
    lignes = [[int(v) - 1 for v in r] for r in _name_range(wb, "LIGNES")
              if all(v not in (None, "") for v in r)]
    tailles = [int(v) for v in _name_range(wb, "TAILLES_CLUSTER")[0] if v not in (None, "")]
    pay_cl = [[float(v or 0) for v in r[:len(tailles)]] for r in _name_range(wb, "PAYTABLE_CLUSTER")[:n_sym]]

    # Une « phase » = un jeu de poids de rouleaux + une table de multis :
    # base, boost (spins boostés), fs1 / fs2 / fs3 (free spins de chaque bonus)
    poids = {"base": weights("POIDS_BASE"), "boost": weights("POIDS_BOOST")}
    multi_w = {"base": np.array([float(r[1] or 0) for r in multis])}
    multi_w["boost"] = multi_w["base"]
    for k in range(len(bonus)):
        poids[f"fs{k + 1}"] = weights(f"POIDS_FS{k + 1}")
        multi_w[f"fs{k + 1}"] = np.array([float(r[2 + k] or 0) for r in multis])

    p = {
        "codes": [r[0] for r in pay_rows],
        "noms": [r[1] for r in pay_rows],
        "types": [str(r[2]).strip().upper() for r in pay_rows],
        "pays": np.array([[float(v or 0) for v in r[3:6]] for r in pay_rows]),  # 3,4,5 OAK
        "tailles": tailles,                               # taille mini de chaque groupe de la paytable cluster
        "pays_cluster": np.array(pay_cl).reshape(n_sym, len(tailles)),
        "cascades": _oui(_name_value(wb, "CASCADES")),
        "poids": poids,
        "multi_val": np.array([float(r[0]) for r in multis]),
        "multi_w": multi_w,
        "bonus": bonus,
        "lignes": np.array(lignes, dtype=np.int64).reshape(-1, 5),
        "rows": int(_name_value(wb, "NB_LIGNES")),
        "mode_gain": str(_name_value(wb, "MODE_GAIN")).strip().upper(),
        "rtp_cible": float(_name_value(wb, "RTP_CIBLE")),
        "max_win": float(_name_value(wb, "MAX_WIN")),
        "mode": str(_name_value(wb, "MODE_MULTI")).strip().upper(),
        "multi_globe": float(_name_value(wb, "MULTI_GLOBE")),
        "fs_par_bonus": float(_name_value(wb, "FS_PAR_BONUS")),
        "boost_cout": float(_name_value(wb, "BOOST_COUT")),
        "sim_spins": int(_name_value(wb, "SIM_SPINS")),
        "sim_boost": int(_name_value(wb, "SIM_BOOST")),
        "sim_buy": int(_name_value(wb, "SIM_BUY")),
        "seed": int(_name_value(wb, "SIM_SEED")),
    }
    p["scatter_min"] = bonus[0]["bn"] if bonus else 0
    validate(p)
    return p


def validate(p):
    if p["mode"] not in MODES:
        sys.exit(f"MODE_MULTI doit être l'un de {MODES}, reçu {p['mode']!r}")
    if p["mode_gain"] not in MODES_GAIN:
        sys.exit(f"MODE_GAIN doit être l'un de {MODES_GAIN}, reçu {p['mode_gain']!r}")
    if p["mode_gain"] == "LINES":
        if not len(p["lignes"]):
            sys.exit("Mode LINES : l'onglet Lignes ne contient aucune ligne complète.")
        if p["lignes"].min() < 0 or p["lignes"].max() >= p["rows"]:
            sys.exit(f"Onglet Lignes : les positions doivent aller de 1 à {p['rows']}.")
    if p["mode_gain"] == "CLUSTER":
        if p["mode"] == "WILD_MULT":
            sys.exit("Mode CLUSTER : choisis WILD_ADD ou GLOBAL_SUM (WILD_MULT n'existe pas en cluster dans le SDK).")
        if not p["tailles"] or p["tailles"] != sorted(set(p["tailles"])) or p["tailles"][0] < 1:
            sys.exit("Paytable cluster : les tailles doivent être des entiers croissants >= 1.")
    if p["types"].count("SCATTER") != 1:
        sys.exit("La Paytable doit contenir exactement un symbole de type SCATTER.")
    if p["types"].count("GLOBE") > 1:
        sys.exit("La Paytable doit contenir au plus un symbole de type GLOBE.")
    if "PAY" not in p["types"]:
        sys.exit("La Paytable doit contenir au moins un symbole de type PAY.")
    b = p["bonus"]
    if not 1 <= len(b) <= 3:
        sys.exit("Config : il faut entre 1 et 3 bonus dans la table des bonus.")
    seuils = [x["bn"] for x in b]
    if seuils != sorted(set(seuils)) or seuils[0] < 1 or seuils[-1] > 5:
        sys.exit("Table des bonus : les nombres de symboles bonus doivent être croissants, entre 1 et 5 "
                 "(au plus 1 symbole bonus par rouleau sur la grille de départ).")
    if any(x["fs"] < 1 for x in b):
        sys.exit("Table des bonus : chaque bonus doit donner au moins 1 FS.")
    if p["boost_cout"] <= 1:
        sys.exit("BOOST_COUT : le prix des spins boostés doit être > 1 x la mise.")
    for nom, w in p["poids"].items():
        if (w.sum(axis=0) <= 0).any():
            sys.exit(f"Poids ({nom}) : chaque rouleau doit avoir un poids total > 0.")
    for nom, w in p["multi_w"].items():
        if w.sum() <= 0:
            sys.exit(f"Multis ({nom}) : les poids des multiplicateurs doivent avoir une somme > 0.")


# --------------------------------------------------------------------------- #
# Moteur
# --------------------------------------------------------------------------- #
class Moteur:
    def __init__(self, p, rng):
        self.p = p
        self.rng = rng
        self.rows = p["rows"]
        self.reels = 5
        types = p["types"]
        self.pay_idx = [i for i, t in enumerate(types) if t == "PAY"]
        self.top = self.pay_idx[0]           # les ways 100 % wild paient comme ce symbole
        self.sc = types.index("SCATTER")
        self.gl = types.index("GLOBE") if "GLOBE" in types else -1
        self.prob = {k: w / w.sum(axis=0) for k, w in p["poids"].items()}
        # Au plus 1 symbole bonus par rouleau (comme sur les bandes du SDK, où les symboles bonus sont espacés) :
        # le symbole bonus est présent sur le rouleau avec la probabilité lignes x p, à une rangée au hasard ;
        # les autres cases sont tirées parmi les symboles hors symbole bonus. Chaque case garde sa
        # probabilité de la feuille (poids / total).
        self.q_sc = {k: self.rows * v[self.sc] for k, v in self.prob.items()}
        for k, q in self.q_sc.items():
            if (q > 1).any():
                sys.exit(f"Trop de symboles bonus ({k}) : lignes x P(symbole bonus) doit rester <= 1 sur chaque rouleau.")
        sans_sc = {}
        for k, v in self.prob.items():
            v = v.copy()
            v[self.sc] = 0
            sans_sc[k] = v / v.sum(axis=0)
        self.cum = {k: np.cumsum(v, axis=0) for k, v in sans_sc.items()}
        self.cum_complet = {k: np.cumsum(v, axis=0) for k, v in self.prob.items()}   # recharges des cascades
        # Gain d'un cluster selon sa taille (0 .. lignes x rouleaux), par symbole
        n_cases = self.rows * self.reels
        self.pay_taille = np.zeros((len(p["codes"]), n_cases + 1))
        for j, t in enumerate(p["tailles"]):
            fin = p["tailles"][j + 1] if j + 1 < len(p["tailles"]) else n_cases + 1
            self.pay_taille[:, min(t, n_cases + 1):min(fin, n_cases + 1)] = p["pays_cluster"][:, j][:, None]
        self.mprob = {k: w / w.sum() for k, w in p["multi_w"].items()}
        # Bonus dont chaque free spin commence avec au moins 1 globe
        self.garanti = {f"fs{k + 1}": b["globe_garanti"] for k, b in enumerate(p["bonus"])}

    def _tirage(self, n, phase, force_bn=None):
        """Grille (n, lignes, rouleaux) d'indices de symboles, au plus 1 symbole bonus par rouleau.
        force_bn : nombre exact de symboles bonus sur la grille (comme force_special_board du SDK :
        rouleaux choisis l'un après l'autre, en proportion de leur probabilité d'avoir un symbole bonus)."""
        u = self.rng.random((n, self.rows, self.reels))
        cum = self.cum[phase]
        grid = np.empty(u.shape, dtype=np.int16)
        for r in range(self.reels):
            grid[:, :, r] = np.searchsorted(cum[:, r], u[:, :, r], side="right")
        grid = np.minimum(grid, len(self.p["codes"]) - 1)
        if force_bn is None:
            a_sc = self.rng.random((n, self.reels)) < self.q_sc[phase]
        else:
            # tirage pondéré sans remise (clés d'Efraimidis-Spirakis) des rouleaux qui ont un symbole bonus
            cle = np.log(self.rng.random((n, self.reels))) / np.maximum(self.q_sc[phase], 1e-300)
            rang = np.argsort(np.argsort(-cle, axis=1), axis=1)
            a_sc = rang < force_bn
        rangee = self.rng.integers(0, self.rows, size=(n, self.reels))
        i, r = np.nonzero(a_sc)
        grid[i, rangee[i, r], r] = self.sc
        if self.garanti.get(phase) and self.gl >= 0:
            # Globe garanti (comme game_override.ensure_globe du SDK) : sans globe sur la grille de
            # départ, une case au hasard (hors symbole bonus) devient un globe.
            sans = np.flatnonzero(~(grid == self.gl).any(axis=(1, 2)))
            if sans.size:
                score = self.rng.random((sans.size, self.rows, self.reels))
                score[grid[sans] == self.sc] = -1.0
                case = score.reshape(sans.size, -1).argmax(axis=1)
                grid[sans, case // self.reels, case % self.reels] = self.gl
        return grid

    def spin(self, n, phase, force_bn=None):
        """Joue n spins. Renvoie (gain x mise, nb symboles bonus à la fin, a_un_globe,
        gains par symbole, nb symboles bonus sur la grille de départ)."""
        if self.p["mode_gain"] == "CLUSTER":
            return self._spin_cluster(n, phase, force_bn)
        grid = self._tirage(n, phase, force_bn)
        n_bonus = (grid == self.sc).sum(axis=(1, 2))
        globe, voisin, mult = self.transformer(grid, phase)
        g = self.evaluer(grid, globe | voisin, mult)        # (n, nb symboles)
        return g.sum(axis=1), n_bonus, (globe | voisin).any(axis=(1, 2)), g.sum(axis=0), n_bonus

    def transformer(self, grid, phase):
        """Les 8 cases autour de chaque globe deviennent des multiplicateurs
        (sauf symboles bonus et autres globes, qui restent en place). Renvoie (globe, voisin, mult)."""
        p = self.p
        if self.gl >= 0:
            globe = grid == self.gl
        else:
            globe = np.zeros(grid.shape, dtype=bool)
        pad = np.pad(globe, ((0, 0), (1, 1), (1, 1)))
        voisin = np.zeros_like(globe)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    voisin |= pad[:, 1 + dr:1 + dr + self.rows, 1 + dc:1 + dc + self.reels]
        voisin &= ~globe & (grid != self.sc)

        mult = np.zeros(grid.shape)
        nv = int(voisin.sum())
        if nv:
            mult[voisin] = self.rng.choice(p["multi_val"], size=nv, p=self.mprob[phase])
        mult[globe] = p["multi_globe"]
        return globe, voisin, mult

    def evaluer(self, grid, speciale, mult):
        """Gains de chaque spin par symbole, (n, nb symboles), en x mise."""
        p = self.p
        # Les cases spéciales (globe + multis) ne comptent jamais comme symbole naturel.
        nat_grid = np.where(speciale, -1, grid)
        if p["mode"] == "GLOBAL_SUM":
            wild = np.zeros_like(speciale)
        else:
            wild = speciale
        if p["mode_gain"] == "WAYS":
            g = self._ways(nat_grid, wild, mult)
        else:
            g = self._lignes(nat_grid, wild, mult)
        if p["mode"] == "GLOBAL_SUM":
            spin_mult = mult.sum(axis=(1, 2))
            spin_mult[spin_mult == 0] = 1.0
            g *= spin_mult[:, None]
        return g

    def _ways(self, nat_grid, wild, mult):
        """Gains en ways, gauche → droite. Renvoie (n, nb symboles)."""
        p = self.p
        n = nat_grid.shape[0]
        # Règles alignées sur le math SDK de Stake Engine (src/calculations/ways.py) :
        # une way doit commencer par le symbole NATUREL sur le rouleau 1 ; ensuite les
        # wilds comptent sur chaque rouleau. Les ways 100 % wild ne paient pas.
        w = wild.sum(axis=1).astype(float)                 # wilds par rouleau
        S = (mult * wild).sum(axis=1)                      # somme des multis des wilds, par rouleau
        big = wild & (mult > 1)
        nb_big = big.sum(axis=1).astype(float)             # wilds avec un multi > 1
        S_big = (mult * big).sum(axis=1)
        out = np.zeros((n, len(p["codes"])))
        for s in self.pay_idx:
            nat = (nat_grid == s).sum(axis=1).astype(float)
            c = nat + w
            amorce = nat[:, 0] > 0
            for j, k in enumerate((3, 4, 5)):
                pay = p["pays"][s, j]
                if pay == 0:
                    continue
                if p["mode"] == "WILD_MULT":
                    # multi d'une way = produit des multis de ses wilds
                    ways = np.prod(nat[:, :k] + S[:, :k], axis=1)
                else:
                    # multi d'une way = somme de ses multis > 1 (1 si aucun)
                    ways = np.prod(c[:, :k] - nb_big[:, :k], axis=1)
                    for r in range(k):
                        autres = [i for i in range(k) if i != r]
                        ways += S_big[:, r] * np.prod(c[:, autres], axis=1)
                ways = ways * amorce
                if k < self.reels:
                    ways = ways * (c[:, k] == 0)           # longueur exacte k
                out[:, s] += pay * ways
        return out

    def _lignes(self, nat_grid, wild, mult):
        """Gains en lignes, gauche → droite, mêmes règles que Lines.get_lines du math SDK :
        la ligne paie soit le 1er symbole naturel (avec les wilds avant et après lui), soit la
        suite de wilds du début (payée comme le symbole le plus fort) : on garde le plus gros
        gain AVANT multiplicateur, puis on applique les multis des cases gagnantes.
        Renvoie (n, nb symboles)."""
        p = self.p
        n = nat_grid.shape[0]
        L = p["lignes"]                                    # (nb lignes, 5), indices de rangée
        cols = np.arange(self.reels)
        nat = nat_grid[:, L, cols]                         # (n, nb lignes, 5)
        wl = wild[:, L, cols]
        ml = np.where(wl, mult[:, L, cols], 0.0)

        def multi(cases):
            if p["mode"] == "WILD_MULT":
                return np.prod(np.where(cases & wl, ml, 1.0), axis=2)
            # comme le SDK (apply_added_symbol_mult) : somme des multis > 1, sinon 1
            somme = np.where(cases & (ml > 1), ml, 0.0).sum(axis=2)
            return np.where(somme > 0, somme, 1.0)

        def table(s, longueur):
            pay = np.zeros(longueur.shape)
            for j, k in enumerate((3, 4, 5)):
                pay[longueur == k] = p["pays"][s, j]
            return pay

        # Suite de wilds au début de la ligne, puis 1er symbole naturel
        prefixe = np.cumprod(wl, axis=2).astype(bool)
        a = prefixe.sum(axis=2)
        premier = np.take_along_axis(nat, np.minimum(a, self.reels - 1)[..., None], axis=2)[..., 0]
        premier = np.where(a < self.reels, premier, -1)

        gain_wild = table(self.top, a) if p["mode"] != "GLOBAL_SUM" else np.zeros(a.shape)
        gain_base = np.zeros(a.shape)
        run_base = np.zeros(nat.shape, dtype=bool)
        sym_base = np.full(a.shape, -1)
        for s in self.pay_idx:
            sel = premier == s
            if not sel.any():
                continue
            run = np.cumprod((nat == s) | wl, axis=2).astype(bool)
            g = table(s, run.sum(axis=2))
            gain_base = np.where(sel, g, gain_base)
            run_base = np.where(sel[..., None], run, run_base)
            sym_base = np.where(sel, s, sym_base)

        wild_gagne = gain_wild > gain_base
        gain = np.where(wild_gagne, gain_wild * multi(prefixe), gain_base * multi(run_base))
        sym = np.where(wild_gagne, self.top, sym_base)
        out = np.zeros((n, len(p["codes"])))
        for s in self.pay_idx:
            out[:, s] = np.where(sym == s, gain, 0.0).sum(axis=1)
        return out

    # ----------------------------------------------------------------- clusters + cascades
    def _spin_cluster(self, n, phase, force_bn=None):
        """Mode CLUSTER, mêmes règles que le math SDK (src/calculations/cluster.py + tumble.py) :
        groupes de symboles identiques reliés horizontalement/verticalement, les wilds relient ;
        multi d'un cluster = somme des multis qu'il contient (1 si aucun) ; les cases gagnantes
        explosent et de nouveaux symboles tombent (cascades) jusqu'à ce qu'il n'y ait plus de gain.
        Les globes qui arrivent sur la grille (au départ ou en cascade) transforment leurs voisins."""
        G = self._tirage(n, phase, force_bn).astype(np.int16)
        n_depart = (G == self.sc).sum(axis=(1, 2))
        Mu = np.zeros(G.shape)
        nouveau = np.ones(G.shape, dtype=bool)
        par_sym = np.zeros((n, len(self.p["codes"])))
        a_globe = np.zeros(n, dtype=bool)
        idx = np.arange(n)
        while True:
            grid, mult, nv = G[idx], Mu[idx], nouveau[idx]
            self._activer_globes(grid, mult, nv, phase)
            a_globe[idx] |= ((grid == MULTI) | (grid == self.gl)).any(axis=(1, 2))
            g, explose = self._clusters(grid, mult)
            par_sym[idx] += g
            G[idx], Mu[idx] = grid, mult
            suite = explose.any(axis=(1, 2))
            if not self.p["cascades"] or not suite.any():
                break
            idx = idx[suite]
            grid, mult, nv = self._tomber(grid[suite], mult[suite], explose[suite], phase)
            G[idx], Mu[idx], nouveau[idx] = grid, mult, nv
        n_bonus = (G == self.sc).sum(axis=(1, 2))
        return par_sym.sum(axis=1), n_bonus, a_globe, par_sym.sum(axis=0), n_depart

    def _activer_globes(self, grid, mult, nouveau, phase):
        """Les globes qui viennent d'arriver transforment leurs 8 voisins en multiplicateurs
        (sauf symboles bonus, globes et cases déjà multiplicateur). Modifie grid et mult sur place."""
        if self.gl < 0:
            return
        globe = (grid == self.gl) & nouveau
        if not globe.any():
            return
        mult[globe] = self.p["multi_globe"]
        pad = np.pad(globe, ((0, 0), (1, 1), (1, 1)))
        voisin = np.zeros_like(globe)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    voisin |= pad[:, 1 + dr:1 + dr + self.rows, 1 + dc:1 + dc + self.reels]
        voisin &= (grid != self.sc) & (grid != self.gl) & (grid != MULTI)
        nv = int(voisin.sum())
        if nv:
            grid[voisin] = MULTI
            mult[voisin] = self.rng.choice(self.p["multi_val"], size=nv, p=self.mprob[phase])

    def _clusters(self, grid, mult):
        """Gains par symbole (n, nb symboles) et cases qui explosent (n, lignes, rouleaux)."""
        p = self.p
        n = grid.shape[0]
        nc = self.rows * self.reels
        if p["mode"] == "GLOBAL_SUM":
            wild = np.zeros(grid.shape, dtype=bool)
        else:
            wild = (grid == MULTI) | (grid == self.gl)
        base = np.arange(n * nc).reshape(grid.shape)
        GRAND = n * nc
        out = np.zeros((n, len(p["codes"])))
        explose = np.zeros(grid.shape, dtype=bool)
        for s in self.pay_idx:
            nat = grid == s
            if not nat.any():
                continue
            M = nat | wild
            lab = np.where(M, base, GRAND)
            while True:                                    # composantes connexes (4 voisins)
                nouv = lab.copy()
                nouv[:, 1:, :] = np.minimum(nouv[:, 1:, :], lab[:, :-1, :])
                nouv[:, :-1, :] = np.minimum(nouv[:, :-1, :], lab[:, 1:, :])
                nouv[:, :, 1:] = np.minimum(nouv[:, :, 1:], lab[:, :, :-1])
                nouv[:, :, :-1] = np.minimum(nouv[:, :, :-1], lab[:, :, 1:])
                nouv = np.where(M, nouv, GRAND)
                if np.array_equal(nouv, lab):
                    break
                lab = nouv
            ids, inv = np.unique(lab[M], return_inverse=True)
            taille = np.bincount(inv)
            n_nat = np.bincount(inv, weights=nat[M])
            somme_m = np.bincount(inv, weights=mult[M] * wild[M])
            pay = self.pay_taille[s][taille]
            valide = (n_nat > 0) & (pay > 0)
            gain = pay * np.where(somme_m > 0, somme_m, 1.0) * valide
            out[:, s] = np.bincount(ids // nc, weights=gain, minlength=n)
            e = np.zeros(grid.shape, dtype=bool)
            e[M] = valide[inv]
            explose |= e
        if p["mode"] == "GLOBAL_SUM":
            bm = mult.sum(axis=(1, 2))
            out *= np.where(bm > 0, bm, 1.0)[:, None]
        return out, explose

    def _tomber(self, grid, mult, explose, phase):
        """Retire les cases gagnantes, fait tomber le reste, remplit le haut de chaque rouleau."""
        cle = (~explose).astype(np.int8)                   # 0 = case retirée (remonte en haut)
        ordre = np.argsort(cle, axis=1, kind="stable")
        grid = np.take_along_axis(grid, ordre, axis=1)
        mult = np.take_along_axis(mult, ordre, axis=1)
        nouveau = np.take_along_axis(cle, ordre, axis=1) == 0
        u = self.rng.random(grid.shape)
        cum = self.cum_complet[phase]
        tir = np.empty(grid.shape, dtype=np.int16)
        for r in range(self.reels):
            tir[:, :, r] = np.searchsorted(cum[:, r], u[:, :, r], side="right")
        tir = np.minimum(tir, len(self.p["codes"]) - 1)
        grid = np.where(nouveau, tir, grid)
        mult = np.where(nouveau, 0.0, mult)
        return grid, mult, nouveau

    def loi_depart(self, phase):
        """Loi exacte du nombre de symboles bonus sur la grille de départ (0..5)."""
        dist = np.array([1.0])
        for q in self.q_sc[phase]:
            dist = np.convolve(dist, [1 - q, q])
        return dist

    def type_bonus(self, nb_bonus):
        """Bonus déclenché (0 = aucun, 1..3) selon le nombre de symboles bonus sur la grille finale :
        le bonus le plus fort dont le seuil est atteint."""
        out = np.zeros(len(nb_bonus), dtype=np.int64)
        for k, b in enumerate(self.p["bonus"]):
            out[nb_bonus >= b["bn"]] = k + 1
        return out

    def critere(self, nb_depart):
        """Critère SDK d'un tour qui déclenche un bonus : le SDK force la grille de départ à avoir
        exactement le seuil d'un bonus (critères bonus1 / bonus2 / bonus3). Un départ sous le premier
        seuil (bonus amené par une cascade) est rattaché à bonus1."""
        out = np.ones(len(nb_depart), dtype=np.int64)
        for k, b in enumerate(self.p["bonus"]):
            out[nb_depart >= b["bn"]] = k + 1
        return out

    def sessions_fs(self, fs_init, plafond, phase):
        """Joue des sessions de free spins (phase fs1 / fs2 / fs3).
        Renvoie (gain total, nb de FS joués, gains par symbole)."""
        n = len(fs_init)
        total = np.zeros(n)
        restant = np.asarray(fs_init, dtype=float).copy()
        joues = np.zeros(n, dtype=np.int64)
        par_symbole = np.zeros(len(self.p["codes"]))
        actifs = np.flatnonzero(restant > 0)
        while actifs.size:
            g, tr, _, ps, _ = self.spin(actifs.size, phase)
            total[actifs] += g
            par_symbole += ps
            joues[actifs] += 1
            restant[actifs] += tr * self.p["fs_par_bonus"] - 1
            fini = (restant[actifs] < 1) | (total[actifs] >= plafond) | \
                   (joues[actifs] >= MAX_FS_PAR_SESSION)
            actifs = actifs[~fini]
        return np.minimum(total, plafond), joues, par_symbole


# --------------------------------------------------------------------------- #
# Simulation complète
# --------------------------------------------------------------------------- #
# Disposition de l'onglet « Simulation » (partagée avec la génération du classeur et l'exporteur)
NUM, PCT, X2 = "#,##0", "0.00%", '0.00"x"'
LIGNES_MODE = [   # colonnes B = jeu de base, C = spins boostés
    ("date", "Date de la simulation", None),
    ("spins", "Spins simulés", NUM),
    ("cout", "Coût d'un spin (x mise)", "0.00"),
    ("rtp_base", "RTP des spins (hors bonus)", PCT),
    ("rtp_fs", "RTP des bonus", PCT),
    ("rtp_total", "RTP total", PCT),
    ("marge", "Marge d'erreur RTP (± à 95 %)", "0.000%"),
    ("hit", "Hit frequency", PCT),
    ("ecart_type", "Écart-type par tour (x mise)", "0.00"),
    ("trig", "Bonus (tous) : 1 spin sur", NUM),
    *[(f"trig{k}", f"Bonus {k} : 1 spin sur", NUM) for k in (1, 2, 3)],
    *[(f"gain{k}", f"Bonus {k} : gain moyen (x mise)", X2) for k in (1, 2, 3)],
    *[(f"fsm{k}", f"Bonus {k} : FS joués en moyenne", "0.00") for k in (1, 2, 3)],
    ("max", "Max win observé (x mise)", X2),
    ("globe", "Spins avec au moins 1 globe", PCT),
    ("etl40b", "3 étoiles : etl40b (limite 0,9)", "0.000"),
    ("etl10k", "3 étoiles : etl10k (limite 0,8)", "0.000"),
    ("pmax", "Max win atteint : 1 tour sur", NUM),
    # probabilité par spin d'un tour bonus, selon le critère SDK (grille de départ) et le bonus obtenu
    *[(f"joint{c}{k}", None, "0.000000%") for c in (1, 2, 3) for k in (1, 2, 3)],
]
LIGNES_BONUS = [  # colonnes B, C, D = bonus 1, 2, 3 (sessions jouées directement, comme un achat)
    ("b_sessions", "Sessions simulées", NUM),
    ("b_prix", "Prix d'achat (x mise)", NUM),
    ("b_gain", "Gain moyen (x mise)", X2),
    ("b_rtp", "RTP au prix actuel", PCT),
    ("b_conseil", "Prix conseillé (gain moyen / RTP cible)", "0.0"),
    ("b_mediane", "Gain médian (x mise)", X2),
    ("b_max", "Max win observé (x mise)", X2),
    ("b_etl40b", "3 étoiles : etl40b (limite 0,9)", "0.000"),
    ("b_etl10k", "3 étoiles : etl10k (limite 0,8)", "0.000"),
]
SIM_LIGNE = {k: 5 + i for i, (k, _, _) in enumerate(LIGNES_MODE)}
SIM_BONUS0 = 5 + len(LIGNES_MODE) + 2          # ligne d'en-tête du bloc des bonus
SIM_LIGNE.update({k: SIM_BONUS0 + 1 + i for i, (k, _, _) in enumerate(LIGNES_BONUS)})
SIM_SYM0 = SIM_BONUS0 + len(LIGNES_BONUS) + 3   # ligne d'en-tête du RTP par symbole
COL_MODE = {"base": "B", "boost": "C"}
COL_BONUS = {1: "B", 2: "C", 3: "D"}


def cellule(cle, col):
    """Adresse d'une cellule de l'onglet Simulation (ex. cellule("rtp_total", "B") -> "B10")."""
    return f"{col}{SIM_LIGNE[cle]}"


def _stats_ponderees(r, w, cout, cap):
    """Statistiques d'un tableau de gains r (x mise) avec des poids w (somme 1)."""
    moy = float((w * r).sum())
    return {
        "moy": moy,
        "hit": float(w[r > 0].sum()),
        "ecart_type": float(np.sqrt(max((w * r * r).sum() - moy * moy, 0.0))),
        "etl40b": float((w * r)[r >= 40 * cout].sum()),
        "etl10k": float((w * r)[r >= 10_000].sum()),
        "p_max": float(w[r >= cap].sum()),
        "max": float(r.max()) if len(r) else float("nan"),
    }


def _distribution(r, w, cap):
    bornes = DIST_BORNES + [cap]
    dist = [("0 x", float(w[r == 0].sum()))]
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        lbl = f"{lo:g} – {hi:g} x" if hi < cap else f"{lo:g} x – max win"
        sel = (r > lo) & (r < hi) if lo == 0 else (r >= lo) & (r < hi)
        dist.append((lbl, float(w[sel].sum())))
    dist.append(("Max win atteint", float(w[r >= cap].sum())))
    return dist


def jouer_mode(m, phase, spins, cout, lot=100_000, verbose=True, tours=False):
    """Simule un mode de jeu (base ou boost) par strates : la loi du nombre de symboles bonus sur la
    grille de départ est exacte, et chaque strate (0, 1, … 5 symboles bonus) est simulée à part, les
    strates qui déclenchent un bonus étant sur-échantillonnées (le bonus caché est très rare).
    Les résultats sont recombinés avec les vraies probabilités."""
    p = m.p
    cap = p["max_win"]
    nb = len(p["bonus"])
    loi = m.loi_depart(phase)
    seuil = p["bonus"][0]["bn"]
    n_min = max(spins // 100, 2000)               # au moins ça par strate qui déclenche un bonus
    rounds, poids = [], []
    tot = {"base": 0.0, "fs": 0.0, "globe": 0.0}
    par_type = np.zeros((nb + 1, 3))               # [type] -> (proba, gain bonus, FS joués) pondérés
    joint = np.zeros((4, 4))
    sym_base = np.zeros(len(p["codes"]))
    sym_fs = np.zeros(len(p["codes"]))
    var_rtp = 0.0
    for j, pj in enumerate(loi):
        if pj <= 0:
            continue
        n_j = max(int(round(spins * pj)), n_min if j >= seuil else 1)
        w_j = pj / n_j
        r_j = []
        fait = 0
        while fait < n_j:
            n = min(lot, n_j - fait)
            g, n_bn, a_globe, ps, n_dep = m.spin(n, phase, force_bn=j)
            typ = m.type_bonus(n_bn)
            crit = m.critere(n_dep)
            bonus = np.zeros(n)
            joues = np.zeros(n)
            for k in range(1, nb + 1):
                sel = typ == k
                if sel.any():
                    t, jo, psf = m.sessions_fs(np.full(int(sel.sum()), p["bonus"][k - 1]["fs"]), cap, f"fs{k}")
                    bonus[sel], joues[sel] = t, jo
                    sym_fs += w_j * psf
            r = np.minimum(g + bonus, cap)
            bonus_eff = r - np.minimum(g, cap)     # la part plafonnée est retirée du bonus en priorité
            tot["base"] += w_j * np.minimum(g, cap).sum()
            tot["fs"] += w_j * bonus_eff.sum()
            tot["globe"] += w_j * a_globe.sum()
            np.add.at(par_type, (typ, 0), w_j)
            np.add.at(par_type, (typ, 1), w_j * bonus_eff)
            np.add.at(par_type, (typ, 2), w_j * joues)
            dec = typ > 0
            np.add.at(joint, (crit[dec], typ[dec]), w_j)
            sym_base += w_j * ps
            r_j.append(r)
            fait += n
            if verbose:
                print(f"\r  {phase} : strate {j} symbole(s) bonus au départ, {fait:,}/{n_j:,} spins   ",
                      end="", file=sys.stderr)
        r_j = np.concatenate(r_j)
        var_rtp += pj * pj * r_j.var() / len(r_j)
        rounds.append(r_j)
        poids.append(np.full(len(r_j), w_j))
    if verbose:
        print(file=sys.stderr)
    r, w = np.concatenate(rounds), np.concatenate(poids)
    s = _stats_ponderees(r, w, cout, cap)
    res = {
        "spins": int(len(r)), "cout": cout,
        "rtp_base": tot["base"] / cout, "rtp_fs": tot["fs"] / cout, "rtp_total": s["moy"] / cout,
        "marge": 1.96 * np.sqrt(var_rtp) / cout, "hit": s["hit"], "ecart_type": s["ecart_type"],
        "trig": 1 / par_type[1:, 0].sum(), "max": s["max"], "globe": tot["globe"],
        "etl40b": s["etl40b"], "etl10k": s["etl10k"],
        "pmax": 1 / s["p_max"] if s["p_max"] > 0 else float("nan"),
        "dist": _distribution(r, w, cap), "sym_base": sym_base, "sym_fs": sym_fs,
        "joint": joint[1:, 1:].tolist(),
    }
    if tours:                                      # gains et poids de chaque tour simulé (pour le calage)
        res["tours"] = (r, w)
    for k in range(1, 4):
        ok = k <= nb and par_type[k, 0] > 0
        res[f"trig{k}"] = 1 / par_type[k, 0] if ok else float("nan")
        res[f"gain{k}"] = par_type[k, 1] / par_type[k, 0] if ok else float("nan")
        res[f"fsm{k}"] = par_type[k, 2] / par_type[k, 0] if ok else float("nan")
    for c in (1, 2, 3):
        for k in (1, 2, 3):
            res[f"joint{c}{k}"] = float(joint[c, k])
    return res


def jouer_bonus(m, k, sessions, lot=10_000, verbose=True):
    """Joue des tours « bonus k » directement, comme un achat : spin de déclenchement (grille de base
    avec le seuil de symboles bonus du bonus k), puis les FS du bonus k."""
    p = m.p
    cap = p["max_win"]
    b = p["bonus"][k - 1]
    parts = []
    for i in range(0, sessions, lot):
        n = min(lot, sessions - i)
        g = m.spin(n, "base", force_bn=b["bn"])[0]
        t, _, _ = m.sessions_fs(np.full(n, b["fs"]), cap, f"fs{k}")
        parts.append(np.minimum(g + t, cap))
        if verbose:
            print(f"\r  bonus {k} : {i + n:,}/{sessions:,} sessions", end="", file=sys.stderr)
    if verbose:
        print(file=sys.stderr)
    t = np.concatenate(parts)
    w = np.full(len(t), 1 / len(t))
    prix = b["prix"]
    s = _stats_ponderees(t, w, prix or 1.0, cap)
    return {
        "b_sessions": len(t), "b_prix": prix, "b_gain": s["moy"],
        "b_rtp": s["moy"] / prix if prix else None,
        "b_conseil": s["moy"] / p["rtp_cible"],
        "b_mediane": float(np.median(t)), "b_max": s["max"],
        "b_etl40b": s["etl40b"] if prix else None, "b_etl10k": s["etl10k"] if prix else None,
        "dist": _distribution(t, w, cap),
    }


def simuler(p, spins=None, boost=None, buy=None, verbose=True):
    rng = np.random.default_rng(p["seed"])
    m = Moteur(p, rng)
    spins = spins or p["sim_spins"]
    boost = p["sim_boost"] if boost is None else boost
    buy = p["sim_buy"] if buy is None else buy
    res = {"date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "modes": {}, "bonus": {}}
    res["modes"]["base"] = jouer_mode(m, "base", spins, 1.0, verbose=verbose)
    if boost:
        res["modes"]["boost"] = jouer_mode(m, "boost", boost, p["boost_cout"], verbose=verbose)
    if buy:
        for k in range(1, len(p["bonus"]) + 1):
            res["bonus"][k] = jouer_bonus(m, k, buy, verbose=verbose)
    return res


def _f(v, fmt):
    return "-" if v is None or v != v else format(v, fmt)


def afficher(p, r):
    noms = {"base": "JEU DE BASE (1x)", "boost": f"SPINS BOOSTÉS ({p['boost_cout']:g}x)"}
    for mode, s in r["modes"].items():
        print(f"\n{noms[mode]} — {s['spins']:,} spins simulés")
        print(f"  RTP total        : {s['rtp_total']:.3%}  (± {s['marge']:.3%})  cible {p['rtp_cible']:.2%}"
              f"   [spins {s['rtp_base']:.2%} + bonus {s['rtp_fs']:.2%}]")
        print(f"  Hit frequency    : {s['hit']:.2%}   écart-type {s['ecart_type']:.1f}x   max {s['max']:.0f}x")
        print(f"  Bonus            : 1 spin sur {s['trig']:.0f}")
        for k, b in enumerate(p["bonus"], 1):
            print(f"    {k}. {b['nom']:<16}: 1 spin sur {_f(s[f'trig{k}'], ',.0f'):>9}, gain moyen "
                  f"{_f(s[f'gain{k}'], '.1f')}x, {_f(s[f'fsm{k}'], '.1f')} FS joués")
        print(f"  3 étoiles        : etl40b {s['etl40b']:.3f} (≤ 0,9)  etl10k {s['etl10k']:.3f} (≤ 0,8)  "
              f"max win 1 tour sur {_f(s['pmax'], ',.0f')}")
    for k, s in r["bonus"].items():
        b = p["bonus"][k - 1]
        prix = f"prix {b['prix']:g}x -> RTP {s['b_rtp']:.2%}" if b["prix"] else "non achetable"
        print(f"\nBONUS {k} ({b['nom']}) joué directement, {s['b_sessions']:,} sessions : gain moyen "
              f"{s['b_gain']:.1f}x, médiane {s['b_mediane']:.1f}x, max {s['b_max']:.0f}x ; {prix} "
              f"(prix conseillé {s['b_conseil']:.0f}x)")
        if b["prix"]:
            print(f"  3 étoiles : etl40b {s['b_etl40b']:.3f} (≤ 0,9)  etl10k {s['b_etl10k']:.3f} (≤ 0,8)")


# --------------------------------------------------------------------------- #
# Écriture dans l'onglet Simulation (disposition : LIGNES_MODE / LIGNES_BONUS)
# --------------------------------------------------------------------------- #
def libelle_joint(p, c, k):
    b = p["bonus"]
    if c > len(b) or k > len(b):
        return f"(critère {c}, bonus {k} : inutilisé)"
    dep = f"{b[c - 1]['bn']} symboles bonus" if c > 1 else f"{b[0]['bn']} symboles bonus ou moins"
    return f"P(départ {dep} → bonus {k})"


def ecrire(path, p, r):
    wb = load_workbook(path)
    ws = wb["Simulation"]

    def put(row, col, v, fmt=None):
        c = ws[f"{col}{row}"]
        c.value = None if v is None or (isinstance(v, float) and v != v) else v
        if fmt:
            c.number_format = fmt

    for key, lbl, fmt in LIGNES_MODE:
        row = SIM_LIGNE[key]
        if key.startswith("joint"):
            lbl = libelle_joint(p, int(key[5]), int(key[6]))
        put(row, "A", lbl)
        for mode, col in COL_MODE.items():
            s = r["modes"].get(mode)
            v = (r["date"] if key == "date" else s.get(key)) if s else None
            put(row, col, v, fmt)
    for key, lbl, fmt in LIGNES_BONUS:
        row = SIM_LIGNE[key]
        put(row, "A", lbl)
        for k, col in COL_BONUS.items():
            s = r["bonus"].get(k)
            put(row, col, s.get(key) if s else None, fmt)

    # Distribution des gains : F = tranche, G = base, H = boost
    for i in range(15):
        for col in "FGH":
            put(5 + i, col, None)
    for mode, col in (("base", "G"), ("boost", "H")):
        s = r["modes"].get(mode)
        if not s:
            continue
        for i, (lbl, v) in enumerate(s["dist"]):
            put(5 + i, "F", lbl)
            put(5 + i, col, v, "0.0000%")

    # RTP par symbole (jeu de base) : lignes SIM_SYM0 + 1 et suivantes
    for i in range(30):
        for col in "ABCD":
            put(SIM_SYM0 + 1 + i, col, None)
    s = r["modes"]["base"]
    j = 0
    for i, t in enumerate(p["types"]):
        if t != "PAY":
            continue
        row = SIM_SYM0 + 1 + j
        put(row, "A", p["codes"][i])
        put(row, "B", p["noms"][i])
        put(row, "C", float(s["sym_base"][i]), PCT)
        put(row, "D", float(s["sym_fs"][i]), PCT)
        j += 1

    wb.calculation.fullCalcOnLoad = True  # Excel recalcule tout à l'ouverture
    wb.save(path)


def lire_simulation(path):
    """Relit l'onglet Simulation : {"base": {clé: valeur}, "boost": {...}, "bonus": {1: {...}, ...}}."""
    ws = load_workbook(path)["Simulation"]
    out = {mode: {k: ws[f"{col}{SIM_LIGNE[k]}"].value for k, _, _ in LIGNES_MODE}
           for mode, col in COL_MODE.items()}
    out["bonus"] = {k: {key: ws[f"{col}{SIM_LIGNE[key]}"].value for key, _, _ in LIGNES_BONUS}
                    for k, col in COL_BONUS.items()}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--spins", type=int, help="remplace « Spins de base simulés »")
    ap.add_argument("--boost", type=int, help="remplace « Spins boostés simulés » (0 = pas de simulation)")
    ap.add_argument("--buy", type=int, help="remplace « Sessions par bonus simulées » (0 = aucune)")
    ap.add_argument("--no-write", action="store_true", help="n'écrit pas dans le classeur")
    a = ap.parse_args()

    p = load_params(a.classeur)
    r = simuler(p, spins=a.spins, boost=a.boost, buy=a.buy)
    afficher(p, r)
    if not a.no_write:
        ecrire(a.classeur, p, r)
        print(f"\nRésultats écrits dans l'onglet « Simulation » de {a.classeur}")


if __name__ == "__main__":
    main()
