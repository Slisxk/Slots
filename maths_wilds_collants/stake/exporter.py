#!/usr/bin/env python3
"""
Exporte le classeur (../classeur_maths.xlsx) vers un jeu pour le math SDK de Stake Engine.

    python exporter.py ../classeur_maths.xlsx
    python exporter.py ../classeur_maths.xlsx --game-id 12_3_monjeu --nom "Mon Jeu" --studio mon_studio

Écrit dans games/<game-id>/ :
  - params.json : paytable, bonus (scatters, FS, wilds NON / FIXE / MARCHE, prix), multis des wilds, retrigger,
    cibles de pondération
  - reels/BR0.csv (jeu de base), FR1.csv, FR2.csv… (FS de chaque bonus) : les MÊMES bandes que le simulateur
    (simulateur.construire_bandes : symboles géants, scatters espacés)
  - reels/FRWCAP1.csv… : bandes FS avec 4 fois plus de wilds, seulement pour fabriquer les résultats « max win »
  - reels/PAD_BR.csv, PAD_FR.csv : bandes courtes pour l'animation des rouleaux (front-end seulement)
Lance d'abord simulateur.py (fréquence de gain et du max win simulées, utilisées par la pondération).
"""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import simulateur  # noqa: E402

MODELE = ICI / "games" / "0_0_wilds"
FICHIERS = ["game_config.py", "game_executables.py", "game_override.py", "game_events.py", "gamestate.py",
            "ponderation.py", "run.py", "readme.txt"]
MODES_ACHAT = {1: "bonus", 2: "super", 3: "bonus3"}
WCAP_WILDS = 4


def erreur(msg):
    sys.exit(f"Erreur : {msg}")


def ecrire_bandes(path, bandes, codes):
    L = min(len(b) for b in bandes)                 # le SDK veut des colonnes de même longueur
    with open(path, "w", encoding="utf-8") as f:
        for i in range(L):
            f.write(",".join(codes[b[i]] for b in bandes) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--game-id", default="0_0_wilds")
    ap.add_argument("--nom", default="Sticky Wilds")
    ap.add_argument("--provider", type=int, default=0)
    ap.add_argument("--studio", default="mon_studio")
    a = ap.parse_args()

    p = simulateur.load_params(a.classeur)
    from openpyxl import load_workbook
    ws = load_workbook(a.classeur)["Simulation"]
    v = lambda cle, col="B": ws[f"{col}{simulateur.SIM_LIGNE[cle]}"].value
    est, hit, p_max = v("estimation"), v("hit"), v("p_max")
    if not isinstance(est, (int, float)) or not isinstance(hit, (int, float)):
        erreur("l'onglet Simulation est incomplet : lance d'abord  python simulateur.py <classeur>  (simulation complète)")
    if not p["rtp_min"] <= est <= p["rtp_max"]:
        erreur(f"RTP estimé {est:.3%} hors de [{p['rtp_min']:.2%} ; {p['rtp_max']:.2%}] : recale le classeur.")
    codes, types = p["codes"], p["types"]
    for c in codes:
        if not str(c).isalnum():
            erreur(f"code symbole invalide « {c} » (lettres et chiffres uniquement).")

    dossier = ICI / "games" / a.game_id
    (dossier / "reels").mkdir(parents=True, exist_ok=True)
    if dossier != MODELE:
        for f in FICHIERS:
            if not (dossier / f).exists():
                shutil.copy(MODELE / f, dossier / f)

    # Bandes : exactement celles du simulateur
    ecrire_bandes(dossier / "reels" / "BR0.csv", simulateur.construire_bandes(p, "base"), codes)
    pw = copy.deepcopy(p)
    wi = types.index("WILD")
    bonuses = []
    nb = len(p["bonus"])
    for k, b in enumerate(p["bonus"], 1):
        ecrire_bandes(dossier / "reels" / f"FR{k}.csv", simulateur.construire_bandes(p, f"fs{k}"), codes)
        pw["poids"][f"wcap{k}"] = p["poids"][f"fs{k}"].copy()
        pw["poids"][f"wcap{k}"][wi] *= WCAP_WILDS
        ecrire_bandes(dossier / "reels" / f"FRWCAP{k}.csv", simulateur.construire_bandes(pw, f"wcap{k}"), codes)
        bonuses.append({"id": k, "name": b["nom"], "scatters": b["bn"], "spins": b["fs"], "wilds": b["wilds"],
                        "buy_cost": b["prix"], "mode": MODES_ACHAT[k] if b["prix"] else None,
                        "reels": f"FR{k}", "reels_wincap": f"FRWCAP{k}"})
    pc = copy.deepcopy(p)
    pc["longueur"] = 100
    ecrire_bandes(dossier / "reels" / "PAD_BR.csv", simulateur.construire_bandes(pc, "base"), codes)
    ecrire_bandes(dossier / "reels" / "PAD_FR.csv", simulateur.construire_bandes(pc, "fs1"), codes)

    def multis(ph):
        return {str(int(x)): float(w) for x, w in zip(p["wild_val"], p["wild_w"][ph]) if w > 0}

    ex = simulateur.exact_base(p)
    loi = ex["loi"]
    seuils = [b["bn"] for b in p["bonus"]] + [len(loi)]
    scat = {str(k): {str(n): float(loi[n]) for n in range(seuils[k - 1], seuils[k]) if loi[n] > 0} for k in range(1, nb + 1)}
    joint = [[ex["freq"][k - 1] if c == k else 0.0 for k in range(1, nb + 1)] for c in range(1, nb + 1)]
    R = p["R"]
    paytable = [{"symbol": codes[i], "kind": kk, "pay": float(p["pays"][i, kk - 3])}
                for i, t in enumerate(types) if t == "PAY" for kk in range(3, R + 1) if p["pays"][i, kk - 3] > 0]
    p_achat = {k: ws[f"{'BCD'[k - 1]}{simulateur.SIM_LIGNE['a_p_max']}"].value for k in range(1, nb + 1)}
    params = {
        "_info": "Généré par exporter.py depuis le classeur. Ne pas éditer : modifie le classeur puis relance l'export.",
        "game_id": a.game_id, "provider_number": a.provider, "provider_name": a.studio, "working_name": a.nom,
        "rtp": round(p["rtp_cible"], 4), "wincap": p["max_win"], "num_reels": R, "num_rows": p["rows"],
        "paytable": paytable, "wild": codes[wi], "scatter": codes[types.index("SCATTER")],
        "retrigger": {"scatters": p["retrig_bn"], "spins": p["retrig_fs"]},
        "wild_multipliers": {"base": multis("base"), **{str(k): multis(f"fs{k}") for k in range(1, nb + 1)}},
        "bonuses": bonuses, "scatter_weights": scat,
        "targets": {
            # Pondération (ponderation.py) : probabilité du max win simulée ; probabilité exacte de chaque bonus
            # (toutes les positions des bandes) ; fréquence de gain simulée
            "wincap_rtp": 0.001,
            "base": {"hit": float(hit), "joint": joint, "p_wincap": float(p_max) if p_max else None},
            **{MODES_ACHAT[k]: {"p_wincap": float(p_achat[k]) if p_achat.get(k) else None}
               for k, b in enumerate(p["bonus"], 1) if b["prix"]},
        },
    }
    with open(dossier / "params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
    print(f"Jeu exporté dans {dossier}")
    print(f"  {R} x {p['rows']} ({p['rows'] ** R:,} ways), RTP estimé {est:.3%}, cible {p['rtp_cible']:.2%}, max win {p['max_win']:,.0f}x")
    for b in bonuses:
        achat = f"achat {b['buy_cost']:g}x (mode « {b['mode']} »)" if b["buy_cost"] else "non achetable"
        print(f"  bonus {b['id']} « {b['name']} » : {b['scatters']}+ scatters, {b['spins']} FS, wilds {b['wilds']}, {achat}")


if __name__ == "__main__":
    main()
