"""Pondération « naturelle » des résultats (remplace l'optimiseur Rust par défaut).

Le SDK simule des résultats par catégorie (« 0 », « basegame », « freegame », « wincap ») avec des
quotas arbitraires. Il faut ensuite donner à chaque résultat un poids pour que le jeu ait les bonnes
probabilités. L'optimiseur du SDK le fait en déformant la distribution des gains ; ici on garde la
distribution NATURELLE du jeu :

  * chaque catégorie reçoit sa probabilité réelle (fréquence du bonus mesurée par la feuille,
    max win fixé par la cible wincap_rtp), et tous les résultats d'une catégorie ont le même poids ;
  * mode base : la probabilité de « basegame » est ajustée pour que le RTP tombe pile sur la cible
    (« 0 » prend le reste) ;
  * mode bonus : le RTP est ajusté par un « basculement exponentiel » minimal des poids des
    free spins (le plus petit écart possible à la distribution naturelle) ;
  * limites « 3 étoiles » du SDK (utils/rgs_verification.py) : si l'espérance des gains >= 40x le
    coût du mode (etl40b) dépasse la limite, seuls ces gros gains sont rendus plus rares, juste
    assez pour passer avec une marge (ETL40_CIBLE), le RTP restant exact.

Écrit library/publish_files/lookUpTable_<mode>_0.csv (format RGS : id, poids uint64, payout).
"""

import csv
import io
import json
import math
import os

import zstandard

TOTAL = 2**60  # somme des poids (doit rester <= uint64)
ETL40_LIMITE = 0.9   # limite « 3 étoiles » du SDK
ETL40_CIBLE = 0.8    # cible, avec une marge


def _lire_books(path):
    """id -> (critère, payout en x mise)."""
    out = {}
    with open(path, "rb") as fh:
        flux = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for ligne in flux:
            b = json.loads(ligne)
            out[b["id"]] = (b["criteria"], b["payoutMultiplier"] / 100)
    return out


def _bascule(pays, cible, queue=None, lam=0.0):
    """Poids w_i ∝ exp(θ·p_i + λ·[i dans la queue]) (normalisés) dont la moyenne vaut `cible`."""
    lo, hi = -1.0, 1.0
    p_max = max(pays)
    queue = queue or [False] * len(pays)

    def moyenne(theta):
        m = theta * p_max if theta > 0 else 0.0
        e = [math.exp(theta * p - m + (lam if q else 0.0)) for p, q in zip(pays, queue)]
        s = sum(e)
        return sum(w * p for w, p in zip(e, pays)) / s, [w / s for w in e]

    if not (min(pays) < cible < p_max):
        raise ValueError(f"RTP impossible : moyenne cible {cible:.3f} hors de [{min(pays)}, {p_max}]")
    for _ in range(200):
        mid = (lo + hi) / 2
        m, w = moyenne(mid)
        if m < cible:
            lo = mid
        else:
            hi = mid
    return moyenne((lo + hi) / 2)[1], (lo + hi) / 2


def _ecrire(path, poids_par_id, books):
    ids = sorted(books)
    tot = sum(poids_par_id[i] for i in ids)
    entiers = {i: int(round(poids_par_id[i] / tot * TOTAL)) for i in ids}
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for i in ids:
            w.writerow([i, entiers[i], int(round(books[i][1] * 100))])
    s = sum(entiers.values())
    return sum(entiers[i] * books[i][1] for i in ids) / s


def ponderer(config, params):
    """Écrit les lookup tables pondérées pour les modes base et bonus. Renvoie un résumé."""
    t = params["targets"]
    wincap = config.wincap
    resume = {}
    for bm in config.bet_modes:
        mode, cout = bm.get_name(), bm.get_cost()
        books = _lire_books(os.path.join(config.publish_path, f"books_{mode}.jsonl.zst"))
        par_crit = {}
        for i, (c, p) in books.items():
            par_crit.setdefault(c, []).append(i)
        moy = {c: sum(books[i][1] for i in ids) / len(ids) for c, ids in par_crit.items()}
        poids = {}
        p_wc = t["wincap_rtp"] * cout / wincap if "wincap" in par_crit else 0.0

        if mode == "base":
            p_fg = 1 / t["freegame_hr"]
            reste = config.rtp - p_wc * moy.get("wincap", 0) - p_fg * moy["freegame"]
            p_bg = reste / moy["basegame"]
            p_0 = 1 - p_wc - p_fg - p_bg
            if not (0 < p_bg < 1 and p_0 > 0):
                raise ValueError(f"Mode base : RTP {config.rtp} impossible avec ces résultats "
                                 f"(P(basegame) = {p_bg:.4f}). Recale la feuille.")
            proba = {"wincap": p_wc, "freegame": p_fg, "basegame": p_bg, "0": p_0}
            for c, ids in par_crit.items():
                for i in ids:
                    poids[i] = proba[c] / len(ids)
            detail = {c: round(v, 8) for c, v in proba.items()}
        else:
            p_fg = 1 - p_wc
            cible = (config.rtp * cout - p_wc * moy.get("wincap", 0)) / p_fg
            ids = par_crit["freegame"]
            pays = [books[i][1] for i in ids]
            seuil = 40 * cout
            queue = [p >= seuil for p in pays]
            etl_wc = p_wc * moy.get("wincap", 0) if moy.get("wincap", 0) >= seuil else 0.0

            def etl40(w):
                return etl_wc + p_fg * sum(wi * p for wi, p, q in zip(w, pays, queue) if q)

            lam = 0.0
            w, theta = _bascule(pays, cible)
            if etl40(w) > ETL40_LIMITE:
                # λ < 0 : rend les gains >= 40x le coût plus rares, jusqu'à etl40b = ETL40_CIBLE
                lo, hi = -50.0, 0.0
                for _ in range(80):
                    lam = (lo + hi) / 2
                    w, theta = _bascule(pays, cible, queue, lam)
                    if etl40(w) > ETL40_CIBLE:
                        hi = lam
                    else:
                        lo = lam
            for i, wi in zip(ids, w):
                poids[i] = p_fg * wi
            for i in par_crit.get("wincap", []):
                poids[i] = p_wc / len(par_crit["wincap"])
            detail = {"wincap": round(p_wc, 10), "freegame": round(p_fg, 10),
                      "moyenne_fs_naturelle": round(moy["freegame"], 3), "moyenne_fs_cible": round(cible, 3),
                      "theta": theta, "etl40b": round(etl40(w), 4),
                      "gros_gains_rendus_plus_rares_x": round(math.exp(-lam), 2)}

        path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
        moyenne = _ecrire(path, poids, books)
        resume[mode] = {"rtp": moyenne / cout, **detail}
        print(f"Pondération naturelle {mode}: RTP {moyenne / cout:.6f}  {detail}")
    return resume
