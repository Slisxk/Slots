"""Surcharges du SDK : choix du bonus, bandes du bonus, multis des wilds, wilds collants (fixes ou qui
avancent d'un rouleau vers la gauche à chaque free spin), événement des symboles géants."""

from game_executables import GameExecutables
from game_events import giant_symbols_event, sticky_wilds_event
from src.calculations.statistics import get_random_outcome
from src.events.events import fs_trigger_event, reveal_event


class GameStateOverride(GameExecutables):

    def reset_book(self):
        super().reset_book()
        self.bonus = 0
        self.sticky = {}                       # {(reel, row): multi} des wilds collants

    def assign_special_sym_function(self):
        self.special_symbol_functions = {self.config.wild_symbol: [self.assign_wild_multiplier]}

    def assign_wild_multiplier(self, symbol) -> None:
        cle = "base" if self.gametype == self.config.basegame_type or not getattr(self, "bonus", 0) else str(self.bonus)
        symbol.assign_attribute({"multiplier": get_random_outcome(self.config.wild_mult[cle])})

    def get_current_distribution_conditions(self) -> dict:
        conds = super().get_current_distribution_conditions()
        if self.gametype == self.config.freegame_type and getattr(self, "bonus", 0):
            fg = self.config.freegame_type
            conds = dict(conds)
            conds["reel_weights"] = dict(conds["reel_weights"], **{fg: conds["bonus_reels"][self.bonus]})
        return conds

    def bonus_from_scatters(self, count: int) -> int:
        out = 0
        for i, b in sorted(self.config.bonuses.items()):
            if count >= b["scatters"]:
                out = i
        return out

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        if self.betmode in self.config.buy_modes:
            self.bonus = self.config.buy_modes[self.betmode]
        else:
            self.bonus = self.bonus_from_scatters(self.count_special_symbols(scatter_key))
        self.tot_fs = self.config.bonuses[self.bonus]["spins"]
        self.sticky = {}
        fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)
        self.book.events[-1]["bonus"] = self.bonus
        self.book.events[-1]["wilds"] = self.config.bonuses[self.bonus]["wilds"]
        self.record({"kind": self.bonus, "symbol": "bonus", "gametype": self.gametype})

    def mode_wilds(self) -> str:
        if self.gametype == self.config.freegame_type and self.bonus:
            return self.config.bonuses[self.bonus]["wilds"]
        return "NON"

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter") -> None:
        mode = self.mode_wilds()
        if mode == "NON":
            super().draw_board(False, trigger_symbol)
            if emit_event:
                reveal_event(self)
                giant_symbols_event(self)
            return
        moved = {}
        if mode == "MARCHE":                   # les wilds collants avancent d'un rouleau vers la gauche
            moved = {(r - 1, w): m for (r, w), m in self.sticky.items() if r - 1 >= 0}
            self.sticky = moved
        super().draw_board(False, trigger_symbol)
        new = {}
        for r in range(self.config.num_reels):
            for w in range(self.config.num_rows[r]):
                sym = self.board[r][w]
                if sym.name == self.config.wild_symbol and (r, w) not in self.sticky:
                    new[(r, w)] = sym.get_attribute("multiplier")
        for (r, w), m in self.sticky.items():   # les wilds collants recouvrent la grille
            sym = self.create_symbol(self.config.wild_symbol)
            sym.assign_attribute({"multiplier": m})
            self.board[r][w] = sym
        self.sticky.update(new)                 # les nouveaux wilds deviennent collants
        self.get_special_symbols_on_board()
        if emit_event:
            reveal_event(self)
            giant_symbols_event(self)
            sticky_wilds_event(self, new, mode)

    def check_repeat(self) -> None:
        super().check_repeat()
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                return
            if self.criteria == "basegame" and self.final_win == 0:
                self.repeat = True
