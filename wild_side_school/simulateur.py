#!/usr/bin/env python3
"""
Simulateur Monte Carlo pour le modèle « Wild Side School » (grille 5 rouleaux,
gains en lignes ou en ways, globe qui fait apparaître des multiplicateurs autour de lui,
free spins avec +1 FS par trophée).

Il lit tous les paramètres dans le classeur Excel (plages nommées) et réécrit
les résultats dans l'onglet « Simulation ».

    python simulateur.py wild_side_school_math.xlsx
    python simulateur.py wild_side_school_math.xlsx --spins 500000 --buy 20000
    python simulateur.py wild_side_school_math.xlsx --no-write   # affiche seulement
"""
import argparse
import datetime as dt
import sys

import numpy as np
from openpyxl import load_workbook

MODES = ("WILD_ADD", "WILD_MULT", "GLOBAL_SUM")
MODES_GAIN = ("LINES", "WAYS")
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

    p = {
        "codes": [r[0] for r in pay_rows],
        "noms": [r[1] for r in pay_rows],
        "types": [str(r[2]).strip().upper() for r in pay_rows],
        "pays": np.array([[float(v or 0) for v in r[3:6]] for r in pay_rows]),  # 3,4,5 OAK
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
        "fs_par_trophee": float(_name_value(wb, "FS_PAR_TROPHEE")),
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
    if p["types"].count("SCATTER") != 1:
        sys.exit("La Paytable doit contenir exactement un symbole de type SCATTER.")
    if p["types"].count("GLOBE") > 1:
        sys.exit("La Paytable doit contenir au plus un symbole de type GLOBE.")
    if "PAY" not in p["types"]:
        sys.exit("La Paytable doit contenir au moins un symbole de type PAY.")
    if p["mode"] == "WILD_ADD" and p["multi_globe"] < 1:
        sys.exit("En mode WILD_ADD, le multi du globe doit être >= 1.")
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
        self.cum = {k: np.cumsum(v, axis=0) for k, v in self.prob.items()}
        self.mprob = {
            "base": p["multi_w_base"] / p["multi_w_base"].sum(),
            "fs": p["multi_w_fs"] / p["multi_w_fs"].sum(),
        }

    def _tirage(self, n, phase):
        """Grille (n, lignes, rouleaux) d'indices de symboles, cases indépendantes."""
        u = self.rng.random((n, self.rows, self.reels))
        cum = self.cum[phase]
        grid = np.empty(u.shape, dtype=np.int16)
        for r in range(self.reels):
            grid[:, :, r] = np.searchsorted(cum[:, r], u[:, :, r], side="right")
        return np.minimum(grid, len(self.p["codes"]) - 1)

    def spin(self, n, phase):
        """Joue n spins. Renvoie (gain x mise, nb trophées, a_un_globe, gains par symbole)."""
        p = self.p
        grid = self._tirage(n, phase)
        trophees = (grid == self.sc).sum(axis=(1, 2))

        if self.gl >= 0:
            globe = grid == self.gl
        else:
            globe = np.zeros(grid.shape, dtype=bool)
        # Les 8 cases autour de chaque globe deviennent des multiplicateurs
        # (sauf trophées et autres globes, qui restent en place).
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
        speciale = globe | voisin

        # Les cases spéciales (globe + multis) ne comptent jamais comme symbole naturel.
        nat_grid = np.where(speciale, -1, grid)
        if p["mode"] == "GLOBAL_SUM":
            wild = np.zeros_like(speciale)
        else:
            wild = speciale
        if p["mode_gain"] == "WAYS":
            g = self._ways(nat_grid, wild, mult)          # (n, nb symboles)
        else:
            g = self._lignes(nat_grid, wild, mult)
        if p["mode"] == "GLOBAL_SUM":
            spin_mult = mult.sum(axis=(1, 2))
            spin_mult[spin_mult == 0] = 1.0
            g *= spin_mult[:, None]
        return g.sum(axis=1), trophees, speciale.any(axis=(1, 2)), g.sum(axis=0)

    def _ways(self, nat_grid, wild, mult):
        """Gains en ways, gauche → droite. Renvoie (n, nb symboles)."""
        p = self.p
        n = nat_grid.shape[0]
        w = wild.sum(axis=1).astype(float)                 # wilds par rouleau
        S = (mult * wild).sum(axis=1)                      # somme des multis par rouleau
        out = np.zeros((n, len(p["codes"])))
        for s in self.pay_idx:
            nat = (nat_grid == s).sum(axis=1).astype(float)
            c = nat + w
            for j, k in enumerate((3, 4, 5)):
                pay = p["pays"][s, j]
                if pay == 0:
                    continue
                if p["mode"] == "WILD_MULT":
                    # multi d'une way = produit des multis de ses wilds
                    tot = np.prod(nat[:, :k] + S[:, :k], axis=1)
                    seul_wild = np.prod(S[:, :k], axis=1)
                else:
                    # multi d'une way = somme des multis de ses wilds (1 si aucun wild)
                    tot = np.prod(nat[:, :k], axis=1)
                    seul_wild = np.zeros(n)
                    for r in range(k):
                        autres = [i for i in range(k) if i != r]
                        tot += S[:, r] * np.prod(c[:, autres], axis=1)
                        seul_wild += S[:, r] * np.prod(w[:, autres], axis=1)
                ways = tot if s == self.top else tot - seul_wild
                if k < self.reels:
                    ways = ways * (c[:, k] == 0)           # longueur exacte k
                out[:, s] += pay * ways
        return out

    def _lignes(self, nat_grid, wild, mult):
        """Gains en lignes, gauche → droite, meilleur gain par ligne. Renvoie (n, nb symboles)."""
        p = self.p
        n = nat_grid.shape[0]
        L = p["lignes"]                                    # (nb lignes, 5), indices de rangée
        cols = np.arange(self.reels)
        nat = nat_grid[:, L, cols]                         # (n, nb lignes, 5)
        wl = wild[:, L, cols]
        ml = np.where(wl, mult[:, L, cols], 0.0)
        best = np.zeros(nat.shape[:2])
        best_s = np.full(nat.shape[:2], -1)
        for s in self.pay_idx:
            run = np.cumprod((nat == s) | wl, axis=2).astype(bool)   # cases de la ligne gagnante
            longueur = run.sum(axis=2)
            if s != self.top:                              # il faut au moins 1 symbole naturel
                longueur = np.where(((nat == s) & run).any(axis=2), longueur, 0)
            pay = np.zeros(longueur.shape)
            for j, k in enumerate((3, 4, 5)):
                pay[longueur == k] = p["pays"][s, j]
            if p["mode"] == "WILD_MULT":
                m = np.prod(np.where(run & wl, ml, 1.0), axis=2)
            else:
                somme = np.where(run, ml, 0.0).sum(axis=2)
                m = np.where(somme > 0, somme, 1.0)
            g = pay * m
            mieux = g > best
            best = np.where(mieux, g, best)
            best_s = np.where(mieux, s, best_s)
        out = np.zeros((n, len(p["codes"])))
        for s in self.pay_idx:
            out[:, s] = np.where(best_s == s, best, 0.0).sum(axis=1)
        return out

    def fs_initiaux(self, nb_trophees):
        table = self.p["table_fs"]
        out = np.zeros(len(nb_trophees), dtype=np.int64)
        for seuil, fs in table:                 # table triée : le dernier seuil couvre « et plus »
            out[nb_trophees >= seuil] = fs
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
            restant[actifs] += tr * self.p["fs_par_trophee"] - 1
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
