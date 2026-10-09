#!/usr/bin/env python3
"""
Simulateur Monte Carlo pour le modèle de maths (grille 5 rouleaux,
gains en lignes ou en ways, globe qui fait apparaître des multiplicateurs autour de lui,
free spins avec +1 FS par symbole bonus).

Il lit tous les paramètres dans le classeur Excel (plages nommées) et réécrit
les résultats dans l'onglet « Simulation ».

    python simulateur.py modele_maths.xlsx
    python simulateur.py modele_maths.xlsx --spins 500000 --buy 20000
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
    table_fs = [r for r in _name_range(wb, "TABLE_FS") if r[0] not in (None, "")]
    lignes = [[int(v) - 1 for v in r] for r in _name_range(wb, "LIGNES")
              if all(v not in (None, "") for v in r)]
    tailles = [int(v) for v in _name_range(wb, "TAILLES_CLUSTER")[0] if v not in (None, "")]
    pay_cl = [[float(v or 0) for v in r[:len(tailles)]] for r in _name_range(wb, "PAYTABLE_CLUSTER")[:n_sym]]

    p = {
        "codes": [r[0] for r in pay_rows],
        "noms": [r[1] for r in pay_rows],
        "types": [str(r[2]).strip().upper() for r in pay_rows],
        "pays": np.array([[float(v or 0) for v in r[3:6]] for r in pay_rows]),  # 3,4,5 OAK
        "tailles": tailles,                               # taille mini de chaque groupe de la paytable cluster
        "pays_cluster": np.array(pay_cl).reshape(n_sym, len(tailles)),
        "cascades": str(_name_value(wb, "CASCADES")).strip().upper() in ("OUI", "YES", "TRUE", "1"),
        "poids_base": weights("POIDS_BASE"),
        "poids_fs": weights("POIDS_FS"),
        "multi_val": np.array([float(r[0]) for r in multis]),
        "multi_w_base": np.array([float(r[1] or 0) for r in multis]),
        "multi_w_fs": np.array([float(r[2] or 0) for r in multis]),
        "table_fs": sorted((int(r[0]), int(r[1])) for r in table_fs),
        "lignes": np.array(lignes, dtype=np.int64).reshape(-1, 5),
        "rows": int(_name_value(wb, "NB_LIGNES")),
        "mode_gain": str(_name_value(wb, "MODE_GAIN")).strip().upper(),
        "rtp_cible": float(_name_value(wb, "RTP_CIBLE")),
        "max_win": float(_name_value(wb, "MAX_WIN")),
        "mode": str(_name_value(wb, "MODE_MULTI")).strip().upper(),
        "multi_globe": float(_name_value(wb, "MULTI_GLOBE")),
        "scatter_min": int(_name_value(wb, "SCATTER_MIN")),
        "fs_par_bonus": float(_name_value(wb, "FS_PAR_BONUS")),
        "buy_cout": float(_name_value(wb, "BUY_COUT")),
        "buy_fs": int(_name_value(wb, "BUY_FS")),
        "sim_spins": int(_name_value(wb, "SIM_SPINS")),
        "sim_buy": int(_name_value(wb, "SIM_BUY")),
        "seed": int(_name_value(wb, "SIM_SEED")),
    }
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
    for w in (p["poids_base"], p["poids_fs"]):
        if (w.sum(axis=0) <= 0).any():
            sys.exit("Chaque rouleau doit avoir un poids total > 0.")
    if p["multi_w_base"].sum() <= 0 or p["multi_w_fs"].sum() <= 0:
        sys.exit("Les poids des multiplicateurs doivent avoir une somme > 0.")


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
        self.prob = {
            "base": p["poids_base"] / p["poids_base"].sum(axis=0),
            "fs": p["poids_fs"] / p["poids_fs"].sum(axis=0),
        }
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
        self.mprob = {
            "base": p["multi_w_base"] / p["multi_w_base"].sum(),
            "fs": p["multi_w_fs"] / p["multi_w_fs"].sum(),
        }

    def _tirage(self, n, phase):
        """Grille (n, lignes, rouleaux) d'indices de symboles, au plus 1 symbole bonus par rouleau."""
        u = self.rng.random((n, self.rows, self.reels))
        cum = self.cum[phase]
        grid = np.empty(u.shape, dtype=np.int16)
        for r in range(self.reels):
            grid[:, :, r] = np.searchsorted(cum[:, r], u[:, :, r], side="right")
        grid = np.minimum(grid, len(self.p["codes"]) - 1)
        a_sc = self.rng.random((n, self.reels)) < self.q_sc[phase]
        rangee = self.rng.integers(0, self.rows, size=(n, self.reels))
        i, r = np.nonzero(a_sc)
        grid[i, rangee[i, r], r] = self.sc
        return grid

    def spin(self, n, phase):
        """Joue n spins. Renvoie (gain x mise, nb symboles bonus, a_un_globe, gains par symbole)."""
        if self.p["mode_gain"] == "CLUSTER":
            return self._spin_cluster(n, phase)
        grid = self._tirage(n, phase)
        n_bonus = (grid == self.sc).sum(axis=(1, 2))
        globe, voisin, mult = self.transformer(grid, phase)
        g = self.evaluer(grid, globe | voisin, mult)        # (n, nb symboles)
        return g.sum(axis=1), n_bonus, (globe | voisin).any(axis=(1, 2)), g.sum(axis=0)

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
    def _spin_cluster(self, n, phase):
        """Mode CLUSTER, mêmes règles que le math SDK (src/calculations/cluster.py + tumble.py) :
        groupes de symboles identiques reliés horizontalement/verticalement, les wilds relient ;
        multi d'un cluster = somme des multis qu'il contient (1 si aucun) ; les cases gagnantes
        explosent et de nouveaux symboles tombent (cascades) jusqu'à ce qu'il n'y ait plus de gain.
        Les globes qui arrivent sur la grille (au départ ou en cascade) transforment leurs voisins."""
        G = self._tirage(n, phase).astype(np.int16)
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
        return par_sym.sum(axis=1), n_bonus, a_globe, par_sym.sum(axis=0)

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

    def fs_initiaux(self, nb_bonus):
        table = self.p["table_fs"]
        out = np.zeros(len(nb_bonus), dtype=np.int64)
        for seuil, fs in table:                 # table triée : le dernier seuil couvre « et plus »
            out[nb_bonus >= seuil] = fs
        return out

    def sessions_fs(self, fs_init, plafond):
        """Joue des sessions de free spins. Renvoie (gain total, nb de FS joués, gains par symbole)."""
        n = len(fs_init)
        total = np.zeros(n)
        restant = fs_init.astype(float).copy()
        joues = np.zeros(n, dtype=np.int64)
        par_symbole = np.zeros(len(self.p["codes"]))
        actifs = np.flatnonzero(restant > 0)
        while actifs.size:
            g, tr, _, ps = self.spin(actifs.size, "fs")
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
def simuler(p, spins=None, buy=None, lot=100_000, verbose=True):
    rng = np.random.default_rng(p["seed"])
    m = Moteur(p, rng)
    spins = spins or p["sim_spins"]
    buy = p["sim_buy"] if buy is None else buy
    cap = p["max_win"]

    rounds = []
    base_total = fs_total = 0.0
    globe_spins = globe_gain = 0.0
    nb_bonus = fs_joues = 0
    sym_base = np.zeros(len(p["codes"]))
    sym_fs = np.zeros(len(p["codes"]))
    fait = 0
    while fait < spins:
        n = min(lot, spins - fait)
        g, tr, a_globe, ps = m.spin(n, "base")
        sym_base += ps
        bonus = np.zeros(n)
        decl = tr >= p["scatter_min"]
        if decl.any():
            tot, joues, psf = m.sessions_fs(m.fs_initiaux(tr[decl]), cap)
            bonus[decl] = tot
            sym_fs += psf
            nb_bonus += int(decl.sum())
            fs_joues += int(joues.sum())
        r = np.minimum(g + bonus, cap)
        # la part plafonnée est retirée du bonus en priorité
        bonus_eff = r - np.minimum(g, cap)
        base_total += np.minimum(g, cap).sum()
        fs_total += bonus_eff.sum()
        globe_spins += a_globe.sum()
        globe_gain += np.minimum(g, cap)[a_globe].sum()
        rounds.append(r)
        fait += n
        if verbose:
            print(f"\r  jeu de base : {fait:,}/{spins:,} spins", end="", file=sys.stderr)
    if verbose:
        print(file=sys.stderr)
    rounds = np.concatenate(rounds)

    buy_tot = np.array([])
    if buy:
        parts = []
        for i in range(0, buy, lot // 10):
            k = min(lot // 10, buy - i)
            t, _, _ = m.sessions_fs(np.full(k, p["buy_fs"]), cap)
            parts.append(t)
            if verbose:
                print(f"\r  bonus buy : {i + k:,}/{buy:,} sessions", end="", file=sys.stderr)
        if verbose:
            print(file=sys.stderr)
        buy_tot = np.concatenate(parts)

    N = len(rounds)
    bornes = DIST_BORNES + [cap]
    dist = [("0 x", float((rounds == 0).mean()))]
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        lbl = f"{lo:g} – {hi:g} x" if hi < cap else f"{lo:g} x – max win"
        sel = (rounds > lo) & (rounds < hi) if lo == 0 else (rounds >= lo) & (rounds < hi)
        dist.append((lbl, float(sel.mean())))
    dist.append(("Max win atteint", float((rounds >= cap).mean())))

    res = {
        "date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "spins": N,
        "sessions_buy": len(buy_tot),
        "rtp_base": base_total / N,
        "rtp_fs": fs_total / N,
        "rtp_total": rounds.mean(),
        "erreur_std": rounds.std() / np.sqrt(N),
        "hit_freq": float((rounds > 0).mean()),
        "ecart_type": float(rounds.std()),
        "trigger_1_sur": N / nb_bonus if nb_bonus else float("nan"),
        "fs_moyens": fs_joues / nb_bonus if nb_bonus else float("nan"),
        "gain_bonus_naturel": fs_total / nb_bonus if nb_bonus else float("nan"),
        "gain_bonus_buy": float(buy_tot.mean()) if len(buy_tot) else float("nan"),
        "rtp_buy": float(buy_tot.mean() / p["buy_cout"]) if len(buy_tot) else float("nan"),
        "max_observe": float(rounds.max()),
        "max_observe_buy": float(buy_tot.max()) if len(buy_tot) else float("nan"),
        "freq_globe": globe_spins / N,
        "rtp_spins_globe": globe_gain / N,
        "sym_base": sym_base / N,
        "sym_fs": sym_fs / N,
        "dist": dist,
    }
    return res


def afficher(p, r):
    print(f"Spins simulés          : {r['spins']:,}")
    print(f"RTP jeu de base        : {r['rtp_base']:.4%}")
    print(f"RTP free spins         : {r['rtp_fs']:.4%}")
    print(f"RTP total              : {r['rtp_total']:.4%}  (± {1.96 * r['erreur_std']:.3%} à 95 %)"
          f"  cible {p['rtp_cible']:.2%}")
    print(f"Hit frequency          : {r['hit_freq']:.2%}")
    print(f"Écart-type (x mise)    : {r['ecart_type']:.2f}")
    print(f"Bonus 1 spin sur       : {r['trigger_1_sur']:.0f}")
    print(f"FS moyens / bonus      : {r['fs_moyens']:.2f}")
    print(f"Gain moyen bonus       : {r['gain_bonus_naturel']:.2f} x")
    print(f"Gain moyen bonus buy   : {r['gain_bonus_buy']:.2f} x  -> RTP buy {r['rtp_buy']:.2%}")
    print(f"Spins avec globe       : {r['freq_globe']:.2%}")
    print(f"Max win observé        : {r['max_observe']:.1f} x (base)  /  "
          f"{r['max_observe_buy']:.1f} x (buy)")


# --------------------------------------------------------------------------- #
# Écriture dans l'onglet Simulation (cellules fixes, voir le classeur)
# --------------------------------------------------------------------------- #
def ecrire(path, p, r):
    wb = load_workbook(path)
    ws = wb["Simulation"]
    valeurs = [r["date"], r["spins"], r["sessions_buy"], r["rtp_base"], r["rtp_fs"],
               r["rtp_total"], 1.96 * r["erreur_std"], r["hit_freq"], r["ecart_type"],
               r["trigger_1_sur"], r["fs_moyens"], r["gain_bonus_naturel"],
               r["gain_bonus_buy"], r["rtp_buy"], r["max_observe"], r["max_observe_buy"],
               r["freq_globe"], r["rtp_spins_globe"]]
    for i, v in enumerate(valeurs):
        ws.cell(row=5 + i, column=2, value=v if v == v else None)  # NaN -> vide

    # Contribution par symbole : lignes 27+
    for i in range(30):
        for col in (1, 2, 3, 4):
            ws.cell(row=27 + i, column=col, value=None)
    j = 0
    for s, t in enumerate(p["types"]):
        if t != "PAY":
            continue
        ws.cell(row=27 + j, column=1, value=p["codes"][s])
        ws.cell(row=27 + j, column=2, value=p["noms"][s])
        ws.cell(row=27 + j, column=3, value=float(r["sym_base"][s]))
        ws.cell(row=27 + j, column=4, value=float(r["sym_fs"][s]))
        j += 1

    # Distribution des gains : colonnes F:G, lignes 5+
    for i in range(15):
        ws.cell(row=5 + i, column=6, value=None)
        ws.cell(row=5 + i, column=7, value=None)
    for i, (lbl, v) in enumerate(r["dist"]):
        ws.cell(row=5 + i, column=6, value=lbl)
        ws.cell(row=5 + i, column=7, value=v)

    wb.calculation.fullCalcOnLoad = True  # Excel recalcule tout à l'ouverture
    wb.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--spins", type=int, help="remplace « Spins de base simulés »")
    ap.add_argument("--buy", type=int, help="remplace « Sessions bonus buy simulées »")
    ap.add_argument("--no-write", action="store_true", help="n'écrit pas dans le classeur")
    a = ap.parse_args()

    p = load_params(a.classeur)
    r = simuler(p, spins=a.spins, buy=a.buy)
    afficher(p, r)
    if not a.no_write:
        ecrire(a.classeur, p, r)
        print(f"\nRésultats écrits dans l'onglet « Simulation » de {a.classeur}")


if __name__ == "__main__":
    main()
