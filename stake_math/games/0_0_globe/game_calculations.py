"""Calculs propres au jeu : voisins du globe et multiplicateur de grille."""

from src.executables.executables import Executables


class GameCalculations(Executables):
    """Fonctions de calcul sans effet de bord."""

    def globe_positions(self) -> list:
        """Positions (reel, row) des globes sur la grille."""
        return [
            (reel, row)
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
            if self.board[reel][row].name == self.config.globe_symbol
        ]

    def globe_neighbours(self, reel: int, row: int) -> list:
        """Les 8 cases autour d'un globe (dans la grille), dans un ordre fixe."""
        out = []
        for d_row in (-1, 0, 1):
            for d_reel in (-1, 0, 1):
                if d_row == 0 and d_reel == 0:
                    continue
                r, w = reel + d_reel, row + d_row
                if 0 <= r < self.config.num_reels and 0 <= w < self.config.num_rows[r]:
                    out.append((r, w))
        return out

    def board_multiplier(self) -> float:
        """Mode GLOBAL_SUM : somme des multis visibles (globe compris), 1 si aucun."""
        total = 0
        for reel in self.board:
            for sym in reel:
                if sym.name in self.config.special_symbols["multiplier"] and sym.multiplier:
                    total += sym.multiplier
        return total if total > 0 else 1
