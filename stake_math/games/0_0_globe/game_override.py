"""Surcharges des fonctions génériques du SDK."""

import random

from game_executables import GameExecutables
from src.events.events import fs_trigger_event, reveal_event


class GameStateOverride(GameExecutables):
    """Multi du globe, choix du bonus (1, 2 ou 3), bandes et multis propres à chaque bonus,
    globe garanti du bonus caché, conditions de répétition."""

    def reset_book(self):
        super().reset_book()
        self.bonus = 0          # bonus en cours (0 = aucun)

    def assign_special_sym_function(self):
        self.special_symbol_functions = {self.config.globe_symbol: [self.assign_globe_multiplier]}

    def assign_globe_multiplier(self, symbol) -> None:
        symbol.assign_attribute({"multiplier": self.config.globe_multiplier})

    def get_current_distribution_conditions(self) -> dict:
        """Pendant les FS, les bandes et les multis sont ceux du bonus en cours."""
        conds = super().get_current_distribution_conditions()
        if self.gametype == self.config.freegame_type and getattr(self, "bonus", 0):
            fg = self.config.freegame_type
            conds = dict(conds)
            conds["reel_weights"] = dict(conds["reel_weights"], **{fg: conds["bonus_reels"][self.bonus]})
            conds["mult_values"] = dict(conds["mult_values"], **{fg: conds["bonus_mults"][self.bonus]})
        return conds

    def bonus_from_scatters(self, count: int) -> int:
        """Le bonus le plus fort dont le nombre de symboles bonus est atteint."""
        out = 0
        for i, b in sorted(self.config.bonuses.items()):
            if count >= b["scatters"]:
                out = i
        return out

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        """Choisit le bonus : acheté (mode bonus buy) ou selon le nombre de symboles bonus sur la grille
        finale. L'événement freeSpinTrigger porte en plus le numéro du bonus ("bonus": 1, 2 ou 3)."""
        if self.betmode in self.config.buy_modes:
            self.bonus = self.config.buy_modes[self.betmode]
        else:
            self.bonus = self.bonus_from_scatters(self.count_special_symbols(scatter_key))
        self.tot_fs = self.config.bonuses[self.bonus]["spins"]
        fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)
        self.book.events[-1]["bonus"] = self.bonus
        self.record({"kind": self.bonus, "symbol": "bonus", "gametype": self.gametype})

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter") -> None:
        """Bonus avec globe garanti : si la grille de départ d'un FS n'a pas de globe, une case au hasard
        (hors symbole bonus) devient un globe, avant le reveal."""
        garanti = (self.gametype == self.config.freegame_type and self.bonus
                   and self.config.bonuses[self.bonus].get("guaranteed_globe"))
        if not garanti:
            super().draw_board(emit_event, trigger_symbol)
            return
        super().draw_board(False, trigger_symbol)
        self.ensure_globe()
        if emit_event:
            reveal_event(self)

    def ensure_globe(self) -> None:
        if self.globe_positions():
            return
        cases = [(r, w) for r in range(self.config.num_reels) for w in range(self.config.num_rows[r])
                 if self.board[r][w].name != self.config.scatter_symbol]
        reel, row = random.choice(cases)
        self.board[reel][row] = self.create_symbol(self.config.globe_symbol)
        self.get_special_symbols_on_board()

    def check_repeat(self) -> None:
        super().check_repeat()
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                return
            # « basegame » doit produire un gain non nul (« 0 » regroupe les tours perdants)
            if self.criteria == "basegame" and self.final_win == 0:
                self.repeat = True
