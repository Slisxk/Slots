#!/usr/bin/env python3
"""
Génère classeur_maths.xlsx : modèle de maths réutilisable « ways + multis de colonne ».

    python generer_classeur.py                       # écrit classeur_maths.xlsx
    python generer_classeur.py autre.xlsx            # autre nom
    python generer_classeur.py autre.xlsx "ACT_FS=(0.30,0.25)"   # surcharge rapide d'une valeur

Le classeur calcule le RTP EXACT en formules (jeu de base, chaque bonus, multis collants ou non) :
il se met à jour dès qu'on change une cellule. simulateur.py vérifie ces formules par simulation,
mesure la volatilité, le max win et les limites « 3 étoiles », et écrit l'onglet Simulation.
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import simulateur as SIMU  # noqa: E402  (disposition de l'onglet Simulation)

OUT = sys.argv[1] if len(sys.argv) > 1 and "=" not in sys.argv[1] else str(ICI / "classeur_maths.xlsx")

# ============================================================================ valeurs par défaut
NB_ROULEAUX, NB_LIGNES = 5, 3
RMAX = 6                                   # le classeur gère jusqu'à 6 rouleaux
SYMBOLES = [  # code, nom, type, 3, 4, 5, 6 identiques (x mise totale, par way)
    ("H1", "Premium 1", "PAY", 2.0, 5.5, 18.0, 36.0),
    ("H2", "Premium 2", "PAY", 1.4, 3.7, 13.0, 26.0),
    ("H3", "Premium 3", "PAY", 1.1, 2.8, 8.3, 16.0),
    ("H4", "Premium 4", "PAY", 0.9, 2.3, 5.5, 11.0),
    ("L1", "Bas 1 (A)", "PAY", 0.55, 1.5, 3.0, 6.0),
    ("L2", "Bas 2 (K)", "PAY", 0.45, 1.1, 2.2, 4.5),
    ("L3", "Bas 3 (Q)", "PAY", 0.4, 0.9, 1.8, 3.6),
    ("L4", "Bas 4 (J)", "PAY", 0.35, 0.75, 1.5, 3.0),
    ("L5", "Bas 5 (10)", "PAY", 0.3, 0.7, 1.5, 3.0),
    ("W", "Wild", "WILD", 0, 0, 0, 0),
    ("S", "Scatter", "SCATTER", 0, 0, 0, 0),
]
PAYANTS = [40, 50, 60, 70, 110, 120, 130, 140, 150]
W_BASE, S_BASE = 8, 21                     # peu de wilds en jeu de base (fréquence de gain ≈ 30 %)
W_FS, S_FS = 40, 28                        # plus de wilds en free spins, scatters pour les retriggers
BONUS = [  # nom, scatters, FS, multis collants, prix d'achat (vide = non achetable)
    ("Free spins", 3, 10, "NON", 101),
    ("Super free spins", 4, 10, "OUI", None),
    (None, None, None, None, None),
]
MULTI_VALEURS = [2, 3, 4, 5, 10, 20, 50, 100, 250, 500]
MULTI_POIDS = {  # poids de chaque valeur : jeu de base, bonus 1, bonus 2, bonus 3
    "base": [400, 250, 150, 100, 60, 25, 10, 4, 1, 0],
    "fs1": [300, 220, 160, 130, 110, 70, 30, 10, 2, 0.5],
    "fs2": [300, 200, 150, 120, 100, 60, 30, 15, 5, 2],
    "fs3": [300, 200, 150, 120, 100, 60, 30, 15, 5, 2],
}
ACT_BASE = 0.015                           # probabilité qu'une colonne reçoive un multi, par spin
ACT_FS = (0.31, 0.25, 0.25)                # bonus 1 (non collant), 2 (collant), 3
RETRIG_SCATTERS, RETRIG_FS = 3, 5
RTP_CIBLE, RTP_MIN, RTP_MAX = 0.962, 0.96, 0.965
MAX_WIN = 10_000
T_SURVIE, R_SURVIE = 60, 60                # table de survie des FS (spins x FS restants)

for k, v in [a.split("=", 1) for a in sys.argv[1:] if "=" in a]:   # surcharges rapides
    exec(f"{k} = {v}")

N = len(SYMBOLES)
I_W = [s[2] for s in SYMBOLES].index("WILD")
I_S = [s[2] for s in SYMBOLES].index("SCATTER")
PAY = [i for i, s in enumerate(SYMBOLES) if s[2] == "PAY"]
PHASES = ["base", "fs1", "fs2", "fs3"]

# ============================================================================ styles
F = "Arial"
f_norm, f_bold = Font(name=F, size=10), Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=14, bold=True, color="1F3B57")
f_sub = Font(name=F, size=11, bold=True, color="1F3B57")
f_in = Font(name=F, size=10, color="0000FF")
f_link = Font(name=F, size=10, color="008000")
f_note = Font(name=F, size=9, italic=True, color="666666")
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
fill_in = PatternFill("solid", fgColor="FFF2CC")
fill_head = PatternFill("solid", fgColor="1F3B57")
fill_tot = PatternFill("solid", fgColor="E7EEF5")
fill_key = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center")
PCT, PCT4, NUM, X2, DEC = "0.00%", "0.0000%", "#,##0", '0.00"x"', "0.0000"

wb = Workbook()


def put(ws, ref, v, font=f_norm, fmt=None, fill=None, align=None, border=True):
    c = ws[ref]
    c.value = v
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = box
    return c


def inp(ws, ref, v, fmt=None):
    return put(ws, ref, v, f_in, fmt, fill_in)


def header(ws, row, col0, labels):
    for i, lbl in enumerate(labels):
        put(ws, f"{L(col0 + i)}{row}", lbl, f_head, fill=fill_head, align=center)


def title(ws, text, sub=None):
    ws["A1"].value, ws["A1"].font = text, f_title
    if sub:
        ws["A2"].value, ws["A2"].font = sub, f_note


def name(n, ref):
    wb.defined_names[n] = DefinedName(n, attr_text=ref)


def widths(ws, d):
    for k, v in d.items():
        ws.column_dimensions[k].width = v


def note(ws, ref, txt):
    put(ws, ref, txt, f_note, border=False)


# ============================================================================ LISEZ-MOI
ws = wb.active
ws.title = "LISEZ-MOI"
title(ws, "Modèle de maths : ways + multis de colonne (x2 à x500), bonus collant ou non")
TXT = [
    ("Le principe", f_sub),
    ("• Grille NB_ROULEAUX x NB_LIGNES (5 x 3 = 243 ways par défaut). Gains en ways de gauche à droite : un symbole sur les rouleaux 1, 2, 3… consécutifs. Wild (pas sur le rouleau 1) et scatter (au plus 1 par rouleau).", None),
    ("• MULTI DE COLONNE : à chaque spin, chaque rouleau peut recevoir un multi (x2 à x500) qui couvre toute la colonne, de haut en bas. Une way est multipliée par la SOMME des multis des colonnes qu'elle traverse (x1 s'il n'y en a aucun), comme les multis additionnés de Gates of Olympus.", None),
    ("• BONUS : 3 scatters = bonus 1, 4 scatters = bonus 2… (table dans Config). Chaque bonus a ses poids, ses multis et son mode : NON collant (les multis disparaissent après chaque spin) ou COLLANT (un multi reste sur sa colonne jusqu'à la fin du bonus, et chaque nouveau multi sur cette colonne s'ajoute à sa valeur).", None),
    ("• Retrigger : RETRIG_SCATTERS scatters ou plus pendant les FS = +RETRIG_FS free spins.", None),
    ("", None),
    ("Pourquoi ce modèle est « équilibré »", f_sub),
    ("• Le RTP est calculé EXACTEMENT en formules (onglets Calc_*) : chaque composante (spins, chaque bonus) est visible dans le Résumé avec sa part du RTP.", None),
    ("• L'onglet Contrôles vérifie les règles d'approbation Stake Engine (RTP, écart entre modes, fréquence de gain 1/3 à 1/8, max win atteignable) et les règles d'équilibre : les spins rapportent 55 à 70 % du RTP, aucun bonus ne dépasse 35 %.", None),
    ("• Méthode et seuils repris du repo « Slot & Casino Game Developer Skills for Stake Engine » (senior-game-math-engineer, rtp-optimizer, stake-game-developer).", None),
    ("", None),
    ("Comment l'utiliser", f_sub),
    ("1. Modifie uniquement les cellules BLEUES sur fond jaune : Config, Paytable, Poids, Multis. Le Résumé et les Contrôles se recalculent tout de suite.", None),
    ("2. Quand le RTP exact est entre RTP_MIN et RTP_MAX et que les Contrôles sont OK, lance la simulation : python simulateur.py classeur_maths.xlsx", None),
    ("   Elle vérifie les formules, mesure la volatilité, la fréquence du max win et les limites « 3 étoiles » du SDK, puis écrit l'onglet Simulation et rapport_validation.md.", None),
    ("3. Exporte vers le math SDK de Stake Engine : dossier stake/ (voir README.md).", None),
    ("Pour une autre slot : change la grille (3 à 6 rouleaux, 2 à 6 lignes), les symboles, la paytable, les poids, les multis et les bonus. Garde le même ordre de symboles dans Paytable et dans les blocs de Poids.", None),
    ("", None),
    ("Code couleur", f_sub),
    ("Bleu sur fond jaune = saisie · Noir = formule · Vert = lien vers un autre onglet · Fond jaune vif = résultat clé", None),
]
for i, (t, fnt) in enumerate(TXT):
    c = ws.cell(row=3 + i, column=1, value=t)
    c.font = fnt or f_norm
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 150

# ============================================================================ Config
ws = wb.create_sheet("Config")
title(ws, "Paramètres généraux", "Cellules bleues sur fond jaune = à modifier.")
header(ws, 4, 1, ["Paramètre", "Valeur", "Notes"])
cfg = [
    ("NB_ROULEAUX", "Nombre de rouleaux", NB_ROULEAUX, NUM, "3 à 6."),
    ("NB_LIGNES", "Nombre de lignes (hauteur)", NB_LIGNES, NUM, "2 à 6. Plus de lignes = plus de ways = gains plus fréquents."),
    ("NB_WAYS", "Nombre de ways", "=NB_LIGNES^NB_ROULEAUX", NUM, "Calculé."),
    ("RTP_CIBLE", "RTP visé", RTP_CIBLE, PCT, "Le SDK règle le RTP final exactement sur cette valeur (pondération)."),
    ("RTP_MIN", "RTP minimum accepté", RTP_MIN, PCT, "Ta règle : 96 % minimum."),
    ("RTP_MAX", "RTP maximum accepté", RTP_MAX, PCT, "Ta règle : 96,5 % maximum."),
    ("MAX_WIN", "Max win (x mise)", MAX_WIN, NUM, "Plafond d'un tour. Doit être atteignable au moins 1 fois sur 20 000 000 (règle Stake)."),
    ("RETRIG_SCATTERS", "Scatters pour un retrigger en FS", RETRIG_SCATTERS, NUM, ""),
    ("RETRIG_FS", "FS ajoutés par un retrigger", RETRIG_FS, NUM, ""),
    ("PART_SPINS_MIN", "Équilibre : part minimum des spins", 0.55, PCT, "Les spins doivent rapporter : sinon le jeu « ne donne rien » hors bonus."),
    ("PART_SPINS_MAX", "Équilibre : part maximum des spins", 0.70, PCT, "Au-delà, les bonus deviennent trop faibles."),
    ("PART_BONUS_MAX", "Équilibre : part maximum d'un bonus", 0.35, PCT, "Aucun bonus ne doit « tout donner »."),
    ("HIT_MIN", "Fréquence de gain minimum", 1 / 8, PCT, "Règle d'approbation : 1 tour gagnant sur 3 à 8."),
    ("HIT_MAX", "Fréquence de gain maximum", 1 / 3, PCT, ""),
    ("SIM_SPINS", "Spins de base simulés", 2_000_000, NUM, "Le repo conseille ≥ 1 000 000 pour caler et ≥ 20 000 000 pour valider."),
    ("SIM_BUY", "Tours simulés par bonus (comme un achat)", 100_000, NUM, ""),
    ("SIM_SEED", "Graine aléatoire", 2026, NUM, "Même graine = mêmes résultats (reproductibilité)."),
]
for i, (nm, lbl, v, fmt, nt) in enumerate(cfg):
    r = 5 + i
    put(ws, f"A{r}", lbl)
    if isinstance(v, str) and v.startswith("="):
        put(ws, f"B{r}", v, f_norm, fmt)
    else:
        inp(ws, f"B{r}", v, fmt)
    note(ws, f"C{r}", nt)
    name(nm, f"Config!$B${r}")
r0 = 5 + len(cfg) + 2
put(ws, f"A{r0}", "Les bonus", f_sub, border=False)
header(ws, r0 + 1, 1, ["Nom du bonus (libre)", "Scatters", "FS donnés", "Multis collants", "Prix d'achat (x mise)", "Notes"])
BONUS_R0 = r0 + 2
notes_b = ["Multis non collants : ils disparaissent après chaque spin.",
           "Multis collants : ils restent et s'additionnent jusqu'à la fin du bonus. Prix vide = non achetable.",
           "Optionnel : laisse la ligne vide pour 2 bonus seulement."]
for i, row in enumerate(BONUS):
    r = BONUS_R0 + i
    for col, v, fmt in zip("ABCDE", row, (None, NUM, NUM, None, NUM)):
        inp(ws, f"{col}{r}", v, fmt)
    note(ws, f"F{r}", notes_b[i])
name("BONUS", f"Config!$A${BONUS_R0}:$E${BONUS_R0 + 2}")
dv = DataValidation(type="list", formula1='"OUI,NON"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"D{BONUS_R0}:D{BONUS_R0 + 2}")
note(ws, f"A{BONUS_R0 + 3}", "Le bonus déclenché est le plus fort dont le nombre de scatters est atteint. Scatters croissants, au plus NB_ROULEAUX (1 scatter max par rouleau).")
widths(ws, {"A": 42, "B": 16, "C": 14, "D": 16, "E": 18, "F": 80})
B_ACTIF = [f"ISNUMBER(Config!$B${BONUS_R0 + k})" for k in range(3)]

# ============================================================================ Paytable
ws = wb.create_sheet("Paytable")
title(ws, "Paytable (x mise totale, par way)", "Types : PAY = payant · WILD = remplace les payants (pas sur le rouleau 1) · SCATTER = déclenche les bonus.")
header(ws, 3, 1, ["Code", "Symbole", "Type", "3 identiques", "4 identiques", "5 identiques", "6 identiques"])
PT0 = 4
for i, s in enumerate(SYMBOLES):
    r = PT0 + i
    for col, v in zip("ABC", s[:3]):
        inp(ws, f"{col}{r}", v)
    for col, v in zip("DEFG", s[3:]):
        (inp if s[2] == "PAY" else lambda w, ref, v, fmt: put(w, ref, v, f_norm, fmt))(ws, f"{col}{r}", v, X2)
name("SYMBOLES", f"Paytable!$A${PT0}:$G${PT0 + N - 1}")
dvt = DataValidation(type="list", formula1='"PAY,WILD,SCATTER"')
ws.add_data_validation(dvt)
dvt.add(f"C{PT0}:C{PT0 + N - 1}")
note(ws, f"A{PT0 + N + 1}", "Gain d'une way = valeur ci-dessus x multi de la way. Exemple : 3 ways de H1 sur 5 rouleaux = 3 x 20 = 60x la mise. La colonne « 6 identiques » ne sert qu'avec 6 rouleaux.")
widths(ws, {"A": 8, "B": 16, "C": 10, "D": 13, "E": 13, "F": 13, "G": 13})

# ============================================================================ Poids
ws = wb.create_sheet("Poids")
title(ws, "Poids des symboles par rouleau", "Probabilité d'une case = poids / total du rouleau. Les colonnes au-delà de NB_ROULEAUX sont ignorées.")
BLOC = {}
LBL = {"base": "JEU DE BASE", "fs1": "FREE SPINS DU BONUS 1", "fs2": "FREE SPINS DU BONUS 2", "fs3": "FREE SPINS DU BONUS 3"}
for b_i, ph in enumerate(PHASES):
    t0 = 3 + b_i * (N + 5)
    put(ws, f"A{t0}", LBL[ph], f_sub, border=False)
    header(ws, t0 + 1, 1, ["Code", "Symbole"] + [f"R{k}" for k in range(1, RMAX + 1)] + [""] + [f"P(R{k})" for k in range(1, RMAX + 1)])
    first = t0 + 2
    wv = W_BASE if ph == "base" else W_FS
    sv = S_BASE if ph == "base" else S_FS
    for i in range(N):
        r = first + i
        put(ws, f"A{r}", f"=Paytable!A{PT0 + i}", f_link)
        put(ws, f"B{r}", f"=Paytable!B{PT0 + i}", f_link)
        for k in range(RMAX):
            v = PAYANTS[i] if i in PAY else (wv if i == I_W else sv)
            if i == I_W and k == 0:
                v = 0
            inp(ws, f"{L(3 + k)}{r}", v, NUM)
            tc = f"{L(3 + k)}${first + N}"
            put(ws, f"{L(10 + k)}{r}", f"=IF({tc}=0,0,{L(3 + k)}{r}/{tc})", f_norm, PCT)
    t = first + N
    put(ws, f"B{t}", "Total", f_bold, fill=fill_tot)
    for k in range(RMAX):
        put(ws, f"{L(3 + k)}{t}", f"=SUM({L(3 + k)}{first}:{L(3 + k)}{t - 1})", f_bold, NUM, fill_tot)
    name(f"POIDS_{ph.upper()}", f"Poids!$A${first}:$H${t - 1}")
    BLOC[ph] = first
widths(ws, {"A": 8, "B": 14, **{L(c): 8 for c in range(3, 9)}, "I": 2, **{L(c): 9 for c in range(10, 16)}})

# ============================================================================ Multis
ws = wb.create_sheet("Multis")
title(ws, "Multis de colonne (x2 à x500)", "Un multi couvre toute la colonne. Une way prend la somme des multis des colonnes qu'elle traverse.")
put(ws, "A3", "Valeurs et poids", f_sub, border=False)
noms_ph = ["Jeu de base", "Bonus 1", "Bonus 2", "Bonus 3"]
header(ws, 4, 1, ["Valeur"] + [f"Poids {n}" for n in noms_ph] + [f"P {n}" for n in noms_ph])
M0 = 5
M1 = M0 + len(MULTI_VALEURS) - 1
for i, v in enumerate(MULTI_VALEURS):
    r = M0 + i
    inp(ws, f"A{r}", v, X2)
    for j, ph in enumerate(PHASES):
        cw, cp = L(2 + j), L(6 + j)
        inp(ws, f"{cw}{r}", MULTI_POIDS[ph][i], "0.0")
        put(ws, f"{cp}{r}", f"=IF(${cw}${M1 + 1}=0,0,{cw}{r}/${cw}${M1 + 1})", f_norm, "0.000%")
put(ws, f"A{M1 + 1}", "Total", f_bold, fill=fill_tot)
put(ws, f"A{M1 + 2}", "Multi moyen E[V]", f_bold, fill=fill_tot)
EV = {}
for j, ph in enumerate(PHASES):
    cw, cp = L(2 + j), L(6 + j)
    put(ws, f"{cw}{M1 + 1}", f"=SUM({cw}{M0}:{cw}{M1})", f_bold, "0.0", fill_tot)
    put(ws, f"{cp}{M1 + 2}", f"=SUMPRODUCT($A${M0}:$A${M1},{cp}{M0}:{cp}{M1})", f_bold, X2, fill_key)
    EV[ph] = f"Multis!${cp}${M1 + 2}"
name("MULTI_VALEURS", f"Multis!$A${M0}:$E${M1}")
A0 = M1 + 5
put(ws, f"A{A0 - 1}", "Probabilité qu'une colonne reçoive un multi, par spin", f_sub, border=False)
header(ws, A0, 1, ["Phase"] + [f"R{k}" for k in range(1, RMAX + 1)] + ["Spins avec au moins 1 multi"])
ACT = {}
for j, ph in enumerate(PHASES):
    r = A0 + 1 + j
    put(ws, f"A{r}", noms_ph[j], f_bold)
    a = ACT_BASE if ph == "base" else ACT_FS[j - 1]
    for k in range(RMAX):
        inp(ws, f"{L(2 + k)}{r}", a, PCT)
    put(ws, f"H{r}", "=1-" + "*".join(f"IF({k + 1}<=NB_ROULEAUX,1-{L(2 + k)}{r},1)" for k in range(RMAX)), f_norm, PCT)
    ACT[ph] = r
name("MULTI_ACTIVATION", f"Multis!$B${A0 + 1}:$G${A0 + 4}")
note(ws, f"A{A0 + 6}", "Le jeu de base garde des multis rares (envie de spinner sans trop donner). En bonus, les multis sont fréquents ; "
     "dans un bonus collant, mets une probabilité plus faible ou des valeurs plus petites : les multis s'accumulent.")
note(ws, f"A{A0 + 7}", "Bonus collant : au spin t, une colonne vaut la somme de tous les multis tombés dessus depuis le début du bonus.")
widths(ws, {"A": 26, **{L(c): 13 for c in range(2, 10)}})


# ============================================================================ Calc (une feuille par phase)
def bloc_scatters(ws, row0, ph, titre):
    """Loi du nombre de scatters sur la grille (au plus 1 par rouleau). Renvoie (ligne n=0, colonne finale)."""
    put(ws, f"A{row0}", titre, f_sub, border=False)
    header(ws, row0 + 1, 1, ["n"] + [f"jusqu'à R{k}" for k in range(1, RMAX + 1)])
    p0 = row0 + 2
    pS = BLOC[ph] + I_S
    for n in range(RMAX + 1):
        r = p0 + n
        put(ws, f"A{r}", n, f_bold, NUM)
        for k in range(RMAX):
            col = L(2 + k)
            q = f"IF({k + 1}<=NB_ROULEAUX,MIN(1,NB_LIGNES*Poids!{L(10 + k)}${pS}),0)"
            if k == 0:
                f = f"=IF($A{r}=0,1-{q},IF($A{r}=1,{q},0))"
            else:
                prev = L(1 + k)
                f = f"={prev}{r}*(1-{q})" + (f"+{prev}{r - 1}*{q}" if n > 0 else "")
            put(ws, f"{col}{r}", f, f_norm, PCT4)
    return p0, L(1 + RMAX)


def calc_sheet(ph, k_bonus=None):
    nom = "Calc_Spins" if ph == "base" else f"Calc_Bonus{k_bonus}"
    ws = wb.create_sheet(nom)
    sub = ("Gain moyen d'un spin du jeu de base, multis de colonne compris (calcul exact)." if ph == "base" else
           f"Gain moyen du bonus {k_bonus} : free spins, multis (collants ou non) et retriggers (calcul exact, avant plafond du max win).")
    title(ws, f"{'Spins du jeu de base' if ph == 'base' else f'Bonus {k_bonus}'} — calcul exact", sub)
    first = BLOC[ph]
    pW = f"Poids!{{c}}${first + I_W}"
    pS = f"Poids!{{c}}${first + I_S}"
    # ---- facteurs de multi par longueur de way
    put(ws, "A4", "Multi moyen d'une way de longueur k", f_sub, border=False)
    header(ws, 5, 1, ["", "k = 3", "k = 4", "k = 5", "k = 6"])
    ar = ACT[ph]
    acts = [f"IF({k + 1}<=NB_ROULEAUX,Multis!{L(2 + k)}${ar},0)" for k in range(RMAX)]
    put(ws, "A6", "P(aucun multi sur les k colonnes)", f_norm)
    put(ws, "A7", "Somme des probabilités d'activation", f_norm)
    put(ws, "A8", "Multi moyen par spin (non collant)", f_bold)
    for j, k in enumerate(range(3, 7)):
        col = L(2 + j)
        put(ws, f"{col}6", "=" + "*".join(f"(1-{acts[r]})" for r in range(k)), f_norm, DEC)
        put(ws, f"{col}7", "=" + "+".join(acts[r] for r in range(k)), f_norm, DEC)
        put(ws, f"{col}8", f"={col}6+{col}7*{EV[ph]}", f_bold, DEC)
    # ---- par symbole : E[symboles comptés], P(aucun), gains par longueur
    R0 = 11
    put(ws, f"A{R0 - 1}", "Par symbole : E[nb de cases qui comptent (symbole + wild)] et P(aucune) sur chaque rouleau", f_sub, border=False)
    header(ws, R0, 1, ["Code"] + [f"E R{k}" for k in range(1, RMAX + 1)] + [f"P0 R{k}" for k in range(1, RMAX + 1)]
           + ["Ways k=3", "Ways k=4", "Ways k=5", "Ways k=6", "Gain moyen", "% du total"])
    rows_sym = []
    for j, s in enumerate(PAY):
        r = R0 + 1 + j
        rows_sym.append(r)
        ps = first + s
        put(ws, f"A{r}", f"=Paytable!A{PT0 + s}", f_link)
        for k in range(RMAX):
            c = L(10 + k)
            p_s = f"(Poids!{c}${ps}+{pW.format(c=c)})"
            put(ws, f"{L(2 + k)}{r}", f"=NB_LIGNES*{p_s}", f_norm, DEC)
            Q = f"NB_LIGNES*{pS.format(c=c)}"
            q = f"({p_s}/(1-{pS.format(c=c)}))"
            put(ws, f"{L(8 + k)}{r}", f"=(1-{Q})*(1-{q})^NB_LIGNES+{Q}*(1-{q})^(NB_LIGNES-1)", f_norm, DEC)
        for j2, k in enumerate(range(3, 7)):
            prod = "*".join(f"{L(2 + rr)}{r}" for rr in range(k))
            p0n = f"IF({k}<NB_ROULEAUX,{L(8 + k)}{r},1)" if k < RMAX else "1"
            put(ws, f"{L(14 + j2)}{r}", f"=IF({k}>NB_ROULEAUX,0,{prod}*{p0n})", f_norm, DEC)
    # ---- gain moyen (facteur de multi : ligne G)
    rG = R0 + len(PAY) + 4
    if ph == "base":
        G = [f"$B$8", f"$C$8", f"$D$8", f"$E$8"]
        lblG = "Facteur appliqué = multi moyen par spin (ligne 8)."
    else:
        G = [f"$B${rG}", f"$C${rG}", f"$D${rG}", f"$E${rG}"]
        lblG = "Facteur appliqué au bonus = somme sur ses spins du multi moyen (ligne ci-dessous)."
    for j, s in enumerate(PAY):
        r = rows_sym[j]
        terms = "+".join(f"Paytable!{L(4 + j2)}{PT0 + s}*{L(14 + j2)}{r}*{G[j2]}" for j2 in range(4))
        put(ws, f"S{r}", f"={terms}", f_bold, DEC)
    rt = R0 + len(PAY) + 1
    put(ws, f"A{rt}", "Total", f_bold, fill=fill_tot)
    put(ws, f"S{rt}", f"=SUM(S{R0 + 1}:S{rt - 1})", f_bold, X2 if ph != "base" else PCT, fill_key)
    for j in range(len(PAY)):
        r = rows_sym[j]
        put(ws, f"T{r}", f"=IF($S${rt}=0,0,S{r}/$S${rt})", f_norm, PCT)
    note(ws, f"A{rt + 1}", lblG)
    out = {"total": f"{nom}!$S${rt}"}
    if ph != "base":
        # ---- survie des FS (retriggers) : D[t][r] = P(r FS restants après t spins)
        p0, colf = bloc_scatters(ws, rG + 4, ph, "Scatters sur la grille pendant les FS (pour les retriggers)")
        rp = p0 + RMAX + 1
        put(ws, f"A{rp}", "P(retrigger) par FS", f_bold)
        put(ws, f"B{rp}", f"=SUMPRODUCT(--($A${p0}:$A${p0 + RMAX}>=RETRIG_SCATTERS),{colf}{p0}:{colf}{p0 + RMAX})", f_bold, PCT4)
        P_RE = f"$B${rp}"
        s0 = rp + 3
        put(ws, f"A{s0 - 1}", "Survie des free spins : chaque ligne t donne la loi du nombre de FS restants après t spins", f_sub, border=False)
        header(ws, s0, 1, ["t", "Spin t joué ?", "multi moyen k=3", "k=4", "k=5", "k=6"] + [f"r={x}" for x in range(R_SURVIE + 1)])
        c_r0 = 7                                   # colonne de r = 0
        bk = BONUS_R0 + k_bonus - 1
        for t in range(T_SURVIE + 1):
            r = s0 + 1 + t
            put(ws, f"A{r}", t, f_bold, NUM)
            for x in range(R_SURVIE + 1):
                col = L(c_r0 + x)
                if t == 0:
                    f = f"=IF({x}=MIN(Config!$C${bk},{R_SURVIE}),1,0)"
                else:
                    up = r - 1
                    keep = f"{L(c_r0)}{up}" if x == 0 else "0"
                    dec = f"{L(c_r0 + x + 1)}{up}*(1-{P_RE})" if x + 1 <= R_SURVIE else "0"
                    re_ = (f"IF({x}+1-RETRIG_FS>=1,INDEX(${L(c_r0)}{up}:${L(c_r0 + R_SURVIE)}{up},1,{x}+2-RETRIG_FS)*{P_RE},0)")
                    f = f"={keep}+{dec}+{re_}"
                put(ws, f"{col}{r}", f, f_norm, "0.0000")
            if t >= 1:
                put(ws, f"B{r}", f"=1-{L(c_r0)}{r - 1}", f_norm, DEC)
                for j2, k in enumerate(range(3, 7)):
                    colk = L(2 + j2)                      # B..E des lignes 6/7
                    put(ws, f"{L(3 + j2)}{r}",
                        f"=IF(Config!$D${bk}=\"OUI\",{colk}$6^$A{r}+$A{r}*{colk}$7*{EV[ph]},{colk}$8)", f_norm, DEC)
        tl = s0 + 1 + T_SURVIE
        put(ws, f"A{rG - 1}", "Somme sur les spins du bonus du multi moyen d'une way (facteur du bonus)", f_sub, border=False)
        for j2 in range(4):
            col = L(3 + j2)
            put(ws, f"{L(2 + j2)}{rG}", f"=SUMPRODUCT($B${s0 + 2}:$B${tl},{col}{s0 + 2}:{col}{tl})", f_bold, DEC)
        put(ws, f"A{rG}", "Facteur du bonus", f_bold)
        put(ws, f"A{rG + 1}", "FS joués en moyenne", f_norm)
        put(ws, f"B{rG + 1}", f"=SUM(B{s0 + 2}:B{tl})", f_bold, "0.00")
        out.update({"fs": f"{nom}!$B${rG + 1}", "p_re": f"{nom}!{P_RE}"})
    widths(ws, {"A": 34, **{L(c): 10 for c in range(2, 20)}})
    return out


CALC = {"base": calc_sheet("base")}
for k in (1, 2, 3):
    CALC[f"fs{k}"] = calc_sheet(f"fs{k}", k)

# scatters du jeu de base (déclenchement des bonus) : dans Calc_Spins
ws = wb["Calc_Spins"]
p0, colf = bloc_scatters(ws, 30, "base", "Scatters sur la grille du jeu de base (déclenchement des bonus)")
NR = f"Calc_Spins!$A${p0}:$A${p0 + RMAX}"
PR = f"Calc_Spins!${colf}${p0}:${colf}${p0 + RMAX}"
FREQ = []
for k in range(3):
    bk = BONUS_R0 + k
    hi = "99"
    for kk in range(k + 1, 3):
        hi = f"IF({B_ACTIF[kk]},Config!$B${BONUS_R0 + kk},{hi})"
    FREQ.append(f"IF({B_ACTIF[k]},SUMPRODUCT(--({NR}>=Config!$B${bk}),--({NR}<{hi}),{PR}),0)")

# ============================================================================ Simulation (écrit par simulateur.py)
ws = wb.create_sheet("Simulation")
title(ws, "Résultats de la simulation (écrits par simulateur.py — ne pas saisir ici)", "python simulateur.py classeur_maths.xlsx")
header(ws, 4, 1, ["Jeu de base", "Valeur"])
FMT_SIM = {"spins": NUM, "rtp": "0.000%", "marge": "0.000%", "rtp_spins": PCT, "hit": PCT, "ecart_type": "0.00",
           "mediane": X2, "max": X2, "p_max": "0.0000000%", "etl40b": "0.000", "etl10k": "0.000", "cvar": "0.0"}
for key in SIMU.LIGNES_SIM:
    r = SIMU.SIM_LIGNE[key]
    put(ws, f"A{r}", SIMU.LIBELLES_SIM[key])
    fmt = FMT_SIM.get(key) or ("0.000000%" if key.startswith("freq") else PCT if key.startswith("rtp_bonus")
                               else X2 if key.startswith("gain") else "0.00")
    put(ws, f"B{r}", None, f_norm, fmt)
header(ws, SIMU.SIM_A0, 1, ["Chaque bonus joué comme un achat", "Bonus 1", "Bonus 2", "Bonus 3"])
for key in SIMU.LIGNES_ACHAT:
    r = SIMU.SIM_LIGNE["a_" + key]
    put(ws, f"A{r}", SIMU.LIBELLES_ACHAT[key])
    fmt = {"sessions": NUM, "prix": NUM, "rtp": PCT, "marge": PCT, "prix_conseille": "0", "p_max": "0.0000%",
           "etl40b": "0.000", "etl10k": "0.000", "cvar": "0.0"}.get(key, X2)
    for col in "BCD":
        put(ws, f"{col}{r}", None, f_norm, fmt)
header(ws, SIMU.SIM_C0, 1, ["Contrôle (simulation)", "Valeur", "Règle", "Statut"])
put(ws, "F4", "Distribution des gains (jeu de base)", f_head, fill=fill_head)
put(ws, "G4", "% des tours", f_head, fill=fill_head)
for i in range(10):
    put(ws, f"F{5 + i}", None)
    put(ws, f"G{5 + i}", None, f_norm, "0.0000%")
widths(ws, {"A": 44, "B": 22, "C": 46, "D": 12, "E": 2, "F": 22, "G": 14})
SIM = lambda key: f"Simulation!{SIMU.cellule(key)}"
SIMA = lambda key, k: f"Simulation!{'BCD'[k - 1]}{SIMU.SIM_LIGNE['a_' + key]}"

# ============================================================================ Résumé
ws = wb.create_sheet("Résumé", 1)
title(ws, "Résumé : RTP exact et équilibre", "Tout est recalculé en direct. Simulation = dernière exécution de simulateur.py.")
header(ws, 4, 1, ["Composante", "Fréquence", "Gain moyen", "FS joués", "RTP apporté", "Part du RTP", "Achat : prix", "RTP de l'achat", "Prix conseillé"])
r = 5
put(ws, f"A{r}", "Spins du jeu de base (multis compris)", f_bold)
put(ws, f"B{r}", "chaque spin")
put(ws, f"C{r}", f"={CALC['base']['total']}", f_norm, DEC)
put(ws, f"E{r}", f"={CALC['base']['total']}", f_bold, PCT)
ROW_SPINS = r
ROWS_B = []
for k in range(3):
    r = 6 + k
    bk = BONUS_R0 + k
    act = B_ACTIF[k]
    ph = f"fs{k + 1}"
    put(ws, f"A{r}", f'=IF({act},"Bonus {k + 1} : "&Config!A{bk}&IF(Config!D{bk}="OUI"," (collant)"," (non collant)"),"Bonus {k + 1} : non utilisé")')
    put(ws, f"B{r}", f"={FREQ[k]}", f_norm, "0.000000%")
    put(ws, f"C{r}", f"=IF({act},{CALC[ph]['total']},0)", f_norm, X2)
    put(ws, f"D{r}", f"=IF({act},{CALC[ph]['fs']},0)", f_norm, "0.0")
    put(ws, f"E{r}", f"=B{r}*C{r}", f_bold, PCT)
    put(ws, f"G{r}", f"=IF(ISNUMBER(Config!E{bk}),Config!E{bk},\"non achetable\")", f_link, NUM)
    put(ws, f"H{r}", f"=IF(ISNUMBER(Config!E{bk}),(C{r}+$C${ROW_SPINS})/Config!E{bk},\"-\")", f_norm, PCT)
    put(ws, f"I{r}", f"=IF({act},(C{r}+$C${ROW_SPINS})/RTP_CIBLE,\"-\")", f_norm, "0")
    ROWS_B.append(r)
rT = 9
put(ws, f"A{rT}", "RTP TOTAL EXACT (avant plafond du max win)", f_bold, fill=fill_key)
put(ws, f"E{rT}", f"=SUM(E{ROW_SPINS}:E{rT - 1})", f_bold, "0.000%", fill_key)
for rr in [ROW_SPINS] + ROWS_B:
    put(ws, f"F{rr}", f"=IF($E${rT}=0,0,E{rr}/$E${rT})", f_norm, PCT)
put(ws, f"A{rT + 1}", "Statut du RTP", f_bold)
put(ws, f"E{rT + 1}", f'=IF(AND(E{rT}>=RTP_MIN,E{rT}<=RTP_MAX),"OK",IF(E{rT}<RTP_MIN,"Trop bas","Trop haut"))', f_bold, fill=fill_key)
note(ws, f"A{rT + 2}", "Le SDK règle le RTP final exactement sur RTP_CIBLE ; le calcul exact doit déjà être dans [RTP_MIN ; RTP_MAX] pour que la distribution reste naturelle. "
     "Le plafond du max win retire en général moins de 0,1 % (voir Simulation).")
note(ws, f"A{rT + 3}", "Prix conseillé d'un achat = (gain moyen du bonus + gain moyen du spin de déclenchement) / RTP_CIBLE.")

# ---- Contrôles
c0 = rT + 6
put(ws, f"A{c0 - 1}", "CONTRÔLES (règles Stake Engine + équilibre)", f_sub, border=False)
header(ws, c0, 1, ["Contrôle", "Valeur", "Règle", "Statut"])
E_T = f"$E${rT}"
ctrl = [
    ("RTP exact", f"={E_T}", "0.000%", "entre RTP_MIN et RTP_MAX", f'=IF(AND({E_T}>=RTP_MIN,{E_T}<=RTP_MAX),"OK","ÉCHEC")'),
    ("Part des spins", f"=F{ROW_SPINS}", PCT, "entre PART_SPINS_MIN et PART_SPINS_MAX",
     f'=IF(AND(F{ROW_SPINS}>=PART_SPINS_MIN,F{ROW_SPINS}<=PART_SPINS_MAX),"OK","ÉCHEC")'),
]
for k in range(3):
    rr = ROWS_B[k]
    ctrl.append((f"Part du bonus {k + 1}", f"=F{rr}", PCT, "au plus PART_BONUS_MAX",
                 f'=IF(NOT({B_ACTIF[k]}),"-",IF(F{rr}<=PART_BONUS_MAX,"OK","ÉCHEC"))'))
for k in range(3):
    rr = ROWS_B[k]
    bk = BONUS_R0 + k
    ctrl.append((f"Achat bonus {k + 1} : RTP exact", f"=H{rr}", PCT, "à 0,5 % du jeu de base (règle Stake)",
                 f'=IF(NOT(ISNUMBER(Config!E{bk})),"-",IF(ABS(H{rr}-{E_T})<=0.005,"OK","ÉCHEC"))'))
for k in range(3):
    ctrl.append((f"Bonus {k + 1} : retriggers maîtrisés", f"={CALC[f'fs{k + 1}']['p_re']}*RETRIG_FS", DEC,
                 "P(retrigger) x FS ajoutés < 0,5", f'=IF(NOT({B_ACTIF[k]}),"-",IF({CALC[f"fs{k + 1}"]["p_re"]}*RETRIG_FS<0.5,"OK","ÉCHEC"))'))
ctrl += [
    ("Fréquence de gain (simulée)", f"={SIM('hit')}", PCT, "entre HIT_MIN et HIT_MAX (1 sur 3 à 1 sur 8)",
     f'=IF(NOT(ISNUMBER({SIM("hit")})),"Lance la simulation",IF(AND({SIM("hit")}>=HIT_MIN,{SIM("hit")}<=HIT_MAX),"OK","ÉCHEC"))'),
    ("RTP simulé = RTP exact ?", f"={SIM('rtp')}", "0.000%", "écart < 3 marges d'erreur (+0,1 % de plafond)",
     f'=IF(NOT(ISNUMBER({SIM("rtp")})),"Lance la simulation",IF(ABS({SIM("rtp")}-{E_T})<=3*{SIM("marge")}+0.001,"OK","ÉCART"))'),
    ("Max win atteignable", f"={SIM('p_max')}", "0.0000000%", "au moins 1 tour sur 20 000 000 (règle Stake)",
     f'=IF(NOT(ISNUMBER({SIM("p_max")})),"Lance la simulation",IF({SIM("p_max")}>=1/20000000,"OK","ÉCHEC"))'),
    ("3 étoiles : etl40b du jeu de base", f"={SIM('etl40b')}", "0.000", "≤ 0,9",
     f'=IF(NOT(ISNUMBER({SIM("etl40b")})),"Lance la simulation",IF({SIM("etl40b")}<=0.9,"OK","ÉCHEC"))'),
]
for i, (lbl, f, fmt, regle, st) in enumerate(ctrl):
    r = c0 + 1 + i
    put(ws, f"A{r}", lbl)
    put(ws, f"B{r}", f, f_norm, fmt)
    put(ws, f"C{r}", regle, f_note)
    put(ws, f"D{r}", st, f_bold, align=center)
note(ws, f"A{c0 + len(ctrl) + 2}", "Contrôles détaillés de la simulation (3 étoiles des achats, max win, etc.) : onglet Simulation et rapport_validation.md.")
widths(ws, {"A": 52, "B": 16, "C": 44, "D": 14, "E": 14, "F": 12, "G": 14, "H": 14, "I": 14})

for s in wb.worksheets:
    s.sheet_view.showGridLines = False
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("ok", OUT)
