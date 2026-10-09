"""Actions du jeu : transformation autour du globe et évaluation des gains."""

from game_calculations import GameCalculations
from game_events import globe_multipliers_event
from src.calculations.cluster import Cluster
from src.calculations.lines import Lines
from src.calculations.ways import Ways
from src.calculations.statistics import get_random_outcome


class GameExecutables(GameCalculations):
    """Exécutables appelés par gamestate.py."""

    def apply_globes(self) -> None:
        """Chaque globe qui vient d'arriver sur la grille transforme ses 8 voisins en multiplicateurs.
        Les symboles bonus, les globes et les cases déjà multiplicateur restent en place.
        Un globe déjà activé est marqué (attribut `locked`) pour ne pas se réactiver après une cascade."""
        globes = [(r, w) for r, w in self.globe_positions() if not self.board[r][w].locked]
        if not globes:
            return
        converted = {}
        mult_values = self.get_current_distribution_conditions()["mult_values"][self.gametype]
        keep = (self.config.scatter_symbol, self.config.globe_symbol, self.config.mult_symbol)
        for reel, row in globes:
            self.board[reel][row].locked = True
        for reel, row in globes:
            for r, w in self.globe_neighbours(reel, row):
                if (r, w) in converted or self.board[r][w].name in keep:
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
        """Lignes / ways : calcule les gains de la grille, met à jour les gains, émet les événements."""
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

    def evaluate_clusters(self) -> None:
        """Clusters : multi d'un cluster = somme des multis qu'il contient (WILD_ADD), ou somme de
        tous les multis à l'écran appliquée à chaque gain (GLOBAL_SUM). Marque les cases gagnantes."""
        global_mult = 1 if self.config.wild_multis else self.board_multiplier()
        self.win_data = Cluster.get_cluster_data(self.config, self.board, global_multiplier=global_mult)
        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.emit_tumble_win_events()

    def play_board(self) -> None:
        """Une grille complète : globes, gains, puis cascades tant qu'il y a des gains."""
        self.apply_globes()
        if self.config.win_type != "cluster":
            self.evaluate_board()
            return
        self.evaluate_clusters()
        while self.config.cascades and self.win_data["totalWin"] > 0 and not self.wincap_triggered:
            self.tumble_game_board()
            self.apply_globes()
            self.evaluate_clusters()
        self.set_end_tumble_event()
