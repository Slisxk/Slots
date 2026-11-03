"""Événements propres au jeu (lignes décalées de +1 à cause du padding, comme les événements du SDK)."""

GIANT_SYMBOLS = "giantSymbols"
STICKY_WILDS = "stickyWilds"


def giant_symbols_event(gamestate) -> None:
    """Symboles géants visibles : blocs de 2 ou 3 cases d'un même symbole payant sur un rouleau.
    row = ligne du haut du bloc (peut être 0 ou moins si le bloc commence au-dessus de l'écran), height = hauteur."""
    cfg = gamestate.config
    blocs = []
    strips = cfg.reels[gamestate.reelstrip_id]
    for r in range(cfg.num_reels):
        debut, long = cfg.blocks[gamestate.reelstrip_id][r]
        L = len(strips[r])
        vus = set()
        for w in range(cfg.num_rows[r]):
            i = (gamestate.reel_positions[r] + w) % L
            if long[i] < 2 or debut[i] in vus or strips[r][i] not in cfg.pay_symbols:
                continue
            vus.add(debut[i])
            haut = w - ((i - debut[i]) % L)
            blocs.append({"reel": r, "row": haut + 1, "height": long[i], "symbol": strips[r][i]})
    if blocs:
        gamestate.book.add_event({"index": len(gamestate.book.events), "type": GIANT_SYMBOLS, "blocks": blocs})


def sticky_wilds_event(gamestate, new: dict, mode: str) -> None:
    """Wilds collants après le reveal : tous ceux de la grille, avec "new": true pour ceux qui viennent de tomber.
    mode = "FIXE" (ils restent en place) ou "MARCHE" (ils ont avancé d'un rouleau vers la gauche)."""
    if not gamestate.sticky:
        return
    gamestate.book.add_event({
        "index": len(gamestate.book.events), "type": STICKY_WILDS, "mode": mode,
        "wilds": [{"reel": r, "row": w + 1, "multiplier": m, "new": (r, w) in new}
                  for (r, w), m in sorted(gamestate.sticky.items())],
    })
