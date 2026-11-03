"""Configuration du jeu. Toutes les valeurs viennent de params.json (généré par exporter.py)."""

import json
import os

from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "params.json"), encoding="utf-8") as f:
    PARAMS = json.load(f)


def _num(k):
    v = float(k)
    return int(v) if v.is_integer() else v


class GameConfig(Config):
    """Ways avec symboles géants (blocs de 1 à 3 cases sur les bandes), wilds multiplicateurs (les multis
    se multiplient d'un rouleau à l'autre), bonus aux wilds collants fixes ou qui avancent, bonus buy."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        p = PARAMS
        self.game_id = p["game_id"]
        self.provider_number = p["provider_number"]
        self.working_name = self.game_name = p["working_name"]
        self.provider_name = p.get("provider_name", "mon_studio")
        self.wincap = float(p["wincap"])
        self.win_type = "ways"
        self.rtp = p["rtp"]
        self.construct_paths()

        self.num_reels = p["num_reels"]
        self.num_rows = [p["num_rows"]] * self.num_reels
        self.paytable = {(e["kind"], e["symbol"]): e["pay"] for e in p["paytable"]}
        self.include_padding = True
        self.wild_symbol, self.scatter_symbol = p["wild"], p["scatter"]
        self.pay_symbols = sorted({e["symbol"] for e in p["paytable"]})
        self.special_symbols = {"wild": [self.wild_symbol], "scatter": [self.scatter_symbol],
                                "multiplier": [self.wild_symbol]}

        self.bonuses = {b["id"]: b for b in p["bonuses"]}
        seuils = sorted((b["scatters"], b["id"]) for b in p["bonuses"])
        R = self.num_reels
        self.freespin_triggers = {
            self.basegame_type: {n: self.bonuses[[i for s, i in seuils if s <= n][-1]]["spins"]
                                 for n in range(seuils[0][0], R + 1)},
            self.freegame_type: {n: p["retrigger"]["spins"] for n in range(p["retrigger"]["scatters"], R + 1)},
        }
        self.anticipation_triggers = {self.basegame_type: seuils[0][0] - 1,
                                      self.freegame_type: p["retrigger"]["scatters"] - 1}

        # Multis des wilds : "base" et chaque bonus (clé = id du bonus en texte)
        self.wild_mult = {k: {_num(v): w for v, w in d.items()} for k, d in p["wild_multipliers"].items()}

        self.reels = {"BR0": self.read_reels_csv(os.path.join(self.reels_path, "BR0.csv"))}
        for b in p["bonuses"]:
            for nom in (b["reels"], b["reels_wincap"]):
                self.reels[nom] = self.read_reels_csv(os.path.join(self.reels_path, f"{nom}.csv"))
        for g, f in ((self.basegame_type, "PAD_BR.csv"), (self.freegame_type, "PAD_FR.csv")):
            path = os.path.join(self.reels_path, f)
            if os.path.exists(path):
                self.padding_reels[g] = self.read_reels_csv(path)
        # Symboles géants : début et longueur du bloc de chaque case des bandes
        self.blocks = {nom: [self._blocs(reel) for reel in strips] for nom, strips in self.reels.items()}

        bonus_reels = {i: {b["reels"]: 1} for i, b in self.bonuses.items()}
        wcap_reels = {i: {b["reels_wincap"]: 1} for i, b in self.bonuses.items()}
        scat = p["scatter_weights"]

        def conditions(scatters=None, wincap=False):
            c = {"reel_weights": {self.basegame_type: {"BR0": 1},
                                  self.freegame_type: (wcap_reels if wincap else bonus_reels)[seuils[0][1]]},
                 "bonus_reels": wcap_reels if wincap else bonus_reels,
                 "force_wincap": wincap, "force_freegame": scatters is not None}
            if scatters is not None:
                c["scatter_triggers"] = scatters
            return c

        def poids_scatters(i):
            return {int(n): w for n, w in scat[str(i)].items()} if str(i) in scat else {self.bonuses[i]["scatters"]: 1}

        quotas = {i: q for i, q in zip(sorted(self.bonuses), (0.10, 0.06, 0.04))}
        top = max(self.bonuses, key=lambda i: self.bonuses[i]["scatters"])
        dist = [Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                             conditions=conditions(poids_scatters(top), wincap=True))]
        for i in sorted(self.bonuses):
            dist.append(Distribution(criteria=f"bonus{i}", quota=quotas[i], conditions=conditions(poids_scatters(i))))
        dist += [Distribution(criteria="0", quota=0.1, win_criteria=0.0, conditions=conditions()),
                 Distribution(criteria="basegame", quota=round(0.899 - sum(quotas.values()), 4), conditions=conditions())]
        self.bet_modes = [BetMode(name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
                                  is_feature=True, is_buybonus=False, distributions=dist)]
        self.buy_modes = {}
        for i, b in sorted(self.bonuses.items()):
            if b.get("buy_cost"):
                self.buy_modes[b["mode"]] = i
                s = {b["scatters"]: 1}
                self.bet_modes.append(BetMode(
                    name=b["mode"], cost=float(b["buy_cost"]), rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=False, is_buybonus=True,
                    distributions=[Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                                                conditions=conditions(s, wincap=True)),
                                   Distribution(criteria="freegame", quota=0.999, conditions=conditions(s))]))

    @staticmethod
    def _blocs(strip):
        """Pour chaque case de la bande : (indice de début du bloc, longueur du bloc). Bande circulaire."""
        L = len(strip)
        debut, long = [0] * L, [1] * L
        i = 0
        # premier indice qui commence un bloc (la case précédente est d'un autre symbole)
        start = next((k for k in range(L) if strip[k] != strip[k - 1]), 0)
        k = 0
        while k < L:
            a = (start + k) % L
            n = 1
            while n < L and strip[(a + n) % L] == strip[a]:
                n += 1
            for j in range(n):
                debut[(a + j) % L] = a
                long[(a + j) % L] = n
            k += n
        return debut, long
