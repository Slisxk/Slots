#!/usr/bin/env python3
"""
Modèle de maths « ways + multis de colonne » : calcul exact (formules) et simulation Monte Carlo.

Le jeu : NB_ROULEAUX x NB_LIGNES (5 x 4 = 1 024 ways par défaut), gains en ways de gauche à droite,
wild, scatter (au plus 1 par rouleau). Un « multi de colonne » peut tomber sur un rouleau entier
(valeurs de x2 à x500) : le gain d'une way est multiplié par la SOMME des multis des colonnes qu'elle
traverse (x1 s'il n'y en a aucun). Bonus « non collants » : les multis disparaissent après chaque
spin. Bonus « collants » : un multi reste sur sa colonne jusqu'à la fin du bonus, et chaque
nouveau multi sur cette colonne s'ajoute à sa valeur.

Il lit tous les paramètres dans le classeur (plages nommées), calcule le RTP exact de chaque
composante, simule des millions de tours (distribution, volatilité, max win, limites « 3 étoiles »)
et réécrit l'onglet « Simulation » et le rapport de validation (rapport_validation.md).

    python simulateur.py classeur_maths.xlsx
    python simulateur.py classeur_maths.xlsx --spins 2000000 --buy 100000
    python simulateur.py classeur_maths.xlsx --exact       # calcul exact seulement (instantané)
"""
import argparse
import datetime as dt
import hashlib
import sys
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

MAX_FS_PAR_SESSION = 500          # garde-fou contre une boucle de retrigger
DIST_BORNES = [0, 1, 5, 20, 100, 1000]
T_MAX = 120                       # spins max pris en compte par le calcul exact d'un bonus collant


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


def _oui(v):
    return str(v).strip().upper() in ("OUI", "YES", "TRUE", "1")


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
        bonus.append({"nom": str(r[0]), "bn": int(r[1]), "fs": int(r[2]), "collant": _oui(r[3]),
                      "prix": float(r[4]) if r[4] not in (None, "", 0) else None})
    phases = ["base"] + [f"fs{k + 1}" for k in range(len(bonus))]
    vals = [r for r in _plage(wb, "MULTI_VALEURS") if r[0] not in (None, "")]
    act = _plage(wb, "MULTI_ACTIVATION")
    p = {
        "R": R,
        "rows": int(_val(wb, "NB_LIGNES")),
        "codes": [str(r[0]) for r in sym],
        "noms": [str(r[1]) for r in sym],
        "types": [str(r[2]).strip().upper() for r in sym],
        "pays": np.array([[_f(v) for v in r[3:7]] for r in sym]),      # 3, 4, 5, 6 identiques
        "poids": {ph: poids(f"POIDS_{ph.upper()}") for ph in phases},
        "multi_val": np.array([float(r[0]) for r in vals]),
        "multi_w": {ph: np.array([_f(r[1 + i]) for r in vals]) for i, ph in enumerate(phases)},
        "multi_act": {ph: np.array([_f(v) for v in act[i][:R]]) for i, ph in enumerate(phases)},
        "bonus": bonus,
        "retrig_bn": int(_val(wb, "RETRIG_SCATTERS")),
        "retrig_fs": int(_val(wb, "RETRIG_FS")),
        "rtp_cible": float(_val(wb, "RTP_CIBLE")),
        "rtp_min": float(_val(wb, "RTP_MIN")),
        "rtp_max": float(_val(wb, "RTP_MAX")),
        "part_spins": (float(_val(wb, "PART_SPINS_MIN")), float(_val(wb, "PART_SPINS_MAX"))),
        "part_bonus_max": float(_val(wb, "PART_BONUS_MAX")),
        "hit": (float(_val(wb, "HIT_MIN")), float(_val(wb, "HIT_MAX"))),
        "max_win": float(_val(wb, "MAX_WIN")),
        "sim_spins": int(_val(wb, "SIM_SPINS")),
        "sim_buy": int(_val(wb, "SIM_BUY")),
        "seed": int(_val(wb, "SIM_SEED")),
        "phases": phases,
    }
    validate(p)
    return p


def validate(p):
    t = p["types"]
    if t.count("SCATTER") != 1 or t.count("WILD") > 1 or "PAY" not in t:
        sys.exit("Paytable : il faut exactement 1 SCATTER, au plus 1 WILD et au moins 1 symbole PAY.")
    if not 3 <= p["R"] <= 6 or not 2 <= p["rows"] <= 6:
        sys.exit("Config : 3 à 6 rouleaux, 2 à 6 lignes.")
    b = p["bonus"]
    if not 1 <= len(b) <= 3:
        sys.exit("Config : il faut entre 1 et 3 bonus.")
    s = [x["bn"] for x in b]
    if s != sorted(set(s)) or s[-1] > p["R"]:
        sys.exit(f"Bonus : nombres de scatters croissants, au plus {p['R']} (1 scatter max par rouleau).")
    if "WILD" in t and (p["poids"]["base"][t.index("WILD"), 0] > 0):
        sys.exit("Le wild ne doit pas être sur le rouleau 1 (une way commence par un symbole naturel).")
    for ph, w in p["poids"].items():
        if (w.sum(axis=0) <= 0).any():
            sys.exit(f"Poids {ph} : chaque rouleau doit avoir un total > 0.")
        q = p["rows"] * w[t.index("SCATTER")] / w.sum(axis=0)
        if (q > 1).any():
            sys.exit(f"Poids {ph} : trop de scatters (lignes x P(scatter) doit rester <= 1).")
    for ph in p["phases"]:
        if p["multi_w"][ph].sum() <= 0 and p["multi_act"][ph].sum() > 0:
            sys.exit(f"Multis {ph} : des colonnes peuvent recevoir un multi mais aucune valeur n'a de poids.")


# --------------------------------------------------------------------------- #
# Calcul exact
# --------------------------------------------------------------------------- #
def stats_rouleaux(p, ph):
    """Par symbole payant et par rouleau : E[symboles comptés (symbole + wild)] et P(aucun).
    Au plus 1 scatter par rouleau : avec la probabilité Q = lignes x p(scatter), une case au hasard
    est le scatter et les autres sont tirées hors scatter. Chaque case garde sa probabilité p."""
    t, rows = p["types"], p["rows"]
    w = p["poids"][ph]
    pr = w / w.sum(axis=0)
    sc = t.index("SCATTER")
    wi = t.index("WILD") if "WILD" in t else None
    Q = rows * pr[sc]
    pay = [i for i, x in enumerate(t) if x == "PAY"]
    ec = np.zeros((len(t), p["R"]))
    p0 = np.ones((len(t), p["R"]))
    for s in pay:
        ps = pr[s] + (pr[wi] if wi is not None else 0)
        q = ps / (1 - pr[sc])
        ec[s] = rows * ps
        p0[s] = (1 - Q) * (1 - q) ** rows + Q * (1 - q) ** (rows - 1)
    return ec, p0, Q


def loi_scatters(Q):
    d = np.array([1.0])
    for q in Q:
        d = np.convolve(d, [1 - q, q])
    return d


def ev_ways(p, ph, facteur):
    """Gain moyen d'un spin : sum_s sum_k gain(s,k) x E[ways de longueur k] x facteur(k).
    facteur(k) = multi moyen d'une way de longueur k (indépendant des symboles)."""
    ec, p0, _ = stats_rouleaux(p, ph)
    R = p["R"]
    tot, par_sym = 0.0, np.zeros(len(p["types"]))
    for s, t in enumerate(p["types"]):
        if t != "PAY":
            continue
        for k in range(3, R + 1):
            g = p["pays"][s, k - 3]
            if g <= 0:
                continue
            e = g * np.prod(ec[s, :k]) * (p0[s, k] if k < R else 1.0) * facteur(k)
            par_sym[s] += e
            tot += e
    return tot, par_sym


def multi_moyen(p, ph):
    """E[valeur d'un multi] et probabilité d'activation de chaque colonne."""
    w = p["multi_w"][ph]
    ev = float((p["multi_val"] * w).sum() / w.sum()) if w.sum() > 0 else 0.0
    return ev, np.clip(p["multi_act"][ph], 0, 1)


def facteur_simple(p, ph):
    """Multis non collants : E[multi d'une way de longueur k] = P(aucun multi) + sum_r a_r E[V]."""
    ev, a = multi_moyen(p, ph)
    return lambda k: float(np.prod(1 - a[:k]) + a[:k].sum() * ev)


def survie_fs(p, fs0, ph):
    """P(N >= t), t = 1..T_MAX, N = nombre de FS joués (retriggers : +RETRIG_FS si >= RETRIG_SCATTERS)."""
    _, _, Q = stats_rouleaux(p, ph)
    pr = float(loi_scatters(Q)[p["retrig_bn"]:].sum())
    X = p["retrig_fs"]
    rmax = fs0 + X * T_MAX
    d = np.zeros(rmax + X + 2)
    d[fs0] = 1.0
    surv = []
    for _ in range(T_MAX):
        surv.append(d[1:].sum())
        nd = np.zeros_like(d)
        nd[0] = d[0]
        r = np.arange(1, len(d))
        np.add.at(nd, r - 1, d[1:] * (1 - pr))
        ok = r - 1 + X < len(d)
        np.add.at(nd, (r - 1 + X)[ok], d[1:][ok] * pr)
        d = nd
    return np.array(surv), pr


def analytique(p):
    """RTP exact de chaque composante (avant plafond du max win)."""
    out = {}
    fb = facteur_simple(p, "base")
    ev_base, sym_base = ev_ways(p, "base", fb)
    _, _, Qb = stats_rouleaux(p, "base")
    loi = loi_scatters(Qb)
    out["spins"] = ev_base
    out["sym_base"] = sym_base
    out["loi_scatters"] = loi
    tot = ev_base
    seuils = [b["bn"] for b in p["bonus"]] + [len(loi)]
    for k, b in enumerate(p["bonus"], 1):
        ph = f"fs{k}"
        surv, pr = survie_fs(p, b["fs"], ph)
        en = float(surv.sum())
        ev_m, a = multi_moyen(p, ph)
        if b["collant"]:
            t = np.arange(1, T_MAX + 1)

            def fac(kk, t=t, a=a, ev_m=ev_m, surv=surv):
                # E[multi d'une way au spin t] = P(aucun multi sur ses colonnes) + t x sum_r a_r x E[V]
                return float((surv * (np.prod((1 - a[:kk])[None, :] ** t[:, None], axis=1)
                                      + t * a[:kk].sum() * ev_m)).sum())
            gain, sym = ev_ways(p, ph, fac)
        else:
            f1 = facteur_simple(p, ph)
            g1, sym = ev_ways(p, ph, f1)
            gain, sym = g1 * en, sym * en
        freq = float(loi[seuils[k - 1]:seuils[k]].sum())
        out[f"bonus{k}"] = {"freq": freq, "gain": gain, "fs_moyens": en, "p_retrig": pr,
                            "rtp": freq * gain, "achat": gain + ev_base, "sym": sym}
        tot += freq * gain
    out["rtp"] = tot
    return out


# --------------------------------------------------------------------------- #
# Simulation Monte Carlo
# --------------------------------------------------------------------------- #
class Moteur:
    def __init__(self, p, rng):
        self.p, self.rng = p, rng
        self.R, self.rows = p["R"], p["rows"]
        t = p["types"]
        self.sc = t.index("SCATTER")
        self.wi = t.index("WILD") if "WILD" in t else -1
        self.pay = [i for i, x in enumerate(t) if x == "PAY"]
        self.prob = {ph: w / w.sum(axis=0) for ph, w in p["poids"].items()}
        self.q_sc = {ph: self.rows * v[self.sc] for ph, v in self.prob.items()}
        self.cum = {}
        for ph, v in self.prob.items():
            v = v.copy()
            v[self.sc] = 0
            self.cum[ph] = np.cumsum(v / v.sum(axis=0), axis=0)
        self.mcum = {ph: np.cumsum(w / w.sum()) if w.sum() > 0 else None for ph, w in p["multi_w"].items()}

    def tirage(self, n, ph, force_bn=None):
        u = self.rng.random((n, self.rows, self.R))
        g = np.empty(u.shape, dtype=np.int16)
        for r in range(self.R):
            g[:, :, r] = np.searchsorted(self.cum[ph][:, r], u[:, :, r], side="right")
        g = np.minimum(g, len(self.p["codes"]) - 1)
        if force_bn is None:
            a = self.rng.random((n, self.R)) < self.q_sc[ph]
        else:
            cle = np.log(self.rng.random((n, self.R))) / np.maximum(self.q_sc[ph], 1e-300)
            a = np.argsort(np.argsort(-cle, axis=1), axis=1) < force_bn
        rangee = self.rng.integers(0, self.rows, size=(n, self.R))
        i, r = np.nonzero(a)
        g[i, rangee[i, r], r] = self.sc
        return g

    def multis(self, n, ph):
        """Multis qui tombent ce spin : (n, R), 0 = pas de multi."""
        act = self.rng.random((n, self.R)) < self.p["multi_act"][ph]
        m = np.zeros((n, self.R))
        if act.any() and self.mcum[ph] is not None:
            idx = np.searchsorted(self.mcum[ph], self.rng.random(int(act.sum())), side="right")
            m[act] = self.p["multi_val"][np.minimum(idx, len(self.p["multi_val"]) - 1)]
        return m

    def gains(self, g, m):
        """Gain de chaque grille (x mise) avec les multis de colonne m (0 = aucun). Renvoie (gains, par symbole)."""
        p = self.p
        n = g.shape[0]
        w = (g == self.wi).sum(axis=1) if self.wi >= 0 else np.zeros((n, self.R))
        cm = np.cumsum(m, axis=1)                         # somme des multis des colonnes 1..k
        out = np.zeros(n)
        par = np.zeros(len(p["codes"]))
        for s in self.pay:
            c = (g == s).sum(axis=1) + w
            amorce = (g[:, :, 0] == s).any(axis=1)
            ways = np.where(amorce, c[:, 0], 0).astype(float)
            for k in range(2, self.R + 1):
                ways = ways * c[:, k - 1] if k > 1 else ways
                if k < 3:
                    continue
                gk = p["pays"][s, k - 3]
                if gk <= 0:
                    continue
                exact = ways * (c[:, k] == 0) if k < self.R else ways
                mult = np.where(cm[:, k - 1] > 0, cm[:, k - 1], 1.0)
                v = gk * exact * mult
                out += v
                par[s] += v.sum()
        return out, par

    def spin(self, n, ph, etat=None, force_bn=None):
        """Un spin. etat = multis collants (n, R) ou None. Renvoie (gains, nb scatters, par symbole, etat, m)."""
        g = self.tirage(n, ph, force_bn)
        neuf = self.multis(n, ph)
        m = neuf if etat is None else etat + neuf
        gain, par = self.gains(g, m)
        return gain, (g == self.sc).sum(axis=(1, 2)), par, (m if etat is not None else None), neuf

    def sessions(self, k, n, cap):
        """n sessions du bonus k. Renvoie (gain plafonné, FS joués, par symbole)."""
        b = self.p["bonus"][k - 1]
        ph = f"fs{k}"
        tot = np.zeros(n)
        reste = np.full(n, b["fs"], dtype=np.int64)
        joues = np.zeros(n, dtype=np.int64)
        etat = np.zeros((n, self.R)) if b["collant"] else None
        par = np.zeros(len(self.p["codes"]))
        act = np.arange(n)
        while act.size:
            e = etat[act] if etat is not None else None
            g, bn, ps, e2, _ = self.spin(act.size, ph, e)
            if etat is not None:
                etat[act] = e2
            tot[act] += g
            par += ps
            joues[act] += 1
            reste[act] += np.where(bn >= self.p["retrig_bn"], self.p["retrig_fs"], 0) - 1
            fini = (reste[act] <= 0) | (tot[act] >= cap) | (joues[act] >= MAX_FS_PAR_SESSION)
            act = act[~fini]
        return np.minimum(tot, cap), joues, par

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
    # CVaR 99,9 % (gain moyen des 0,1 % meilleurs tours), comme le SDK
    i0 = np.searchsorted(cw, 0.999 * cw[-1])
    seuil = r[srt][min(i0, len(r) - 1)]
    queue = r >= seuil
    cvar = float((w * r)[queue].sum() / w[queue].sum())
    return {"moy": moy, "hit": float(w[r > 0].sum()), "ecart_type": float(np.sqrt(max((w * r * r).sum() - moy ** 2, 0))),
            "mediane": med, "etl40b": float((w * r)[r >= 40 * cout].sum()), "etl10k": float((w * r)[r >= 10_000].sum()),
            "p_max": float(w[r >= cap].sum()), "max": float(r.max()), "cvar": cvar / cout}


def _distribution(r, w, cap):
    bornes = DIST_BORNES + [cap]
    d = [("0 x", float(w[r == 0].sum()))]
    for lo, hi in zip(bornes[:-1], bornes[1:]):
        sel = (r > lo) & (r < hi) if lo == 0 else (r >= lo) & (r < hi)
        d.append((f"{lo:g} – {hi:g} x" if hi < cap else f"{lo:g} x – max win", float(w[sel].sum())))
    d.append(("Max win", float(w[r >= cap].sum())))
    return d


def simuler_base(m, spins, lot=100_000, verbose=True):
    """Jeu de base par strates du nombre de scatters (loi exacte), les strates qui déclenchent un
    bonus étant sur-échantillonnées : les bonus rares sont mesurés précisément."""
    p = m.p
    cap = p["max_win"]
    loi = loi_scatters(m.q_sc["base"])
    seuil = p["bonus"][0]["bn"]
    n_min = max(spins // 50, 2000)
    nb = len(p["bonus"])
    R, W = [], []
    comp = np.zeros(nb + 1)                       # RTP : spins, bonus 1..nb
    par_type = np.zeros((nb + 1, 3))              # proba, gain bonus, FS joués
    sym = np.zeros(len(p["codes"]))
    var = 0.0
    for j, pj in enumerate(loi):
        if pj <= 0:
            continue
        nj = max(int(round(spins * pj)), n_min if j >= seuil else 1)
        wj = pj / nj
        rj = []
        fait = 0
        while fait < nj:
            n = min(lot, nj - fait)
            g, bn, ps, _, _ = m.spin(n, "base", force_bn=j)
            sym += wj * ps
            typ = m.type_bonus(bn)
            bon = np.zeros(n)
            jo = np.zeros(n)
            for k in range(1, nb + 1):
                sel = typ == k
                if sel.any():
                    t, js, _ = m.sessions(k, int(sel.sum()), cap)
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
           "dist": _distribution(r, w, cap), "sym": sym, **s}
    for k in range(1, nb + 1):
        f = par_type[k, 0]
        res[f"rtp_bonus{k}"] = comp[k]
        res[f"freq{k}"] = f
        res[f"gain{k}"] = par_type[k, 1] / f if f else float("nan")
        res[f"fsm{k}"] = par_type[k, 2] / f if f else float("nan")
    return res


def simuler_achat(m, k, n, lot=20_000, verbose=True):
    """Bonus k joué comme un achat : spin de déclenchement (k-ième seuil de scatters) + le bonus."""
    p = m.p
    cap = p["max_win"]
    b = p["bonus"][k - 1]
    parts = []
    for i in range(0, n, lot):
        nn = min(lot, n - i)
        g = m.spin(nn, "base", force_bn=b["bn"])[0]
        t, _, _ = m.sessions(k, nn, cap)
        parts.append(np.minimum(g + t, cap))
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
            "prix_conseille": s["moy"] / p["rtp_cible"], "dist": _distribution(r, w, cap), **s}


def simuler(p, spins=None, buy=None, verbose=True):
    m = Moteur(p, np.random.default_rng(p["seed"]))
    res = {"date": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "exact": analytique(p)}
    res["base"] = simuler_base(m, spins or p["sim_spins"], verbose=verbose)
    buy = p["sim_buy"] if buy is None else buy
    res["achats"] = {k: simuler_achat(m, k, buy, verbose=verbose) for k in range(1, len(p["bonus"]) + 1) if buy}
    return res


# --------------------------------------------------------------------------- #
# Contrôles (règles Stake Engine + équilibre)
# --------------------------------------------------------------------------- #
def controles(p, r):
    """Liste de (contrôle, valeur, règle, OK/ÉCHEC/À SURVEILLER)."""
    e, b = r["exact"], r.get("base")
    cible = p["rtp_cible"]
    L = []

    def add(nom, val, regle, ok, txt=None):
        L.append((nom, txt if txt is not None else val, regle, "OK" if ok else "ÉCHEC"))

    lo, hi = p["rtp_min"], p["rtp_max"]
    add("RTP exact du jeu de base", f"{e['rtp']:.3%}", f"entre {lo:.2%} et {hi:.2%}", lo <= e["rtp"] <= hi)
    if b:
        add("RTP simulé (plafond compris)", f"{b['rtp']:.3%} ± {b['marge']:.3%}", "écart à l'exact < 3 marges",
            abs(b["rtp"] - e["rtp"]) <= 3 * b["marge"] + 0.001)
    part = e["spins"] / e["rtp"]
    a0, a1 = p["part_spins"]
    add("Part des spins (hors bonus)", f"{part:.1%}", f"{a0:.0%} à {a1:.0%} : les spins rapportent sans tout donner", a0 <= part <= a1)
    for k, bb in enumerate(p["bonus"], 1):
        pk = e[f"bonus{k}"]["rtp"] / e["rtp"]
        add(f"Part du bonus {k}", f"{pk:.1%}", f"au plus {p['part_bonus_max']:.0%} : aucun bonus ne donne tout",
            pk <= p["part_bonus_max"])
        add(f"Bonus {k} : fréquence", f"1 sur {1 / e[f'bonus{k}']['freq']:,.0f}", "entre 1/100 et 1/1 000 000",
            1e-6 <= e[f"bonus{k}"]["freq"] <= 0.01)
    if b:
        h0, h1 = p["hit"]
        add("Fréquence de gain", f"{b['hit']:.1%} (1 sur {1 / b['hit']:.1f})", f"1 sur {1 / h1:.0f} à 1 sur {1 / h0:.0f} (règle d'approbation)",
            h0 <= b["hit"] <= h1)
        pm = b["p_max"]
        add("Max win atteignable", f"1 sur {1 / pm:,.0f}" if pm else "jamais observé",
            "au moins 1 sur 20 000 000 (règle d'approbation)", pm >= 1 / 20e6)
        add("3 étoiles : etl40b (base)", f"{b['etl40b']:.3f}", "≤ 0,9", b["etl40b"] <= 0.9)
        add("3 étoiles : cvar (base)", f"{b['cvar']:.0f}", "≤ 800", b["cvar"] <= 800)
    for k, a in r.get("achats", {}).items():
        if not a["prix"]:
            continue
        add(f"Achat bonus {k} : RTP simulé", f"{a['rtp']:.2%} ± {a['marge']:.2%}",
            "à 0,5 % du jeu de base (règle d'approbation) ; corrigé exactement par la pondération",
            abs(a["rtp"] - cible) <= 0.005 + a["marge"])
        ok = a["etl40b"] <= 0.9
        L.append((f"Achat bonus {k} : 3 étoiles etl40b", f"{a['etl40b']:.3f}",
                  "≤ 0,9 ; sinon la pondération du SDK rend les gains ≥ 40x le prix plus rares, dans ce mode seulement",
                  "OK" if ok else f"CORRIGÉ PAR LA PONDÉRATION (≈ x{a['etl40b'] / 0.88:.1f} plus rares)"))
        L.append((f"Achat bonus {k} : 3 étoiles etl10k", f"{a['etl10k']:.3f}",
                  "≤ 0,8 ; sinon la pondération rend le max win plus rare dans ce mode",
                  "OK" if a["etl10k"] <= 0.8 else "CORRIGÉ PAR LA PONDÉRATION"))
    return L


# --------------------------------------------------------------------------- #
# Écriture : onglet Simulation + rapport de validation
# --------------------------------------------------------------------------- #
LIGNES_SIM = ["date", "spins", "rtp", "marge", "rtp_spins", "hit", "ecart_type", "mediane", "max", "p_max",
              "etl40b", "etl10k", "cvar"] + [f"{x}{k}" for k in (1, 2, 3) for x in ("freq", "gain", "fsm", "rtp_bonus")]
LIBELLES_SIM = {
    "date": "Date de la simulation", "spins": "Spins simulés", "rtp": "RTP simulé (plafond compris)",
    "marge": "Marge d'erreur (± à 95 %)", "rtp_spins": "RTP des spins (hors bonus)", "hit": "Fréquence de gain",
    "ecart_type": "Écart-type par tour (x mise)", "mediane": "Gain médian", "max": "Max observé (x mise)",
    "p_max": "Probabilité du max win", "etl40b": "3 étoiles : etl40b (≤ 0,9)", "etl10k": "3 étoiles : etl10k (≤ 0,8)",
    "cvar": "3 étoiles : cvar (≤ 800)",
    **{f"freq{k}": f"Bonus {k} : probabilité par spin" for k in (1, 2, 3)},
    **{f"gain{k}": f"Bonus {k} : gain moyen (x mise)" for k in (1, 2, 3)},
    **{f"fsm{k}": f"Bonus {k} : FS joués en moyenne" for k in (1, 2, 3)},
    **{f"rtp_bonus{k}": f"Bonus {k} : RTP apporté" for k in (1, 2, 3)},
}
LIGNES_ACHAT = ["sessions", "prix", "gain", "rtp", "marge", "prix_conseille", "mediane", "max", "p_max", "etl40b",
                "etl10k", "cvar"]
LIBELLES_ACHAT = {"sessions": "Tours simulés", "prix": "Prix (x mise)", "gain": "Gain moyen (x mise)",
                  "rtp": "RTP au prix actuel", "marge": "Marge d'erreur (± à 95 %)",
                  "prix_conseille": "Prix conseillé (gain moyen / RTP cible)", "mediane": "Gain médian",
                  "max": "Max observé", "p_max": "Probabilité du max win", "etl40b": "3 étoiles : etl40b (≤ 0,9)",
                  "etl10k": "3 étoiles : etl10k (≤ 0,8)", "cvar": "3 étoiles : cvar (≤ 800)"}
SIM_L0 = 5                                   # 1re ligne du bloc « jeu de base »
SIM_A0 = SIM_L0 + len(LIGNES_SIM) + 2        # en-tête du bloc « achats »
SIM_C0 = SIM_A0 + len(LIGNES_ACHAT) + 3      # en-tête du bloc « contrôles »
SIM_LIGNE = {k: SIM_L0 + i for i, k in enumerate(LIGNES_SIM)}
SIM_LIGNE.update({f"a_{k}": SIM_A0 + 1 + i for i, k in enumerate(LIGNES_ACHAT)})


def cellule(cle, col="B"):
    return f"{col}{SIM_LIGNE[cle]}"


def ecrire(path, p, r, ctrl):
    wb = load_workbook(path)
    ws = wb["Simulation"]

    def put(ref, v):
        ws[ref].value = None if v is None or (isinstance(v, float) and v != v) else (float(v) if isinstance(v, np.floating) else v)

    b = r["base"]
    for k in LIGNES_SIM:
        put(cellule(k), r["date"] if k == "date" else b.get(k))
    for k in LIGNES_ACHAT:
        for kk, col in ((1, "B"), (2, "C"), (3, "D")):
            a = r["achats"].get(kk)
            put(f"{col}{SIM_LIGNE['a_' + k]}", a.get(k) if a else None)
    for i in range(25):
        for col in "ABCD":
            put(f"{col}{SIM_C0 + 1 + i}", None)
    for i, (nom, val, regle, etat) in enumerate(ctrl):
        for col, v in zip("ABCD", (nom, val, regle, etat)):
            put(f"{col}{SIM_C0 + 1 + i}", v)
    for i in range(12):
        for col in "FG":
            put(f"{col}{5 + i}", None)
    for i, (lbl, v) in enumerate(b["dist"]):
        put(f"F{5 + i}", lbl)
        put(f"G{5 + i}", v)
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)


def empreinte(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def rapport(path_xlsx, p, r, ctrl, sortie):
    """Rapport de validation au format du « Math Sign-Off Template » (senior-game-math-engineer)."""
    e, b = r["exact"], r["base"]
    L = [f"# Rapport de validation des maths", "",
         "Format : « Math Sign-Off Template » du repo egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine.", "",
         "## 1. Périmètre", f"- Classeur : `{Path(path_xlsx).name}` (empreinte {empreinte(path_xlsx)})",
         f"- Date : {r['date']}", f"- Grille : {p['R']} rouleaux x {p['rows']} lignes ({p['rows'] ** p['R']:,} ways)",
         f"- Modes : base" + "".join(f", achat bonus {k}" for k, bb in enumerate(p['bonus'], 1) if bb['prix']), "",
         "## 2. Hypothèses",
         "- Gains en x la mise totale ; montants arrondis au centième par le SDK.",
         "- Multis de colonne indépendants des symboles ; une way prend la somme des multis de ses colonnes.",
         "- Calcul exact avant plafond du max win ; la simulation applique le plafond.", "",
         "## 3. Décomposition du RTP (calcul exact)", "", "| Composante | Fréquence | Gain moyen | RTP |", "|---|---|---|---|",
         f"| Spins (jeu de base, multis compris) | chaque spin | {e['spins']:.4f} x | {e['spins']:.3%} |"]
    for k, bb in enumerate(p["bonus"], 1):
        x = e[f"bonus{k}"]
        L.append(f"| Bonus {k} « {bb['nom']} » ({'collant' if bb['collant'] else 'non collant'}) | 1 sur {1 / x['freq']:,.0f} | "
                 f"{x['gain']:.1f} x ({x['fs_moyens']:.1f} FS) | {x['rtp']:.3%} |")
    L += [f"| **Total** | | | **{e['rtp']:.3%}** |", "",
          "## 4. Méthode", f"- Simulation : `simulateur.py`, graine {p['seed']}, {b['spins']:,} spins de base (strates du nombre de scatters),"
          f" {next(iter(r['achats'].values()))['sessions'] if r['achats'] else 0:,} tours par bonus.",
          "- Le repo recommande ≥ 1 000 000 de spins pour orienter le calage et ≥ 20 000 000 pour valider.", "",
          "## 5. Résultats", "", "| Indicateur | Exact | Simulé | Écart | Statut |", "|---|---|---|---|---|",
          f"| RTP | {e['rtp']:.3%} | {b['rtp']:.3%} ± {b['marge']:.3%} | {b['rtp'] - e['rtp']:+.3%} | "
          f"{'OK' if abs(b['rtp'] - e['rtp']) <= 3 * b['marge'] + 0.001 else 'ÉCART'} |"]
    for k in range(1, len(p["bonus"]) + 1):
        x = e[f"bonus{k}"]
        L.append(f"| Bonus {k} : fréquence | 1 sur {1 / x['freq']:,.0f} | 1 sur {1 / b[f'freq{k}']:,.0f} | | |")
        L.append(f"| Bonus {k} : gain moyen | {x['gain']:.1f} x | {b[f'gain{k}']:.1f} x | | |")
    L += [f"| Fréquence de gain | | {b['hit']:.2%} | | |", f"| Écart-type | | {b['ecart_type']:.1f} x | | |",
          f"| Max win | {p['max_win']:,.0f} x | 1 tour sur {1 / b['p_max']:,.0f} | | |" if b["p_max"] else
          f"| Max win | {p['max_win']:,.0f} x | non observé | | |", "",
          "## 6. Contrôles", "", "| Contrôle | Valeur | Règle | Statut |", "|---|---|---|---|"]
    L += [f"| {a} | {v} | {rg} | {s} |" for a, v, rg, s in ctrl]
    ech = [a for a, _, _, s in ctrl if s in ("ÉCHEC", "ÉCART")]
    L += ["", "## 7. Décision", f"- Statut : **{'VALIDÉ' if not ech else 'À REVOIR'}**"
          + ("" if not ech else " (" + ", ".join(ech) + ")"),
          "- Rappel : la validation finale se fait sur les fichiers générés par le SDK (RTP pondéré des books).", ""]
    Path(sortie).write_text("\n".join(L), encoding="utf-8")


def afficher_exact(p, e):
    print(f"CALCUL EXACT — RTP {e['rtp']:.3%} (cible {p['rtp_cible']:.2%})")
    print(f"  spins {e['spins']:.3%} ({e['spins'] / e['rtp']:.0%})")
    for k, b in enumerate(p["bonus"], 1):
        x = e[f"bonus{k}"]
        print(f"  bonus {k} {b['nom']:<18} 1/{1 / x['freq']:>9,.0f}  gain {x['gain']:8.1f}x  FS {x['fs_moyens']:.1f}  "
              f"RTP {x['rtp']:.3%} ({x['rtp'] / e['rtp']:.0%})  achat ≈ {x['achat']:.1f}x -> prix conseillé "
              f"{x['achat'] / p['rtp_cible']:.0f}x")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--spins", type=int)
    ap.add_argument("--buy", type=int)
    ap.add_argument("--exact", action="store_true", help="calcul exact seulement")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    p = load_params(a.classeur)
    if a.exact:
        afficher_exact(p, analytique(p))
        return
    r = simuler(p, a.spins, a.buy)
    afficher_exact(p, r["exact"])
    ctrl = controles(p, r)
    print()
    for nom, val, regle, etat in ctrl:
        print(f"  [{etat:^6}] {nom:<34} {val:<28} {regle}")
    if not a.no_write:
        ecrire(a.classeur, p, r, ctrl)
        rapport(a.classeur, p, r, ctrl, Path(a.classeur).with_name("rapport_validation.md"))
        print(f"\nRésultats écrits dans {a.classeur} (onglet Simulation) et rapport_validation.md")


if __name__ == "__main__":
    main()
