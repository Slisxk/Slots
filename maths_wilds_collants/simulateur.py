#!/usr/bin/env python3
"""
Modèle de maths « symboles géants + wilds multiplicateurs collants » (style Dog House).

Le jeu : NB_ROULEAUX x NB_LIGNES (5 x 4 = 1 024 ways par défaut), gains en ways de gauche à droite.
- Symboles géants : sur les bandes, chaque symbole payant forme un bloc de 1, 2 ou 3 cases de haut.
- Wild W (pas sur le rouleau 1) : porte un multi (x2, x3…). Dans une way, chaque wild compte pour sa
  valeur de multi au lieu de 1 : les multis de rouleaux différents se multiplient (comme Dog House).
- Scatter S : au plus 1 par rouleau ; 3, 4, 5 scatters déclenchent le bonus 1, 2, 3.
- Wilds des bonus : NON (normaux), FIXE (collants : ils restent à leur place jusqu'à la fin du bonus)
  ou MARCHE (collants et ils avancent d'un rouleau vers la gauche à chaque free spin, puis sortent).

Les bandes sont construites depuis le classeur (construire_bandes), exactement comme pour le SDK.
Le RTP des spins du jeu de base et la fréquence des bonus sont calculés EXACTEMENT en parcourant
toutes les positions des bandes ; les bonus (wilds collants) sont simulés.

    python simulateur.py classeur_maths.xlsx
    python simulateur.py classeur_maths.xlsx --spins 2000000 --buy 100000
    python simulateur.py classeur_maths.xlsx --exact      # calcul exact du jeu de base + bonus simulés (rapide)
"""
import argparse
import datetime as dt
import hashlib
import random
import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

MAX_FS_PAR_SESSION = 500
DIST_BORNES = [0, 1, 5, 20, 100, 1000]
MODES_WILDS = ("NON", "FIXE", "MARCHE")


# --------------------------------------------------------------------------- #
# Lecture des paramètres
# --------------------------------------------------------------------------- #
def _plage(wb, nom):
    if nom not in wb.defined_names:
        sys.exit(f"Plage nommée introuvable dans le classeur : {nom}")
    feuille, ref = next(iter(wb.defined_names[nom].destinations))
    cells = wb[feuille][ref.replace("$", "")]
    if not isinstance(cells, tuple):
        return [[cells.value]]
    if not isinstance(cells[0], tuple):
        cells = (cells,)
    return [[c.value for c in row] for row in cells]


def _val(wb, nom):
    return _plage(wb, nom)[0][0]


def _f(v):
    return float(v) if v not in (None, "") else 0.0


def load_params(path):
    wb = load_workbook(path)
    R = int(_val(wb, "NB_ROULEAUX"))
    sym = [r for r in _plage(wb, "SYMBOLES") if r[0] not in (None, "")]
    n = len(sym)

    def poids(nom):
        w = np.array([[_f(v) for v in r[2:2 + R]] for r in _plage(wb, nom)[:n]])
        if w.shape != (n, R):
            sys.exit(f"{nom} : il faut {R} colonnes de poids et {n} symboles (même ordre que la Paytable).")
        return w

    bonus = []
    for r in _plage(wb, "BONUS"):
        if r[0] in (None, "") or r[1] in (None, ""):
            continue
        bonus.append({"nom": str(r[0]), "bn": int(r[1]), "fs": int(r[2]), "wilds": str(r[3]).strip().upper(),
                      "prix": float(r[4]) if r[4] not in (None, "", 0) else None})
    phases = ["base"] + [f"fs{k + 1}" for k in range(len(bonus))]
    tailles = np.array([[_f(v) for v in r[2:5]] for r in _plage(wb, "TAILLES")[:n]])
    mv = [r for r in _plage(wb, "WILD_MULTIS") if r[0] not in (None, "")]
    p = {
        "R": R, "rows": int(_val(wb, "NB_LIGNES")),
        "codes": [str(r[0]) for r in sym], "noms": [str(r[1]) for r in sym],
        "types": [str(r[2]).strip().upper() for r in sym],
        "pays": np.array([[_f(v) for v in r[3:7]] for r in sym]),
        "poids": {ph: poids(f"POIDS_{ph.upper()}") for ph in phases},
        "tailles": tailles,
        "wild_val": np.array([float(r[0]) for r in mv]),
        "wild_w": {ph: np.array([_f(r[1 + i]) for r in mv]) for i, ph in enumerate(phases)},
        "bonus": bonus,
        "retrig_bn": int(_val(wb, "RETRIG_SCATTERS")), "retrig_fs": int(_val(wb, "RETRIG_FS")),
        "rtp_cible": float(_val(wb, "RTP_CIBLE")), "rtp_min": float(_val(wb, "RTP_MIN")),
        "rtp_max": float(_val(wb, "RTP_MAX")), "max_win": float(_val(wb, "MAX_WIN")),
        "part_spins": (float(_val(wb, "PART_SPINS_MIN")), float(_val(wb, "PART_SPINS_MAX"))),
        "part_bonus_max": float(_val(wb, "PART_BONUS_MAX")),
        "hit": (float(_val(wb, "HIT_MIN")), float(_val(wb, "HIT_MAX"))),
        "longueur": int(_val(wb, "LONGUEUR_BANDES")), "seed_bandes": int(_val(wb, "SEED_BANDES")),
        "sim_spins": int(_val(wb, "SIM_SPINS")), "sim_buy": int(_val(wb, "SIM_BUY")), "seed": int(_val(wb, "SIM_SEED")),
        "phases": phases,
    }
    validate(p)
    return p


def validate(p):
    t = p["types"]
    if t.count("SCATTER") != 1 or t.count("WILD") != 1 or "PAY" not in t:
        sys.exit("Paytable : il faut exactement 1 SCATTER, 1 WILD et au moins 1 symbole PAY.")
    if not 3 <= p["R"] <= 6 or not 2 <= p["rows"] <= 6:
        sys.exit("Config : 3 à 6 rouleaux, 2 à 6 lignes.")
    b = p["bonus"]
    if not 1 <= len(b) <= 3:
        sys.exit("Config : il faut entre 1 et 3 bonus.")
    s = [x["bn"] for x in b]
    if s != sorted(set(s)) or s[-1] > p["R"]:
        sys.exit(f"Bonus : nombres de scatters croissants, au plus {p['R']} (1 scatter max par rouleau).")
    for x in b:
        if x["wilds"] not in MODES_WILDS:
            sys.exit(f"Bonus « {x['nom']} » : mode des wilds = {' / '.join(MODES_WILDS)}.")
    wi = t.index("WILD")
    if p["poids"]["base"][wi, 0] > 0:
        sys.exit("Le wild ne doit pas tomber sur le rouleau 1 (une way commence par un symbole naturel).")
    pays = p["pays"][[i for i, x in enumerate(t) if x == "PAY"]]
    if (np.abs(pays * 10 - np.round(pays * 10)) > 1e-9).any():
        sys.exit("Paytable : chaque gain doit être un multiple de 0,1 (le SDK n'accepte que des gains par pas de 0,1x la mise).")
    if (np.abs(p["wild_val"] - np.round(p["wild_val"])) > 1e-9).any() or (p["wild_val"] < 1).any():
        sys.exit("Multis des wilds : valeurs entières, au moins 1.")
    for ph in p["phases"]:
        if p["wild_w"][ph].sum() <= 0:
            sys.exit(f"Multis des wilds ({ph}) : les poids doivent avoir une somme > 0.")
    ta = p["tailles"]
    for i, x in enumerate(t):
        if x == "PAY" and ta[i].sum() <= 0:
            sys.exit(f"Tailles : le symbole {p['codes'][i]} n'a aucune taille possible.")


# --------------------------------------------------------------------------- #
# Bandes avec symboles géants (partagées avec stake/exporter.py)
# --------------------------------------------------------------------------- #
def construire_bande(p, ph, reel):
    """Une bande de LONGUEUR_BANDES cases. Les poids = part des CASES de chaque symbole. Les symboles payants
    forment des blocs de 1 à 3 cases (onglet Tailles), le wild et le scatter 1 case. Deux blocs du même
    symbole ne se touchent jamais (un bloc = un symbole géant). Scatters espacés d'au moins NB_LIGNES cases."""
    t, rows, L = p["types"], p["rows"], p["longueur"]
    rng = random.Random(f"{p['seed_bandes']}-{ph}-{reel}")
    w = p["poids"][ph][:, reel].astype(float)
    haut = []
    for i, x in enumerate(t):
        if x == "PAY":
            ta = p["tailles"][i] / p["tailles"][i].sum()
            haut.append(ta)
        else:
            haut.append(np.array([1.0, 0.0, 0.0]))
    moy_h = np.array([(h * np.array([1, 2, 3])).sum() for h in haut])
    q = np.where(w > 0, w / moy_h, 0.0)                     # probabilité de tirer un bloc de chaque symbole
    q = q / q.sum()
    cum = np.cumsum(q)
    sc = t.index("SCATTER")
    out, last, dernier_sc = [], -1, -10 ** 9
    while len(out) < L:
        s = int(np.searchsorted(cum, rng.random(), side="right"))
        s = min(s, len(q) - 1)
        if s == last or (s == sc and len(out) - dernier_sc < rows):
            continue
        h = 1 + int(np.searchsorted(np.cumsum(haut[s]), rng.random(), side="right"))
        h = min(h, 3)
        if s == sc:
            dernier_sc = len(out)
        out += [s] * h
        last = s
    out = out[:L]                                           # longueur exacte (le SDK veut des rouleaux égaux)
    # Bande circulaire : réparer la jonction fin / début (deux blocs du même symbole qui se toucheraient,
    # ou deux scatters à moins de NB_LIGNES cases) en remplaçant des cases de la fin par un symbole payant.
    pay = [i for i, x in enumerate(t) if x == "PAY"]

    def remplacer(i):
        voisins = {out[i - 1], out[(i + 1) % L]}
        out[i] = next(x for x in pay if x not in voisins)

    for i in range(L - rows + 1, L):                        # scatter trop près d'un scatter du début
        if out[i] == sc and sc in out[:rows - (L - i)]:
            remplacer(i)
    if out[-1] == out[0]:
        remplacer(L - 1)
    return np.array(out, dtype=np.int16)


def construire_bandes(p, ph):
    return [construire_bande(p, ph, r) for r in range(p["R"])]


def fenetres(bande, rows):
    """Toutes les fenêtres visibles d'une bande : (L, rows)."""
    L = len(bande)
    return bande[(np.arange(L)[:, None] + np.arange(rows)) % L]


# --------------------------------------------------------------------------- #
# Calcul exact du jeu de base (toutes les positions des bandes)
# --------------------------------------------------------------------------- #
def multi_moyen(p, ph):
    w = p["wild_w"][ph]
    return float((p["wild_val"] * w).sum() / w.sum())


def stats_bandes(p, ph, bandes=None):
    """Par symbole payant et rouleau : E[cases qui comptent], avec un wild compté pour son multi moyen,
    et P(aucune). Plus la probabilité qu'un rouleau montre un scatter."""
    bandes = bandes or construire_bandes(p, ph)
    t = p["types"]
    sc, wi = t.index("SCATTER"), t.index("WILD")
    em = multi_moyen(p, ph)
    n = len(t)
    ec, p0 = np.zeros((n, p["R"])), np.ones((n, p["R"]))
    q_sc = np.zeros(p["R"])
    for r, b in enumerate(bandes):
        f = fenetres(b, p["rows"])
        nw = (f == wi).sum(axis=1)
        q_sc[r] = (f == sc).any(axis=1).mean()
        for s, x in enumerate(t):
            if x != "PAY":
                continue
            ns = (f == s).sum(axis=1)
            if r == 0:
                ec[s, r] = (ns + nw * em)[ns > 0].sum() / len(f)    # une way commence par un symbole naturel
            else:
                ec[s, r] = (ns + nw * em).mean()
            p0[s, r] = ((ns + nw) == 0).mean()
    return ec, p0, q_sc


def loi_scatters(q):
    d = np.array([1.0])
    for x in q:
        d = np.convolve(d, [1 - x, x])
    return d


def exact_base(p, bandes=None):
    ec, p0, q = stats_bandes(p, "base", bandes)
    R = p["R"]
    ev, par = 0.0, np.zeros(len(p["types"]))
    for s, x in enumerate(p["types"]):
        if x != "PAY":
            continue
        for k in range(3, R + 1):
            g = p["pays"][s, k - 3]
            if g > 0:
                e = g * np.prod(ec[s, :k]) * (p0[s, k] if k < R else 1.0)
                par[s] += e
                ev += e
    loi = loi_scatters(q)
    seuils = [b["bn"] for b in p["bonus"]] + [len(loi)]
    freq = [float(loi[seuils[k]:seuils[k + 1]].sum()) for k in range(len(p["bonus"]))]
    return {"spins": ev, "sym": par, "loi": loi, "freq": freq, "q_sc": q}


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #
class Moteur:
    def __init__(self, p, rng):
        self.p, self.rng = p, rng
        self.R, self.rows = p["R"], p["rows"]
        t = p["types"]
        self.sc, self.wi = t.index("SCATTER"), t.index("WILD")
        self.pay = [i for i, x in enumerate(t) if x == "PAY"]
        self.bandes = {ph: construire_bandes(p, ph) for ph in p["phases"]}
        self.fen = {ph: [fenetres(b, self.rows) for b in bs] for ph, bs in self.bandes.items()}
        # positions d'arrêt avec / sans scatter visible, pour forcer un nombre de scatters
        self.avec, self.sans, self.q = {}, {}, {}
        for ph, fs in self.fen.items():
            a = [np.flatnonzero((f == self.sc).any(axis=1)) for f in fs]
            self.avec[ph] = a
            self.sans[ph] = [np.flatnonzero(~(f == self.sc).any(axis=1)) for f in fs]
            self.q[ph] = np.array([len(x) / len(f) for x, f in zip(a, fs)])
        self.wcum = {ph: np.cumsum(w / w.sum()) for ph, w in p["wild_w"].items()}

    def tirage(self, n, ph, force_bn=None):
        g = np.empty((n, self.rows, self.R), dtype=np.int16)
        if force_bn is None:
            for r in range(self.R):
                f = self.fen[ph][r]
                g[:, :, r] = f[self.rng.integers(0, len(f), n)]
            return g
        cle = np.log(self.rng.random((n, self.R))) / np.maximum(self.q[ph], 1e-300)
        a = np.argsort(np.argsort(-cle, axis=1), axis=1) < force_bn
        for r in range(self.R):
            f = self.fen[ph][r]
            av, sa = self.avec[ph][r], self.sans[ph][r]
            pos = np.where(a[:, r], av[self.rng.integers(0, max(len(av), 1), n) % max(len(av), 1)],
                           sa[self.rng.integers(0, len(sa), n)])
            g[:, :, r] = f[pos]
        return g

    def multis(self, g, ph):
        """Multi de chaque wild de la grille (0 ailleurs)."""
        m = np.zeros(g.shape)
        w = g == self.wi
        k = int(w.sum())
        if k:
            idx = np.searchsorted(self.wcum[ph], self.rng.random(k), side="right")
            m[w] = self.p["wild_val"][np.minimum(idx, len(self.p["wild_val"]) - 1)]
        return m

    def gains(self, g, m):
        """Ways : chaque wild compte pour son multi. g (n, rows, R), m multis des wilds (0 ailleurs)."""
        p = self.p
        n = g.shape[0]
        wsum = m.sum(axis=1)                                   # somme des multis des wilds, par rouleau
        out = np.zeros(n)
        par = np.zeros(len(p["codes"]))
        for s in self.pay:
            nat = (g == s).sum(axis=1)
            c = nat + wsum
            ways = np.where(nat[:, 0] > 0, c[:, 0], 0.0)
            for k in range(2, self.R + 1):
                ways = ways * c[:, k - 1]
                if k < 3:
                    continue
                gk = p["pays"][s, k - 3]
                if gk <= 0:
                    continue
                v = gk * (ways * (c[:, k] == 0) if k < self.R else ways)
                out += v
                par[s] += v.sum()
        return np.round(out, 2), par

    def spin(self, n, ph, force_bn=None):
        g = self.tirage(n, ph, force_bn)
        m = self.multis(g, ph)
        gain, par = self.gains(g, m)
        return gain, (g == self.sc).sum(axis=(1, 2)), par

    def sessions(self, k, n, cap):
        """n sessions du bonus k (wilds NON / FIXE / MARCHE). Renvoie (gains plafonnés, FS joués)."""
        b = self.p["bonus"][k - 1]
        ph, mode = f"fs{k}", b["wilds"]
        tot = np.zeros(n)
        reste = np.full(n, b["fs"], dtype=np.int64)
        joues = np.zeros(n, dtype=np.int64)
        coll = np.zeros((n, self.rows, self.R))                # multis des wilds collants (0 = aucun)
        act = np.arange(n)
        while act.size:
            c = coll[act]
            if mode == "MARCHE":                               # les wilds collants avancent d'un rouleau vers la gauche
                c = np.concatenate([c[:, :, 1:], np.zeros((len(act), self.rows, 1))], axis=2)
            g = self.tirage(act.size, ph)
            m = self.multis(g, ph)
            sous = c > 0
            g = np.where(sous, self.wi, g)                     # les wilds collants recouvrent la grille
            m = np.where(sous, c, m)
            if mode != "NON":
                c = np.where(sous, c, m)                       # les nouveaux wilds deviennent collants
                coll[act] = c
            gain, _ = self.gains(g, m)
            tot[act] += gain
            joues[act] += 1
            bn = (g == self.sc).sum(axis=(1, 2))
            reste[act] += np.where(bn >= self.p["retrig_bn"], self.p["retrig_fs"], 0) - 1
            fini = (reste[act] <= 0) | (tot[act] >= cap) | (joues[act] >= MAX_FS_PAR_SESSION)
            act = act[~fini]
        return np.minimum(tot, cap), joues

    def type_bonus(self, nb):
        out = np.zeros(len(nb), dtype=np.int64)
        for k, b in enumerate(self.p["bonus"], 1):
            out[nb >= b["bn"]] = k
        return out


def _stats(r, w, cout, cap):
    moy = float((w * r).sum())
    srt = np.argsort(r)
    cw = np.cumsum(w[srt])
    med = float(r[srt][np.searchsorted(cw, 0.5 * cw[-1])])
    seuil = r[srt][min(np.searchsorted(cw, 0.999 * cw[-1]), len(r) - 1)]
    queue = r >= seuil
    cvar = float((w * r)[queue].sum() / w[queue].sum())
    etl40, etl10k = float((w * r)[r >= 40 * cout].sum()), float((w * r)[r >= 10_000].sum())
    return {"moy": moy, "hit": float(w[r > 0].sum()), "ecart_type": float(np.sqrt(max((w * r * r).sum() - moy ** 2, 0))),
            "mediane": med, "etl40b": etl40 / cout, "etl10k": etl10k / cout, "etl_abs": etl40 + etl10k,
            "p_max": float(w[r >= cap].sum()), "p5k": float(w[r >= 5_000].sum()), "max": float(r.max()),
            "cvar": cvar / cout, "cvar_abs": cvar}


def _distribution(r, w, cap):
    bornes = DIST_BORNES + [cap]
    d = [("0 x", float(w[r == 0].sum()))]
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        sel = (r > lo) & (r < hi) if lo == 0 else (r >= lo) & (r < hi)
        d.append((f"{lo:g} – {hi:g} x" if hi < cap else f"{lo:g} x – max win", float(w[sel].sum())))
    d.append(("Max win", float(w[r >= cap].sum())))
    return d


def simuler_base(m, spins, lot=50_000, verbose=True):
    """Jeu de base par strates du nombre de scatters (loi exacte), strates qui déclenchent sur-échantillonnées."""
    p = m.p
    cap = p["max_win"]
    loi = loi_scatters(m.q["base"])
    seuil = p["bonus"][0]["bn"]
    n_min = max(spins // 50, 2000)
    nb = len(p["bonus"])
    R, W = [], []
    comp = np.zeros(nb + 1)
    par_type = np.zeros((nb + 1, 3))
    var = 0.0
    for j, pj in enumerate(loi):
        if pj <= 0:
            continue
        nj = max(int(round(spins * pj)), n_min if j >= seuil else 1)
        wj = pj / nj
        rj, fait = [], 0
        while fait < nj:
            n = min(lot, nj - fait)
            g, bn, _ = m.spin(n, "base", force_bn=j)
            typ = m.type_bonus(bn)
            bon, jo = np.zeros(n), np.zeros(n)
            for k in range(1, nb + 1):
                sel = typ == k
                if sel.any():
                    t, js = m.sessions(k, int(sel.sum()), cap)
                    bon[sel], jo[sel] = t, js
            r = np.minimum(g + bon, cap)
            beff = r - np.minimum(g, cap)
            comp[0] += wj * np.minimum(g, cap).sum()
            for k in range(1, nb + 1):
                sel = typ == k
                comp[k] += wj * beff[sel].sum()
                par_type[k] += wj * np.array([sel.sum(), beff[sel].sum(), jo[sel].sum()])
            rj.append(r)
            fait += n
            if verbose:
                print(f"\r  base : strate {j} scatter(s), {fait:,}/{nj:,}   ", end="", file=sys.stderr)
        rj = np.concatenate(rj)
        var += pj * pj * rj.var() / len(rj)
        R.append(rj)
        W.append(np.full(len(rj), wj))
    if verbose:
        print(file=sys.stderr)
    r, w = np.concatenate(R), np.concatenate(W)
    s = _stats(r, w, 1.0, cap)
    res = {"spins": len(r), "rtp": s["moy"], "marge": 1.96 * np.sqrt(var), "rtp_spins": comp[0],
           "dist": _distribution(r, w, cap), **s}
    for k in range(1, nb + 1):
        f = par_type[k, 0]
        res[f"rtp_bonus{k}"] = comp[k]
        res[f"freq{k}"] = f
        res[f"gain{k}"] = par_type[k, 1] / f if f else float("nan")
        res[f"fsm{k}"] = par_type[k, 2] / f if f else float("nan")
    return res


def simuler_achat(m, k, n, lot=10_000, verbose=True):
    p = m.p
    cap = p["max_win"]
    b = p["bonus"][k - 1]
    parts, fs, seuls = [], [], []
    for i in range(0, n, lot):
        nn = min(lot, n - i)
        g = m.spin(nn, "base", force_bn=b["bn"])[0]
        t, js = m.sessions(k, nn, cap)
        parts.append(np.minimum(g + t, cap))
        seuls.append(t)
        fs.append(js)
        if verbose:
            print(f"\r  bonus {k} : {i + nn:,}/{n:,}", end="", file=sys.stderr)
    if verbose:
        print(file=sys.stderr)
    r = np.concatenate(parts)
    w = np.full(len(r), 1 / len(r))
    prix = b["prix"] or 1.0
    s = _stats(r, w, prix, cap)
    return {"sessions": len(r), "prix": b["prix"], "gain": s["moy"], "rtp": s["moy"] / prix if b["prix"] else None,
            "marge": 1.96 * float(r.std() / np.sqrt(len(r))) / prix if b["prix"] else None,
            "prix_conseille": s["moy"] / p["rtp_cible"], "fs_moyens": float(np.concatenate(fs).mean()),
            "gain_bonus": float(np.concatenate(seuls).mean()),
            "dist": _distribution(r, w, cap), **s}


def estimation(p, ex, achats):
    """RTP « exact + bonus simulés » : spins exacts, fréquence exacte des bonus, gain moyen simulé de chaque bonus
    (sans le spin de déclenchement, déjà compté dans les spins)."""
    tot = ex["spins"]
    parts = {}
    for k in range(1, len(p["bonus"]) + 1):
        a = achats.get(k)
        if not a:
            continue
        gain = a["gain_bonus"]                                 # free spins seuls (le spin de déclenchement est dans les spins)
        parts[k] = (ex["freq"][k - 1], gain, ex["freq"][k - 1] * gain)
        tot += ex["freq"][k - 1] * gain
    return tot, parts


def simuler(p, spins=None, buy=None, verbose=True):
    m = Moteur(p, np.random.default_rng(p["seed"]))
    ex = exact_base(p, m.bandes["base"])
    res = {"date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "exact": ex}
    buy = p["sim_buy"] if buy is None else buy
    res["achats"] = {k: simuler_achat(m, k, buy, verbose=verbose) for k in range(1, len(p["bonus"]) + 1)}
    res["estimation"] = estimation(p, ex, res["achats"])
    if spins != 0:
        res["base"] = simuler_base(m, spins or p["sim_spins"], verbose=verbose)
    return res


# --------------------------------------------------------------------------- #
# Contrôles (doc d'approbation et math SDK de Stake Engine + équilibre)
# --------------------------------------------------------------------------- #
SOUMISSION = {"rtp_min": 0.960, "rtp_max": 0.967, "ecart_type_base_min": 0.6}
RISQUE = {"ecart_type": 60, "cvar": 700, "cvar_abs": 50_000, "etl40b": 0.9, "etl10k": 0.8, "etl_somme": 1.5,
          "etl_abs": 10_000, "p5k": 0.05}
MAX_WIN_RARETE = 10_000_000
HIT_MIN_ABSOLU = 1 / 20


def controles_risque(s, cout):
    ech = []
    for cle, val in (("ecart_type", s["ecart_type"] / cout), ("cvar", s["cvar"]), ("cvar_abs", s["cvar_abs"]),
                     ("etl40b", s["etl40b"]), ("etl10k", s["etl10k"]), ("etl_somme", s["etl40b"] + s["etl10k"]),
                     ("etl_abs", s["etl_abs"]), ("p5k", s["p5k"])):
        if val > RISQUE[cle]:
            ech.append(f"{cle} {val:.3g} > {RISQUE[cle]:g}")
    return ech


def controles(p, r):
    est, parts = r["estimation"]
    b = r.get("base")
    L = []

    def add(nom, val, regle, ok):
        L.append((nom, val, regle, "OK" if ok else "ÉCHEC"))

    lo, hi = p["rtp_min"], p["rtp_max"]
    add("RTP estimé (spins exacts + bonus simulés)", f"{est:.3%}", f"entre {lo:.2%} et {hi:.2%} (ta règle ; SDK : 96,0 à 96,7 %)",
        lo <= est <= hi)
    if b:
        add("RTP simulé (plafond compris)", f"{b['rtp']:.3%} ± {b['marge']:.3%}", "écart à l'estimation < 3 marges",
            abs(b["rtp"] - est) <= 3 * b["marge"] + 0.002)
    part = r["exact"]["spins"] / est
    a0, a1 = p["part_spins"]
    add("Part des spins (hors bonus)", f"{part:.1%}", f"{a0:.0%} à {a1:.0%} : les spins rapportent sans tout donner", a0 <= part <= a1)
    for k, (f, g, rt) in parts.items():
        add(f"Part du bonus {k}", f"{rt / est:.1%}", f"au plus {p['part_bonus_max']:.0%} : aucun bonus ne donne tout",
            rt / est <= p["part_bonus_max"])
        add(f"Bonus {k} : fréquence", f"1 sur {1 / f:,.0f}", "entre 1/100 et 1/1 000 000", 1e-6 <= f <= 0.01)
    if b:
        h0, h1 = p["hit"]
        add("Fréquence de gain", f"{b['hit']:.1%} (1 sur {1 / b['hit']:.1f})",
            f"1 sur {1 / h1:.0f} à 1 sur {1 / h0:.0f} (checklist) ; jamais moins de 1 sur 20 (doc)",
            h0 <= b["hit"] <= h1 and b["hit"] >= HIT_MIN_ABSOLU)
        pm = b["p_max"]
        add("Max win atteignable", f"1 sur {1 / pm:,.0f}" if pm else "jamais observé",
            "plus fréquent que 1 sur 10 000 000 (doc « Math Requirements »)", pm >= 1 / MAX_WIN_RARETE)
        add("Écart-type du jeu de base", f"{b['ecart_type']:.1f}x", "au moins 0,6 (soumission SDK)",
            b["ecart_type"] >= SOUMISSION["ecart_type_base_min"])
        ech = controles_risque(b, 1.0)
        add("Contrôles de risque Studio (base)", "tous OK" if not ech else ", ".join(ech),
            "RISK_CHECKS du SDK : chaque échec baisse la mise max autorisée", not ech)
    for k, a in r["achats"].items():
        if not a["prix"]:
            continue
        add(f"Achat bonus {k} : RTP simulé", f"{a['rtp']:.2%} ± {a['marge']:.2%}",
            "à 0,5 % du jeu de base (doc) ; la pondération du SDK le règle exactement",
            abs(a["rtp"] - est) <= 0.005 + a["marge"])
        add(f"Achat bonus {k} : prix", f"{a['prix']:g}x", "500x au plus pour garder la mise maximale de 1 000 $ (math SDK)",
            a["prix"] <= 500)
        ech = controles_risque(a, a["prix"])
        L.append((f"Achat bonus {k} : contrôles de risque Studio", "tous OK" if not ech else ", ".join(ech),
                  "RISK_CHECKS du SDK ; sinon la pondération rend les plus gros gains de ce mode plus rares",
                  "OK" if not ech else "CORRIGÉ PAR LA PONDÉRATION"))
    return L


# --------------------------------------------------------------------------- #
# Écriture : onglet Simulation + rapport
# --------------------------------------------------------------------------- #
LIGNES_SIM = ["date", "estimation", "spins_exact", "spins", "rtp", "marge", "rtp_spins", "hit", "ecart_type", "mediane",
              "max", "p_max", "etl40b", "etl10k", "cvar"] + [f"{x}{k}" for k in (1, 2, 3) for x in ("freq", "gain", "fsm", "rtp_bonus")]
LIBELLES_SIM = {
    "date": "Date de la simulation", "estimation": "RTP estimé (spins exacts + bonus simulés)",
    "spins_exact": "RTP des spins, calcul exact (toutes les positions des bandes)", "spins": "Spins simulés",
    "rtp": "RTP simulé (plafond compris)", "marge": "Marge d'erreur (± à 95 %)", "rtp_spins": "RTP des spins simulé",
    "hit": "Fréquence de gain", "ecart_type": "Écart-type par tour (x mise)", "mediane": "Gain médian",
    "max": "Max observé (x mise)", "p_max": "Probabilité du max win",
    "etl40b": "Risque : part du RTP ≥ 40x le coût (≤ 0,9)", "etl10k": "Risque : part du RTP ≥ 10 000x (≤ 0,8)",
    "cvar": "Risque : cvar, 0,1 % des meilleurs tours / coût (≤ 700)",
    **{f"freq{k}": f"Bonus {k} : probabilité par spin (exacte)" for k in (1, 2, 3)},
    **{f"gain{k}": f"Bonus {k} : gain moyen (x mise)" for k in (1, 2, 3)},
    **{f"fsm{k}": f"Bonus {k} : FS joués en moyenne" for k in (1, 2, 3)},
    **{f"rtp_bonus{k}": f"Bonus {k} : RTP apporté" for k in (1, 2, 3)},
}
LIGNES_ACHAT = ["sessions", "prix", "gain", "rtp", "marge", "prix_conseille", "fs_moyens", "mediane", "max", "p_max",
                "etl40b", "etl10k", "cvar"]
LIBELLES_ACHAT = {"sessions": "Tours simulés", "prix": "Prix (x mise)", "gain": "Gain moyen (x mise)",
                  "rtp": "RTP au prix actuel", "marge": "Marge d'erreur (± à 95 %)",
                  "prix_conseille": "Prix conseillé (gain moyen / RTP cible)", "fs_moyens": "FS joués en moyenne",
                  "mediane": "Gain médian", "max": "Max observé", "p_max": "Probabilité du max win",
                  "etl40b": "Risque : part du RTP ≥ 40x le prix (≤ 0,9)", "etl10k": "Risque : part du RTP ≥ 10 000x (≤ 0,8)",
                  "cvar": "Risque : cvar / prix (≤ 700)"}
SIM_L0 = 5
SIM_A0 = SIM_L0 + len(LIGNES_SIM) + 2
SIM_C0 = SIM_A0 + len(LIGNES_ACHAT) + 3
SIM_LIGNE = {k: SIM_L0 + i for i, k in enumerate(LIGNES_SIM)}
SIM_LIGNE.update({f"a_{k}": SIM_A0 + 1 + i for i, k in enumerate(LIGNES_ACHAT)})


def cellule(cle, col="B"):
    return f"{col}{SIM_LIGNE[cle]}"


def _valeurs_base(r):
    b = dict(r.get("base") or {})
    b["estimation"] = r["estimation"][0]
    b["spins_exact"] = r["exact"]["spins"]
    for k, (f, g, rt) in r["estimation"][1].items():
        b[f"freq{k}"] = f
        b.setdefault(f"gain{k}", g)
        b[f"rtp_bonus{k}"] = rt
        b.setdefault(f"fsm{k}", r["achats"][k]["fs_moyens"])
    return b


def ecrire(path, p, r, ctrl):
    wb = load_workbook(path)
    ws = wb["Simulation"]

    def put(ref, v):
        ws[ref].value = None if v is None or (isinstance(v, float) and v != v) else (float(v) if isinstance(v, np.floating) else v)

    b = _valeurs_base(r)
    for k in LIGNES_SIM:
        put(cellule(k), r["date"] if k == "date" else b.get(k))
    for k in LIGNES_ACHAT:
        for kk, col in ((1, "B"), (2, "C"), (3, "D")):
            a = r["achats"].get(kk)
            put(f"{col}{SIM_LIGNE['a_' + k]}", a.get(k) if a else None)
    for i in range(30):
        for col in "ABCD":
            put(f"{col}{SIM_C0 + 1 + i}", None)
    for i, row in enumerate(ctrl):
        for col, v in zip("ABCD", row):
            put(f"{col}{SIM_C0 + 1 + i}", v)
    for i in range(12):
        for col in "FG":
            put(f"{col}{5 + i}", None)
    if r.get("base"):
        for i, (lbl, v) in enumerate(r["base"]["dist"]):
            put(f"F{5 + i}", lbl)
            put(f"G{5 + i}", v)
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)


def rapport(path_xlsx, p, r, ctrl, sortie):
    est, parts = r["estimation"]
    ex, b = r["exact"], r.get("base") or {}
    L = ["# Rapport de validation des maths", "",
         "Contrôles repris de la doc et du math SDK officiels de Stake Engine (github.com/engineio).", "",
         "## 1. Périmètre", f"- Classeur : `{Path(path_xlsx).name}` (empreinte {hashlib.sha256(Path(path_xlsx).read_bytes()).hexdigest()[:12]})",
         f"- Date : {r['date']}", f"- Grille : {p['R']} rouleaux x {p['rows']} lignes ({p['rows'] ** p['R']:,} ways), symboles géants de 1 à 3 cases",
         "", "## 2. Décomposition du RTP", "", "| Composante | Fréquence | Gain moyen | RTP |", "|---|---|---|---|",
         f"| Spins du jeu de base (calcul exact sur toutes les positions des bandes) | chaque spin | {ex['spins']:.4f} x | {ex['spins']:.3%} |"]
    for k, (f, g, rt) in parts.items():
        bb = p["bonus"][k - 1]
        L.append(f"| Bonus {k} « {bb['nom']} » (wilds {bb['wilds']}) | 1 sur {1 / f:,.0f} (exact) | {g:.1f} x (simulé) | {rt:.3%} |")
    L += [f"| **Total estimé** | | | **{est:.3%}** |", ""]
    if b:
        L += ["## 3. Simulation complète", f"- {b['spins']:,} spins de base (strates du nombre de scatters), graine {p['seed']}",
              f"- RTP simulé {b['rtp']:.3%} ± {b['marge']:.3%} ; fréquence de gain {b['hit']:.2%} ; écart-type {b['ecart_type']:.1f}x",
              f"- Max win : " + (f"1 tour sur {1 / b['p_max']:,.0f}" if b["p_max"] else "non observé"), ""]
    L += ["## 4. Contrôles", "", "| Contrôle | Valeur | Règle | Statut |", "|---|---|---|---|"]
    L += [f"| {a} | {v} | {rg} | {s} |" for a, v, rg, s in ctrl]
    ech = [a for a, _, _, s in ctrl if s in ("ÉCHEC",)]
    L += ["", "## 5. Décision", f"- Statut : **{'VALIDÉ' if not ech else 'À REVOIR'}**" + ("" if not ech else " (" + ", ".join(ech) + ")"),
          "- La validation finale se fait sur les fichiers générés par le SDK (RTP pondéré des books).", ""]
    Path(sortie).write_text("\n".join(L), encoding="utf-8")


def afficher(p, r):
    est, parts = r["estimation"]
    ex = r["exact"]
    print(f"RTP ESTIMÉ {est:.3%} (cible {p['rtp_cible']:.2%}) — spins exacts {ex['spins']:.3%} ({ex['spins'] / est:.0%})")
    for k, (f, g, rt) in parts.items():
        a = r["achats"][k]
        print(f"  bonus {k} {p['bonus'][k - 1]['nom']:<18} 1/{1 / f:>8,.0f}  gain {g:7.1f}x  FS {a['fs_moyens']:.1f}  "
              f"RTP {rt:.3%} ({rt / est:.0%})  achat {a['gain']:.1f}x (± {1.96 * a['ecart_type'] / np.sqrt(a['sessions']):.1f}) "
              f"-> prix conseillé {a['prix_conseille']:.0f}x, médiane {a['mediane']:.1f}x")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--spins", type=int)
    ap.add_argument("--buy", type=int)
    ap.add_argument("--exact", action="store_true", help="spins exacts + bonus simulés (20 000 tours par bonus)")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    p = load_params(a.classeur)
    if a.exact:
        r = simuler(p, spins=0, buy=a.buy or 20_000, verbose=False)
        afficher(p, r)
        return
    r = simuler(p, a.spins, a.buy)
    afficher(p, r)
    ctrl = controles(p, r)
    print()
    for nom, val, regle, etat in ctrl:
        print(f"  [{etat:^6}] {nom:<36} {val:<28} {regle}")
    if not a.no_write:
        ecrire(a.classeur, p, r, ctrl)
        rapport(a.classeur, p, r, ctrl, Path(a.classeur).with_name("rapport_validation.md"))
        print(f"\nRésultats écrits dans {a.classeur} (onglet Simulation) et rapport_validation.md")


if __name__ == "__main__":
    main()
