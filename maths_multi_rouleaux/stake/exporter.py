#!/usr/bin/env python3
"""
Exporte le classeur (../classeur_maths.xlsx) vers un jeu pour le math SDK de Stake Engine.

    python exporter.py ../classeur_maths.xlsx
    python exporter.py ../classeur_maths.xlsx --game-id 12_3_monjeu --nom "Mon Jeu" --studio mon_studio

Écrit dans games/<game-id>/ :
  - params.json : paytable, bonus (scatters, FS, collant, prix), multis de colonne, retrigger, cibles de pondération
  - reels/BR0.csv (jeu de base), FR1.csv, FR2.csv… (FS de chaque bonus) : poids de l'onglet Poids
    = nombre d'occurrences sur la bande ; scatters espacés (au plus 1 visible par rouleau)
  - reels/PAD_BR.csv, PAD_FR.csv : bandes courtes pour l'animation des rouleaux (front-end seulement)
Les fichiers Python du jeu sont recopiés depuis games/0_0_colonnes s'ils n'existent pas encore.
Lance d'abord simulateur.py (la fréquence de gain simulée sert à la pondération).
"""
import argparse
import json
import random
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import simulateur  # noqa: E402

MODELE = ICI / "games" / "0_0_colonnes"
FICHIERS = ["game_config.py", "game_executables.py", "game_override.py", "game_events.py", "gamestate.py",
            "ponderation.py", "run.py", "readme.txt"]
MODES_ACHAT = {1: "bonus", 2: "super", 3: "bonus3"}


def erreur(msg):
    sys.exit(f"Erreur : {msg}")


def comptes(poids, L):
    """Répartit L cases proportionnellement aux poids (plus forts restes), au moins 1 si poids > 0."""
    tot = float(sum(poids))
    brut = [w * L / tot for w in poids]
    n = [max(int(b), 1 if w > 0 else 0) for b, w in zip(brut, poids)]
    ordre = sorted(range(len(poids)), key=lambda i: brut[i] - int(brut[i]), reverse=True)
    i = 0
    while sum(n) < L:
        if poids[ordre[i % len(ordre)]] > 0:
            n[ordre[i % len(ordre)]] += 1
        i += 1
    while sum(n) > L:
        n[max(range(len(n)), key=lambda k: n[k])] -= 1
    return n


def bande(poids, codes, L, ecart, scatter, rng):
    """Bande de L cases, chaque symbole en proportion de son poids ; scatters espacés d'au moins `ecart`."""
    n = dict(zip(codes, comptes(list(poids), L)))
    nb_sc = n.pop(scatter, 0)
    reste = [c for c, k in n.items() for _ in range(k)]
    rng.shuffle(reste)
    L = len(reste) + nb_sc
    if nb_sc and L < nb_sc * ecart:
        erreur(f"trop de scatters ({nb_sc}) pour une bande de {L} cases.")
    libre = L - nb_sc * ecart
    pos = {c + i * ecart for i, c in enumerate(sorted(rng.randint(0, libre) for _ in range(nb_sc)))}
    it = iter(reste)
    return [scatter if i in pos else next(it) for i in range(L)]


def ecrire_bandes(path, bandes):
    with open(path, "w", encoding="utf-8") as f:
        for i in range(len(bandes[0])):
            f.write(",".join(b[i] for b in bandes) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classeur")
    ap.add_argument("--game-id", default="0_0_colonnes")
    ap.add_argument("--nom", default="Column Multipliers")
    ap.add_argument("--provider", type=int, default=0)
    ap.add_argument("--studio", default="mon_studio")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--longueur", type=int, default=20_000, help="longueur des bandes (cases)")
    a = ap.parse_args()

    p = simulateur.load_params(a.classeur)
    e = simulateur.analytique(p)
    from openpyxl import load_workbook
    hit = load_workbook(a.classeur)["Simulation"][simulateur.cellule("hit")].value
    if not isinstance(hit, (int, float)):
        erreur("l'onglet Simulation est vide : lance d'abord  python simulateur.py <classeur>")
    if not p["rtp_min"] <= e["rtp"] <= p["rtp_max"]:
        erreur(f"RTP exact {e['rtp']:.3%} hors de [{p['rtp_min']:.2%} ; {p['rtp_max']:.2%}] : recale le classeur.")
    R, rows, codes, types = p["R"], p["rows"], p["codes"], p["types"]
    for c in codes:
        if not str(c).isalnum():
            erreur(f"code symbole invalide « {c} » (lettres et chiffres uniquement).")
    scatter = codes[types.index("SCATTER")]
    wild = codes[types.index("WILD")] if "WILD" in types else None

    dossier = ICI / "games" / a.game_id
    (dossier / "reels").mkdir(parents=True, exist_ok=True)
    if dossier != MODELE:
        for f in FICHIERS:
            if not (dossier / f).exists():
                shutil.copy(MODELE / f, dossier / f)

    def bandes(ph, nom, L):
        rng = random.Random(f"{a.seed}-{nom}")
        w = p["poids"][ph]
        return [bande(w[:, r], codes, L, rows, scatter, rng) for r in range(R)]

    ecrire_bandes(dossier / "reels" / "BR0.csv", bandes("base", "BR0", a.longueur))
    for k in range(1, len(p["bonus"]) + 1):
        ecrire_bandes(dossier / "reels" / f"FR{k}.csv", bandes(f"fs{k}", f"FR{k}", a.longueur))
    ecrire_bandes(dossier / "reels" / "PAD_BR.csv", bandes("base", "PAD_BR", 100))
    ecrire_bandes(dossier / "reels" / "PAD_FR.csv", bandes("fs1", "PAD_FR", 100))

    def multis(ph):
        return {"act": [float(x) for x in p["multi_act"][ph]],
                "values": {str(int(v) if float(v).is_integer() else v): float(w)
                           for v, w in zip(p["multi_val"], p["multi_w"][ph]) if w > 0}}

    loi = e["loi_scatters"]
    seuils = [b["bn"] for b in p["bonus"]] + [len(loi)]
    bonuses, scat = [], {}
    for k, b in enumerate(p["bonus"], 1):
        bonuses.append({"id": k, "name": b["nom"], "scatters": b["bn"], "spins": b["fs"], "sticky": b["collant"],
                        "buy_cost": b["prix"], "mode": MODES_ACHAT[k] if b["prix"] else None,
                        "reels": f"FR{k}", "column_multipliers": multis(f"fs{k}")})
        scat[str(k)] = {str(n): float(loi[n]) for n in range(seuils[k - 1], seuils[k]) if loi[n] > 0}
    nb = len(p["bonus"])
    joint = [[e[f"bonus{k}"]["freq"] if c == k else 0.0 for k in range(1, nb + 1)] for c in range(1, nb + 1)]
    paytable = [{"symbol": codes[i], "kind": k, "pay": float(p["pays"][i, k - 3])}
                for i, t in enumerate(types) if t == "PAY" for k in range(3, R + 1) if p["pays"][i, k - 3] > 0]
    params = {
        "_info": "Généré par exporter.py depuis le classeur. Ne pas éditer : modifie le classeur puis relance l'export.",
        "game_id": a.game_id, "provider_number": a.provider, "provider_name": a.studio, "working_name": a.nom,
        "rtp": round(p["rtp_cible"], 4), "wincap": p["max_win"], "num_reels": R, "num_rows": rows,
        "paytable": paytable, "wild": wild, "scatter": scatter,
        "retrigger": {"scatters": p["retrig_bn"], "spins": p["retrig_fs"]},
        "column_multipliers": {"base": multis("base")},
        "bonuses": bonuses,
        "scatter_weights": scat,
        "targets": {
            # Pondération (ponderation.py) : max win = 0,1 % du RTP ; probabilité exacte de chaque bonus
            # (calcul exact du classeur) ; fréquence de gain simulée
            "wincap_rtp": 0.001,
            "base": {"hit": float(hit), "joint": joint},
        },
        "exact": {"rtp": e["rtp"], "spins": e["spins"],
                  **{f"bonus{k}": {"freq": e[f"bonus{k}"]["freq"], "gain": e[f"bonus{k}"]["gain"]} for k in range(1, nb + 1)}},
    }
    with open(dossier / "params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
    print(f"Jeu exporté dans {dossier}")
    print(f"  {R} x {rows} ({rows ** R:,} ways), RTP exact {e['rtp']:.3%}, cible {p['rtp_cible']:.2%}, max win {p['max_win']:,.0f}x")
    for b in bonuses:
        achat = f"achat {b['buy_cost']:g}x (mode « {b['mode']} »)" if b["buy_cost"] else "non achetable"
        print(f"  bonus {b['id']} « {b['name']} » : {b['scatters']}+ scatters, {b['spins']} FS, "
              f"{'collant' if b['sticky'] else 'non collant'}, {achat}")


if __name__ == "__main__":
    main()
