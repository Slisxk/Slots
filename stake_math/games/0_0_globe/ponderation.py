"""Pondération « naturelle » des résultats (remplace l'optimiseur Rust du SDK).

Le SDK simule des résultats par critère, avec des quotas arbitraires. Il faut ensuite donner à chaque
résultat un poids pour que le jeu ait les bonnes probabilités. L'optimiseur du SDK le fait en déformant
la distribution des gains ; ici on garde la distribution NATURELLE du jeu, mesurée par la feuille :

  * modes « spin » (base, boost) : chaque case (critère SDK bonus1/2/3 = grille de départ forcée,
    bonus réellement obtenu 1/2/3, lu dans l'événement freeSpinTrigger) reçoit sa probabilité réelle
    (params.json["targets"][mode]["joint"], simulée par la feuille) ; « basegame » (gagnant sans bonus)
    reçoit la fréquence de gain de la feuille moins les bonus ; « 0 » prend le reste ; le max win reçoit
    wincap_rtp du RTP. Tous les résultats d'une case ont le même poids ;
  * modes bonus buy : tous les résultats ont le même poids ;
  * puis le RTP est ajusté exactement par un « basculement exponentiel » (poids × exp(θ·gain)) : le plus
    petit écart possible à la distribution naturelle. Il ne corrige que le bruit des books (quelques %) ;
  * limites « 3 étoiles » du SDK (utils/rgs_verification.py) : si l'espérance des gains >= 40x le coût
    du mode (etl40b) ou >= 10 000x (etl10k) dépasse sa limite, seuls ces gros gains sont rendus plus
    rares, juste assez pour passer, le RTP restant exact.

Écrit library/publish_files/lookUpTable_<mode>_0.csv (format RGS : id, poids uint64, payout).
"""

import csv
import io
import json
import math
import os

import numpy as np
import zstandard

TOTAL = 2**60          # somme des poids (doit rester <= uint64)
ETL40_LIMITE, ETL40_CIBLE = 0.9, 0.88    # limite « 3 étoiles » du SDK et cible (les poids sont exacts)
ETL10K_LIMITE, ETL10K_CIBLE = 0.8, 0.78


def _lire_books(path):
    """id -> (critère, payout en x mise, bonus obtenu ou 0)."""
    out = {}
    with open(path, "rb") as fh:
        flux = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for ligne in flux:
            b = json.loads(ligne)
            bonus = next((e.get("bonus", 0) for e in b["events"] if e["type"] == "freeSpinTrigger"), 0)
            out[b["id"]] = (b["criteria"], b["payoutMultiplier"] / 100, bonus)
    return out


def _bisection(f, lo, hi, n=100):
    """Racine de f croissante sur [lo, hi]."""
    for _ in range(n):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _contraindre(evaluer):
    """Cherche (l40, l10k) <= 0, le plus près de 0 possible, pour respecter les limites 3 étoiles.
    evaluer(l40, l10k) -> (etl40b, etl10k)."""
    l40 = l10k = 0.0
    e40, e10 = evaluer(0.0, 0.0)
    if e40 > ETL40_LIMITE:
        l40 = _bisection(lambda x: evaluer(x, 0.0)[0] - ETL40_CIBLE, -60.0, 0.0)
        e40, e10 = evaluer(l40, 0.0)
    if e10 > ETL10K_LIMITE:
        l10k = _bisection(lambda x: evaluer(l40, x)[1] - ETL10K_CIBLE, -60.0, 0.0)
    return l40, l10k


def _ecrire(path, poids_par_id, books):
    ids = sorted(books)
    tot = sum(poids_par_id.get(i, 0.0) for i in ids)
    entiers = {i: int(round(poids_par_id.get(i, 0.0) / tot * TOTAL)) for i in ids}
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for i in ids:
            w.writerow([i, entiers[i], int(round(books[i][1] * 100))])
    return sum(entiers[i] * books[i][1] for i in ids) / sum(entiers.values())


def _ajuster(books, w0, cible_ev, cout, p_wc):
    """Part commune à tous les modes. w0 : poids naturels des résultats hors max win (somme 1).
    Poids finaux w_i ∝ w0_i · exp(θ·p_i) × réduction de la queue (l40, l10k) : le basculement
    exponentiel est le plus petit écart possible à la distribution naturelle qui donne le RTP exact.
    Renvoie (poids par id, détail)."""
    ids = [i for i in w0 if w0[i] > 0]
    wc = [i for i, b in books.items() if b[0] == "wincap"]
    moy_wc = float(np.mean([books[i][1] for i in wc])) if wc else 0.0
    if not wc:
        p_wc = 0.0
    p_reste = 1 - p_wc
    cible = (cible_ev - p_wc * moy_wc) / p_reste
    pays = np.array([books[i][1] for i in ids])
    base = np.array([w0[i] for i in ids])
    base /= base.sum()
    seuil40 = 40 * cout
    p_max = pays.max()
    if not (pays.min() < cible < p_max):
        raise ValueError(f"RTP impossible : gain moyen cible {cible:.3f} hors de [{pays.min()}, {p_max}]")
    q40, q10 = pays >= seuil40, pays >= 10_000

    def bascule(l40, l10k):
        f = base * np.exp(np.where(q40, l40, 0.0) + np.where(q10, l10k, 0.0))

        def poids(theta):
            e = f * np.exp(theta * (pays - (p_max if theta > 0 else 0.0)))
            return e / e.sum()

        theta = _bisection(lambda t: float(poids(t) @ pays) - cible, -1.0, 1.0, 200)
        return poids(theta), theta

    def evaluer(l40, l10k):
        w, _ = bascule(l40, l10k)
        e40 = (p_wc * moy_wc if moy_wc >= seuil40 else 0.0) + p_reste * float(w[q40] @ pays[q40])
        e10 = (p_wc * moy_wc if moy_wc >= 10_000 else 0.0) + p_reste * float(w[q10] @ pays[q10])
        return e40, e10

    l40, l10k = _contraindre(evaluer)
    w, theta = bascule(l40, l10k)
    poids = {i: p_reste * float(wi) for i, wi in zip(ids, w)}
    for i in wc:
        poids[i] = p_wc / len(wc)
    e40, e10 = evaluer(l40, l10k)
    detail = {"wincap": round(p_wc, 10), "moyenne_naturelle": round(float(base @ pays), 4),
              "moyenne_cible": round(cible, 4), "theta": theta,
              "hit_naturel": round(float(base[pays > 0].sum()) * p_reste + p_wc, 4),
              "hit_final": round(float(w[pays > 0].sum()) * p_reste + p_wc, 4),
              "etl40b": round(e40, 4), "etl10k": round(e10, 4),
              "gros_gains_rendus_plus_rares_x": round(math.exp(-l40), 2),
              "max_win_rendu_plus_rare_x": round(math.exp(-l10k), 2)}
    return poids, detail


def _mode_spin(books, cible_ev, cout, p_wc, joint, hit):
    """Modes base / boost : poids naturels de chaque catégorie (mesurés par la feuille), puis _ajuster."""
    par_cle = {}
    for i, (c, p, k) in books.items():
        cle = (int(c[5:]), k) if c.startswith("bonus") else c
        par_cle.setdefault(cle, []).append(i)

    # Probabilité réelle de chaque case (critère c, bonus k) ; une case sans résultat cède sa probabilité
    # aux autres cases du même bonus.
    p_case = {}
    for k in range(1, len(joint) + 1):
        cases = {c: joint[c - 1][k - 1] for c in range(1, len(joint) + 1)}
        total_k = sum(cases.values())
        dispo = {c: v for c, v in cases.items() if (c, k) in par_cle and v > 0}
        if total_k > 0 and not dispo:
            dispo = {c: 1.0 for c in cases if (c, k) in par_cle}
            if not dispo:
                raise ValueError(f"Aucun résultat SDK pour le bonus {k} : augmente le nombre de books.")
        s = sum(dispo.values())
        for c, v in dispo.items():
            p_case[(c, k)] = total_k * v / s
    p_bonus = sum(p_case.values())
    # Tours gagnants sans bonus : fréquence de gain de la feuille moins les tours bonus
    p_bg = hit - p_wc - p_bonus
    p_0 = 1 - p_wc - p_bonus - p_bg
    if not (0 < p_bg < 1 and p_0 > 0):
        raise ValueError(f"Fréquence de gain incohérente (P(basegame) = {p_bg:.4f}). Relance la simulation.")
    w0 = {}
    for cle, pr in list(p_case.items()) + [("basegame", p_bg), ("0", p_0)]:
        for i in par_cle.get(cle, []):
            w0[i] = pr / len(par_cle[cle]) / (1 - p_wc)
    poids, detail = _ajuster(books, w0, cible_ev, cout, p_wc)
    detail.update({f"bonus{k}": round(sum(v for (c, kk), v in p_case.items() if kk == k), 8)
                   for k in range(1, len(joint) + 1)})
    return poids, detail


def _mode_achat(books, cible_ev, cout, p_wc):
    """Modes bonus buy : tous les résultats ont le même poids naturel, puis _ajuster."""
    ids = [i for i, b in books.items() if b[0] != "wincap"]
    return _ajuster(books, {i: 1.0 / len(ids) for i in ids}, cible_ev, cout, p_wc)


def ponderer(config, params, modes=None):
    """Écrit les lookup tables pondérées des modes demandés. Renvoie un résumé."""
    t = params["targets"]
    resume = {}
    for bm in config.bet_modes:
        mode, cout = bm.get_name(), bm.get_cost()
        if modes is not None and mode not in modes:
            continue
        books = _lire_books(os.path.join(config.publish_path, f"books_{mode}.jsonl.zst"))
        cible_ev = config.rtp * cout
        p_wc = t["wincap_rtp"] * cout / config.wincap
        if mode in config.buy_modes:
            poids, detail = _mode_achat(books, cible_ev, cout, p_wc)
        else:
            poids, detail = _mode_spin(books, cible_ev, cout, p_wc, t[mode]["joint"], t[mode]["hit"])
        path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
        moyenne = _ecrire(path, poids, books)
        resume[mode] = {"rtp": moyenne / cout, **detail}
        print(f"Pondération naturelle {mode}: RTP {moyenne / cout:.6f}  {detail}")
    return resume
