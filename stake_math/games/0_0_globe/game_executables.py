"""Actions du jeu : transformation autour du globe et évaluation des gains."""

from game_calculations import GameCalculations
from game_events import globe_multipliers_event
from src.calculations.lines import Lines
from src.calculations.ways import Ways
from src.calculations.statistics import get_random_outcome


class GameExecutables(GameCalculations):
    """Exécutables appelés par gamestate.py."""

    def apply_globes(self) -> None:
        """Chaque globe transforme ses 8 voisins en multiplicateurs.
        Les trophées et les autres globes restent en place. Une case voisine de deux globes
        ne reçoit qu'un seul multiplicateur."""
        globes = self.globe_positions()
        if not globes:
            return
        converted = {}
        mult_values = self.get_current_distribution_conditions()["mult_values"][self.gametype]
        for reel, row in globes:
            for r, w in self.globe_neighbours(reel, row):
                if (r, w) in converted:
                    continue
                if self.board[r][w].name in (self.config.scatter_symbol, self.config.globe_symbol):
                    continue
                value = get_random_outcome(mult_values)
                sym = self.create_symbol(self.config.mult_symbol)
                sym.assign_attribute({"multiplier": value})
                self.board[r][w] = sym
                converted[(r, w)] = value
        self.get_special_symbols_on_board()
        board_mult = self.board_multiplier() if not self.config.wild_multis else None
        globe_multipliers_event(self, globes, converted, board_mult)

    def evaluate_board(self) -> None:
        """Calcule les gains de la grille (lignes ou ways), met à jour les gains, émet les événements."""
        if self.config.wild_multis:
            strategy, global_mult = "symbol", 1
        else:
            strategy, global_mult = "global", self.board_multiplier()

        if self.config.win_type == "lines":
            # Lignes : les multis > 1 des wilds d'une ligne s'additionnent (WILD_ADD)
            self.win_data = Lines.get_lines(
                self.board, self.config, multiplier_method=strategy, global_multiplier=global_mult
            )
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Lines.emit_linewin_events(self)
        else:
            # Ways : les multis des wilds se multiplient d'un rouleau à l'autre (WILD_MULT)
            self.win_data = Ways.get_ways_data(
                self.config, self.board, global_multiplier=global_mult, multiplier_strategy=strategy
            )
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Ways.emit_wayswin_events(self)
