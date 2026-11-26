#!/usr/bin/env python3
"""news-image-20261125: one-day world news broadsheet poster.

Draws a 1024x1024 PNG summing up Wednesday 25 November 2026 world news and
writes it to /output/entry.png ($MAKEFUN_OUTPUT_DIR overrides the directory).
No network, stdlib + Pillow only, fully deterministic: repeated runs write
identical bytes.

Page plan (1024x1024): masthead with date + story counts -> DAY IN NUMBERS
strip (six figures, each first reported 25 Nov) -> STORIES BY REGION bar ->
hero tier of the day's three consensus leads, each with a map or diagram
(Gulf map for Ras Tanura, tariff bar chart, Shenzhou rocket/orbit diagram)
-> ten more illustrated picture stories -> dotted world map (red pins 1-13
picture stories, dots 14-36 briefs) -> 23 briefs grouped by region ->
footer with DATE CHECK (explicit exclusions split by day + a Not yet line),
HOW SURE legend and HOW TO READ box. All 36 stories first reported Wed
25 Nov 2026.
"""

import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

# ---- palette: cool newsprint broadsheet, ink on paper ----
PAPER = (246, 242, 230)
INK = (18, 18, 18)
MUTED = (96, 90, 78)
FAINT = (150, 143, 126)
RED = (178, 30, 42)
NAVY = (26, 56, 92)
TEAL = (13, 108, 108)
GOLD = (172, 120, 20)
GREEN = (30, 118, 58)
CARD = (255, 255, 255)
LINE = (198, 190, 170)
SKY = (176, 212, 232)
SEA = (138, 188, 220)
LAND = (230, 220, 194)
SAND = (212, 194, 148)
PURPLE = (96, 58, 128)
ORANGE = (196, 96, 24)

REGION_COLORS = {
    "Middle East": (178, 30, 42),
    "Europe": (26, 56, 92),
    "Asia-Pacific": (13, 108, 108),
    "Africa": (172, 120, 20),
    "North America": (30, 118, 58),
    "Latin America": (96, 58, 128),
}

CONF_COLORS = {
    "CONFIRMED": (30, 118, 58),
    "OFFICIAL": (26, 56, 92),
    "REPORTED": (172, 120, 20),
    "CLAIM": (196, 96, 24),
    "FORECAST": (96, 58, 128),
}

# ---- fonts ----
_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts",
]


def _find_font(bold=False):
    names = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else [
        "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    for d in _FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


_FONTS = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _FONTS:
        path = _find_font(bold)
        if path:
            _FONTS[key] = ImageFont.truetype(path, size)
        else:
            _FONTS[key] = ImageFont.load_default()
    return _FONTS[key]


def text_w(draw, s, size, bold=False):
    return draw.textlength(s, font=font(size, bold))


def wrap(draw, s, size, max_w, bold=False):
    """Greedy word wrap returning a list of lines fitting max_w."""
    f = font(size, bold)
    words = s.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(draw, x, y, s, size, max_w, fill=INK, bold=False, leading=None):
    """Draw wrapped paragraph; return y just below the last line."""
    lh = leading if leading is not None else size + 3
    for line in wrap(draw, s, size, max_w, bold):
        draw.text((x, y), line, font=font(size, bold), fill=fill)
        y += lh
    return y


def headline(draw, x, y, s, size, max_w, fill=INK, bold=True, leading=None):
    return para(draw, x, y, s, size, max_w, fill=fill, bold=bold, leading=leading)


def tag(draw, x, y, label, fill):
    """Small confidence tag chip; returns width used."""
    f = font(9, True)
    w = int(draw.textlength(label, font=f)) + 10
    draw.rounded_rectangle([x, y, x + w, y + 14], radius=3, fill=fill)
    draw.text((x + 5, y + 2), label, font=f, fill=(255, 255, 255))
    return w


def rule(draw, x0, x1, y, fill=LINE, width=1):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def pin(draw, cx, cy, n, r=9):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                 outline=(255, 255, 255), width=2)
    f = font(10, True)
    tw = draw.textlength(str(n), font=f)
    draw.text((cx - tw / 2, cy - 7), str(n), font=f, fill=(255, 255, 255))


def dot(draw, cx, cy, r=3, fill=NAVY):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
                 outline=(255, 255, 255), width=1)

# =====================================================================
# Hero tier: three illustrated features, each a map or a diagram.
# =====================================================================

def hero_gulf(d, x, y, w, h):
    """Gulf map: Ras Tanura refinery, Riyadh, Jazan, Hodeidah.

    Stylised Arabian Peninsula (land, sand) against the Gulf (sea).
    Pins: 1 Ras Tanura (refinery, smoke), Riyadh (financial district),
    Jazan port, Hodeidah across the water. Honest labels: the Houthi
    claim + satellite smoke are reported; Riyadh has not confirmed a hit.
    """
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=LINE)
    # Arabian Peninsula land mass (left/bottom) and Iran (top right)
    d.polygon([(x, y), (x + w, y), (x + w, y + 30), (x + 236, y + 44),
               (x + 200, y + 26), (x + 120, y + 30), (x + 40, y + 22),
               (x, y + 34)], fill=LAND)
    d.polygon([(x, y + h), (x + w, y + h), (x + w, y + 52),
               (x + 250, y + 58), (x + 210, y + h - 46), (x + 120, y + h - 30),
               (x + 40, y + h - 52), (x, y + h - 30)], fill=SAND)
    d.text((x + 8, y + 6), "IRAN", font=font(9, True), fill=MUTED)
    d.text((x + 8, y + h - 16), "ARABIAN PENINSULA", font=font(9, True),
           fill=MUTED)
    d.text((x + w // 2 - 30, y + 46), "THE GULF", font=font(9, True),
           fill=NAVY)
    # Ras Tanura pin (east coast, upper middle) + smoke plume
    rx, ry = x + 238, y + 62
    for sx, sy, r in [(rx + 4, ry - 16, 9), (rx + 14, ry - 26, 12),
                      (rx + 26, ry - 34, 8)]:
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(70, 70, 70))
    d.text((x + 252, y + 6), "SMOKE SEEN", font=font(8, True), fill=INK)
    d.text((x + 252, y + 16), "BY SATELLITE", font=font(8, True), fill=INK)
    pin(d, rx, ry, 1, r=10)
    d.text((x + 208, y + 76), "RAS TANURA", font=font(9, True), fill=INK)
    # Riyadh (inland) + Jazan port (south-west coast)
    d.ellipse([x + 148, y + 74, x + 156, y + 82], fill=RED,
              outline=(255, 255, 255), width=1)
    d.text((x + 130, y + 62), "RIYADH", font=font(9, True), fill=INK)
    d.ellipse([x + 108, y + 90, x + 114, y + 96], fill=NAVY,
              outline=(255, 255, 255), width=1)
    d.text((x + 118, y + 88), "JAZAN", font=font(8, True), fill=INK)
    # Hodeidah across the water (bottom right)
    d.ellipse([x + 272, y + 90, x + 278, y + 96], fill=ORANGE,
              outline=(255, 255, 255), width=1)
    d.text((x + 226, y + 88), "HODEIDAH", font=font(8, True), fill=INK)


def hero_tariffs(d, x, y, w, h):
    """Tariff bar chart. Only China's +20% rate is published; the other
    13 partners are shown as one honest 'rates not yet published' block —
    no rates are invented."""
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=LINE)
    d.text((x + 10, y + 6), "US PROPOSES NEW TARIFFS — 14 PARTNERS",
           font=font(11, True), fill=INK)
    # China bar: +20% (the only published rate)
    bx, by, bw, bh = x + 10, y + 24, 150, 28
    d.rectangle([bx, by, bx + bw, by + bh], fill=RED)
    d.text((bx + 8, by + 6), "CHINA  +20%", font=font(12, True),
           fill=(255, 255, 255))
    d.text((bx + bw + 10, by + 2), "highest rate;", font=font(10), fill=INK)
    d.text((bx + bw + 10, by + 16), "blamed most for", font=font(10), fill=INK)
    # 13 more partners: one "?" tile each — rates NOT published, none invented
    tx, ty = x + 10, y + 56
    for i in range(13):
        d.rectangle([tx + i * 22, ty, tx + i * 22 + 18, ty + 18],
                    outline=MUTED, fill=(238, 238, 238))
        d.text((tx + i * 22 + 6, ty + 3), "?", font=font(11, True),
               fill=MUTED)
    d.text((x + 10, ty + 22), "OTHER 13 PARTNERS — RATES UNSPECIFIED",
           font=font(9, True), fill=INK)
    d.text((x + 10, y + h - 12), "WILL NOT STACK ON JULY DUTIES",
           font=font(9, True), fill=GREEN)


def hero_shenzhou(d, x, y, w, h):
    """Shenzhou-24 rocket + orbit diagram with launch/dock timeline."""
    d.rectangle([x, y, x + w, y + h], fill=(12, 20, 44), outline=LINE)
    for sx, sy in [(x + 20, y + 14), (x + 48, y + 30), (x + 90, y + 12),
                   (x + 130, y + 22), (x + 200, y + 16), (x + 250, y + 30),
                   (x + 290, y + 12)]:
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
    # orbit arc across the top right + Tiangong station
    d.arc([x + 140, y - 60, x + 330, y + 20], start=0, end=180, fill=GOLD,
          width=2)
    d.rectangle([x + 250, y + 18, x + 296, y + 30], fill=(220, 220, 220),
                outline=GOLD)
    d.rectangle([x + 238, y + 21, x + 250, y + 27], fill=SKY)
    d.rectangle([x + 296, y + 21, x + 308, y + 27], fill=SKY)
    d.text((x + 238, y + 34), "TIANGONG", font=font(9, True),
           fill=(255, 255, 255))
    # rocket body, lower left
    cx = x + 70
    d.polygon([(cx, y + 46), (cx + 11, y + 64), (cx + 11, y + 96),
               (cx, y + 106), (cx - 11, y + 96), (cx - 11, y + 64)],
              fill=(255, 255, 255), outline=RED)
    d.ellipse([cx - 4, y + 66, cx + 4, y + 74], fill=SKY, outline=NAVY)
    d.polygon([(cx - 13, y + 98), (cx - 24, y + h - 18), (cx - 6, y + 98)],
              fill=RED)
    d.polygon([(cx + 13, y + 98), (cx + 24, y + h - 18), (cx + 6, y + 98)],
              fill=RED)
    d.polygon([(cx - 5, y + 106), (cx + 5, y + 106), (cx + 13, y + h - 8),
               (cx - 13, y + h - 8)], fill=GOLD)
    d.text((cx + 30, y + 40), "SHENZHOU-24", font=font(11, True),
           fill=(255, 255, 255))
    # timeline, bottom
    d.line([(x + 110, y + h - 26), (x + w - 14, y + h - 26)], fill=GOLD,
           width=2)
    d.ellipse([x + 108, y + h - 29, x + 114, y + h - 23], fill=GOLD)
    d.ellipse([x + w - 16, y + h - 29, x + w - 10, y + h - 23], fill=GOLD)
    d.text((x + 110, y + h - 46), "00:18 UTC", font=font(9, True),
           fill=(255, 255, 255))
    d.text((x + 110, y + h - 35), "LAUNCH", font=font(9, True),
           fill=(212, 176, 60))
    d.text((x + w - 92, y + h - 46), "03:56 UTC", font=font(9, True),
           fill=(255, 255, 255))
    d.text((x + w - 92, y + h - 35), "DOCK", font=font(9, True),
           fill=(212, 176, 60))
    d.text((x + 120, y + h - 16), "1st foreign astronaut aboard Tiangong",
           font=font(9), fill=(212, 176, 60))

# =====================================================================
# Picture-story illustrations: small procedural vector scenes.
# Each draws inside (x, y, w, h).
# =====================================================================

def ill_store(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(246, 232, 210))
    d.rectangle([x + 10, y + 26, x + w - 10, y + h - 8], fill=(255, 255, 255),
                outline=INK)
    d.rectangle([x + 10, y + 26, x + w - 10, y + 38], fill=RED)
    d.text((x + 16, y + 28), "SUPERMARKET", font=font(9, True),
           fill=(255, 255, 255))
    d.rectangle([x + 20, y + 42, x + w // 2 - 6, y + h - 8], fill=SKY,
                outline=INK)
    d.rectangle([x + w // 2 + 6, y + 42, x + w - 20, y + h - 8], fill=SKY,
                outline=INK)
    d.text((x + 8, y + 8), "76 HELD · ALL FREED", font=font(11, True),
           fill=RED)


def ill_gaza(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(238, 232, 220))
    # apartment block silhouette + strike flash
    d.rectangle([x + 20, y + 22, x + w - 20, y + h - 8], fill=(120, 110, 96))
    for r in range(3):
        for c in range(4):
            d.rectangle([x + 28 + c * 32, y + 30 + r * 14,
                         x + 44 + c * 32, y + 40 + r * 14],
                        fill=(60, 55, 48))
    d.polygon([(x + w // 2, y + 4), (x + w // 2 + 10, y + 18),
               (x + w // 2 + 26, y + 18), (x + w // 2 + 13, y + 28),
               (x + w // 2 + 18, y + 42), (x + w // 2, y + 32),
               (x + w // 2 - 18, y + 42), (x + w // 2 - 13, y + 28),
               (x + w // 2 - 26, y + 18), (x + w // 2 - 10, y + 18)],
              fill=GOLD)
    d.rectangle([x, y + h - 14, x + w, y + h], fill=(255, 255, 255))
    d.text((x + 8, y + h - 13), "GAZA CITY · OVERNIGHT", font=font(8, True),
           fill=INK)


def ill_treaty(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 238, 246))
    # two flags on poles + handshake arc
    d.line([(x + 30, y + 10), (x + 30, y + 52)], fill=INK, width=2)
    d.polygon([(x + 30, y + 10), (x + 72, y + 18), (x + 30, y + 26)],
              fill=NAVY)
    d.text((x + 36, y + 12), "AU", font=font(8, True), fill=(255, 255, 255))
    d.line([(x + w - 30, y + 10), (x + w - 30, y + 52)], fill=INK, width=2)
    d.polygon([(x + w - 30, y + 10), (x + w - 72, y + 18),
               (x + w - 30, y + 26)], fill=TEAL)
    d.text((x + w - 62, y + 12), "SB", font=font(8, True),
           fill=(255, 255, 255))
    d.arc([x + w // 2 - 34, y + 30, x + w // 2 + 34, y + 62], start=180,
          end=360, fill=GREEN, width=3)
    d.text((x + 8, y + h - 14), "NO FOREIGN BASES", font=font(9, True),
           fill=GREEN)


def ill_deal(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    # document + shelved stamp
    d.rectangle([x + 30, y + 8, x + w - 30, y + h - 8], fill=(246, 242, 230),
                outline=INK)
    for i in range(4):
        d.line([(x + 38, y + 18 + i * 10), (x + w - 38, y + 18 + i * 10)],
               fill=MUTED, width=1)
    d.line([(x + 30, y + 14), (x + w - 30, y + h - 22)], fill=RED, width=3)
    d.line([(x + w - 30, y + 14), (x + 30, y + h - 22)], fill=RED, width=3)
    d.text((x + 8, y + h - 14), "SHELVED — FT", font=font(9, True), fill=RED)


def ill_blast(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 238))
    # barrels + blast star
    for bx in [x + 22, x + 44, x + 66]:
        d.rectangle([bx, y + h - 26, bx + 16, y + h - 10], fill=(90, 110, 90),
                    outline=INK)
        d.line([(bx, y + h - 20), (bx + 16, y + h - 20)], fill=INK, width=1)
    d.polygon([(x + w // 2, y + 6), (x + w // 2 + 8, y + 22),
               (x + w // 2 + 24, y + 22), (x + w // 2 + 12, y + 32),
               (x + w // 2 + 16, y + 48), (x + w // 2, y + 38),
               (x + w // 2 - 16, y + 48), (x + w // 2 - 12, y + 32),
               (x + w // 2 - 24, y + 22), (x + w // 2 - 8, y + 22)],
              fill=GOLD)
    d.text((x + 8, y + 6), "5 TONS", font=font(11, True), fill=INK)


def ill_market(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    # candlesticks: sharp fall, then recovery
    vals = [(0, 18, 8), (1, 26, 8), (2, 38, 8), (3, 30, 8), (4, 24, 8)]
    for i, (col, top, hh) in enumerate(vals):
        bx = x + 16 + i * 30
        col = RED if i < 3 else GREEN
        d.rectangle([bx, y + top, bx + 14, y + top + hh], fill=col)
        d.line([(bx + 7, y + top - 6), (bx + 7, y + top + hh + 6)], fill=col,
               width=1)
    d.line([(x + 8, y + 12), (x + w - 8, y + 12)], fill=FAINT, width=1)
    d.text((x + 8, y + h - 14), "S&P -3% THEN UP", font=font(9, True),
           fill=INK)


def ill_ball(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(20, 90, 50))
    # football + scoreboard
    d.ellipse([x + w // 2 - 24, y + 12, x + w // 2 + 24, y + 60],
              fill=(255, 255, 255), outline=INK, width=2)
    d.polygon([(x + w // 2 - 8, y + 24), (x + w // 2 + 8, y + 24),
               (x + w // 2 + 12, y + 36), (x + w // 2, y + 44),
               (x + w // 2 - 12, y + 36)], fill=INK)
    d.line([(x + w // 2, y + 12), (x + w // 2, y + 24)], fill=INK, width=2)
    d.line([(x + w // 2 - 24, y + 36), (x + w // 2 - 12, y + 36)], fill=INK,
           width=2)
    d.line([(x + w // 2 + 12, y + 36), (x + w // 2 + 24, y + 36)], fill=INK,
           width=2)
    d.text((x + 8, y + h - 14), "PSG 2-2 · BAYERN LOSE", font=font(8, True),
           fill=(255, 255, 255))


def ill_hasaka(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(246, 232, 210))
    # warning triangle + map pin
    d.polygon([(x + w // 2, y + 8), (x + w // 2 + 26, y + 52),
               (x + w // 2 - 26, y + 52)], fill=GOLD, outline=INK)
    d.text((x + w // 2 - 4, y + 26), "!", font=font(18, True), fill=INK)
    d.ellipse([x + w // 2 - 10, y + h - 22, x + w // 2 + 10, y + h - 2],
              fill=RED, outline=(255, 255, 255), width=1)
    d.text((x + 8, y + h - 14), "HASAKA, SYRIA", font=font(8, True),
           fill=INK)


def ill_sat(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(12, 20, 44))
    for sx, sy in [(x + 16, y + 12), (x + 40, y + 26), (x + w - 20, y + 14),
                   (x + w - 44, y + 34), (x + 24, y + h - 16)]:
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
    # satellite body + panels
    d.rectangle([x + w // 2 - 14, y + 22, x + w // 2 + 14, y + 44],
                fill=(220, 220, 220), outline=GOLD)
    d.rectangle([x + w // 2 - 52, y + 28, x + w // 2 - 16, y + 38],
                fill=NAVY, outline=GOLD)
    d.rectangle([x + w // 2 + 16, y + 28, x + w // 2 + 52, y + 38],
                fill=NAVY, outline=GOLD)
    d.line([(x + w // 2, y + 44), (x + w // 2, y + 56)], fill=GOLD, width=2)
    d.text((x + 8, y + h - 14), "1,000,000 SATELLITES", font=font(8, True),
           fill=(255, 255, 255))


def ill_parade(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(176, 212, 232))
    # balloon hippo (Macy's 100th parade) + rain cloud
    d.ellipse([x + 30, y + 14, x + w - 30, y + 52], fill=(90, 140, 200),
              outline=NAVY)
    d.ellipse([x + 40, y + 20, x + 52, y + 30], fill=(255, 255, 255))
    d.ellipse([x + w - 52, y + 20, x + w - 40, y + 30], fill=(255, 255, 255))
    d.ellipse([x + w // 2 - 12, y + 40, x + w // 2 + 12, y + 48],
              fill=(255, 255, 255))
    d.line([(x + w // 2, y + 52), (x + w // 2, y + h - 10)], fill=INK,
           width=1)
    d.ellipse([x + 12, y + 8, x + 40, y + 22], fill=(200, 200, 200))
    d.text((x + 8, y + h - 14), "PARADE → SATURDAY", font=font(9, True),
           fill=NAVY)

# =====================================================================
# Story data. Every story first reported Wed 25 Nov 2026 (UTC).
# conf: CONFIRMED 2+ outlets / OFFICIAL the body itself / REPORTED one
# outlet / CLAIM one side / FORECAST expected.
# =====================================================================

HEROES = [
    {
        "n": 1, "region": "Middle East", "conf": "CLAIM",
        "title": "Houthis claim Ras Tanura strike",
        "summary": ("Houthis say they hit Saudi's largest refinery; "
                    "satellite images show smoke. Coalition downed 4 "
                    "drones; Riyadh has not confirmed a hit."),
        "outlet": "Reuters / Straits Times", "ill": "gulf",
        "note": "STRIKE NOT VERIFIED",
    },
    {
        "n": 2, "region": "North America", "conf": "CONFIRMED",
        "title": "US proposes new tariffs on 14 partners",
        "summary": ("China faces +20%; the EU, Japan, South Korea, Taiwan "
                    "and 9 more are named. Duties will not stack on July's."),
        "outlet": "Reuters / AP", "ill": "tariffs",
    },
    {
        "n": 3, "region": "Asia-Pacific", "conf": "OFFICIAL",
        "title": "Shenzhou-24 puts first foreign astronaut on Tiangong",
        "summary": ("Pakistan's Muhammad Zeeshan Ali boards Tiangong with "
                    "Tang Hongbo and Wu Yi after a 00:18 UTC launch."),
        "outlet": "Xinhua / AP", "ill": "shenzhou",
    },
]

PICTURES = [
    {
        "n": 4, "region": "Latin America", "conf": "CONFIRMED",
        "title": "Cartagena siege ends: all 76 hostages freed",
        "summary": ("Police storm the supermarket after a 17-hour siege; "
                    "everyone freed unharmed, one captor killed."),
        "outlet": "Al Jazeera / Arab News", "ill": ill_store,
    },
    {
        "n": 5, "region": "Middle East", "conf": "CONFIRMED",
        "title": "Israel kills 2nd Hamas security chief in 2 days",
        "summary": ("Overnight Shati strike kills Muhammad Abu al-Awf, his "
                    "wife and two daughters, a day after his predecessor."),
        "outlet": "Times of Israel / JPost", "ill": ill_gaza,
    },
    {
        "n": 6, "region": "Asia-Pacific", "conf": "CONFIRMED",
        "title": "Australia signs Solomons security treaty",
        "summary": ("Canberra becomes Honiara's primary security partner; "
                    "no foreign bases, A$740m over 10 years."),
        "outlet": "Reuters / NZ Herald", "ill": ill_treaty,
    },
    {
        "n": 7, "region": "Europe", "conf": "REPORTED",
        "title": "US shelves business-deal incentives for Russia",
        "summary": ("Washington drops corporate tie-ups as a lever to end "
                    "the Ukraine war, the FT reports; summit due 26 Nov."),
        "outlet": "FT via The Hindu", "ill": ill_deal,
    },
    {
        "n": 8, "region": "North America", "conf": "OFFICIAL",
        "title": "Army blows up 5 tons of bomb chemicals in Iowa",
        "summary": ("Middletown is evacuated as 68 barrels of lead azide "
                    "are detonated; the Army calls it a success."),
        "outlet": "AP", "ill": ill_blast,
    },
    {
        "n": 9, "region": "North America", "conf": "CONFIRMED",
        "title": "S&P slumps 3% in AI rout, then recovers",
        "summary": ("Wall Street fights back from deep lows; Nvidia ends "
                    "-3.9% at $149.30, Anthropic below its $83 IPO price."),
        "outlet": "AP / Reuters", "ill": ill_market,
    },
    {
        "n": 10, "region": "Europe", "conf": "CONFIRMED",
        "title": "PSG held, Bayern beaten in Champions League",
        "summary": ("PSG 2-2 Roma, Utd 2-2 Sporting, Bayern lose 2-1 at "
                    "Lille; Barca 4-1 Sabah, Liverpool 3-0 Brugge."),
        "outlet": "UEFA / AP", "ill": ill_ball,
    },
    {
        "n": 11, "region": "Middle East", "conf": "REPORTED",
        "title": "IS attack kills two Syrian security men in Hasaka",
        "summary": ("Islamic State attack kills two internal security "
                    "personnel and wounds five in north-eastern Syria."),
        "outlet": "Reuters / state TV", "ill": ill_hasaka,
    },
    {
        "n": 12, "region": "Asia-Pacific", "conf": "OFFICIAL",
        "title": "FCC clears SpaceX to launch 1,000,000 satellites",
        "summary": ("SpaceX may deploy a million satellites for data "
                    "centres in space; scientists are sceptical."),
        "outlet": "AP", "ill": ill_sat,
    },
    {
        "n": 13, "region": "North America", "conf": "CONFIRMED",
        "title": "Macy's parade postponed to Saturday",
        "summary": ("Bad weather pushes the 100th Thanksgiving Day Parade "
                    "to Saturday as an East Coast storm bears down."),
        "outlet": "AP", "ill": ill_parade,
    },
]

# Briefs: (number, region, confidence, one-line headline, outlet)
BRIEFS = [
    (14, "North America", "CONFIRMED",
     "Abrego Garcia leaves US for Spain, hopes to return after Trump", "AP"),
    (15, "North America", "CONFIRMED",
     "Plane crash off Mississippi coast kills family of 6", "AP"),
    (16, "North America", "CONFIRMED",
     "Steelers cut Aaron Rodgers after benching, TV outburst", "AP"),
    (17, "Europe", "CONFIRMED",
     "Andy Taylor, Duran Duran guitarist, dies at 65", "AP"),
    (18, "North America", "CONFIRMED",
     "MLB sues players union over lockout legality", "AP"),
    (19, "North America", "CONFIRMED",
     "LeBron's first 76ers triple-double beats the Heat", "AP"),
    (20, "North America", "OFFICIAL",
     "US Q3 GDP revised up to 4.3%; core inflation 3.3%", "Commerce Dept"),
    (21, "North America", "CONFIRMED",
     "US consumer confidence highest in nearly two years", "Reuters"),
    (22, "North America", "CONFIRMED",
     "Average US 30-year mortgage rate eases to 7.21%", "AP"),
    (23, "North America", "REPORTED",
     "Thanksgiving dinner up ~6% on last year", "Farm Bureau"),
    (24, "Africa", "REPORTED",
     "Libya vows retaliation after Ukrainian drone attack", "AP"),
    (25, "Africa", "REPORTED",
     "Congo fighting forces Ebola workers to evacuate", "AP"),
    (26, "North America", "OFFICIAL",
     "Melania Trump reunites 7th group of Ukrainian, Russian children", "AP"),
    (27, "Europe", "REPORTED",
     "Ukraine and Hungary leaders signal a reset", "Guardian / Reuters"),
    (28, "Europe", "REPORTED",
     "EU proposes 22nd sanctions package vs Russia", "Reuters / AFP"),
    (29, "Europe", "REPORTED",
     "Russian strikes hit Odesa and Kyiv, casualties reported", "Reuters / AFP"),
    (30, "Europe", "REPORTED",
     "EU: Taliban cooperation is not recognition", "Reuters / BBC"),
    (31, "North America", "CONFIRMED",
     "Essence Festival bids farewell to New Orleans", "AP"),
    (32, "North America", "REPORTED",
     "Judge declines ban on pro-Trump taxpayer ads", "AP"),
    (33, "North America", "CONFIRMED",
     "Martha Ford, former Detroit Lions owner, dies at 101", "AP"),
    (34, "North America", "REPORTED",
     "Canada PM roasts Trump with a Trump impersonator", "AP"),
    (35, "Europe", "CONFIRMED",
     "Two charged over burglary at William and Catherine's home", "AP"),
    (36, "North America", "CONFIRMED",
     "King tides flood coasts more as seas rise", "AP"),
]

DATE_CHECK = [
    ("24 NOV",
     "Huawei guilty 10/12 · Hormuz tankers hit mines · Riyadh tower hit, "
     "11 hurt · Hamas chief killed · Trump pardons turkeys · Shein $100m · "
     "CIA breached · Trump warns Russia (24 Nov)"),
    ("22 NOV & EARLIER",
     "COP31 collapses, no fossil-fuel deal (22 Nov) · OpenAI apology to "
     "Australia (28 Sep; full review 20 Nov)"),
    ("NOT YET",
     "Trump-Putin summit, Anchorage (Thu 26 Nov) · Thanksgiving Day "
     "(Thu 26 Nov) · Macy's parade (Sat 28 Nov) · Shenzhou-24 astronaut "
     "returns (about a week)"),
]

# Map pins: (number, lon, lat, dx, dy) for picture stories; dots for briefs.
PINS = {
    1: (50.1, 26.6, 0, 0),
    2: (-77.0, 39.0, 0, 0),
    3: (98.5, 40.0, 0, 0),
    4: (-75.5, 10.4, 0, 0),
    5: (34.5, 31.5, 0, 0),
    6: (149.1, -35.3, 0, 0),
    7: (37.6, 55.8, 0, 0),
    8: (-91.3, 40.8, 0, 0),
    9: (-74.0, 40.7, -4, -10),
    10: (2.35, 48.9, 0, 0),
    11: (40.7, 36.5, 0, 0),
    12: (-80.6, 28.4, 0, 0),
    13: (-74.0, 40.7, 10, 8),
}
DOTS = {
    14: (-3.7, 40.4, 0, 0),
    15: (-89.4, 30.2, 0, 0),
    16: (-80.0, 40.4, 0, 0),
    17: (-0.1, 51.5, 0, 0),
    18: (-74.0, 40.7, -10, 4),
    19: (-75.2, 40.0, 6, -6),
    20: (-77.0, 39.0, 8, 6),
    21: (-77.0, 39.0, -12, -4),
    22: (-77.0, 39.0, 4, -10),
    23: (-98.0, 39.8, 0, 0),
    24: (13.2, 32.9, 0, 0),
    25: (25.0, -2.0, 0, 0),
    26: (-77.0, 39.0, -6, 10),
    27: (30.5, 50.4, 0, 0),
    28: (4.35, 50.85, 0, 0),
    29: (30.7, 46.5, 6, 4),
    30: (69.2, 34.5, 0, 0),
    31: (-90.1, 30.0, 0, 0),
    32: (-77.0, 39.0, 12, -2),
    33: (-83.0, 42.3, 0, 0),
    34: (-75.7, 45.4, 0, 0),
    35: (1.0, 52.6, 0, 0),
    36: (0.0, 82.0, 0, 0),
}

# =====================================================================
# Section renderers
# =====================================================================

HERO_ILLS = {"gulf": hero_gulf, "tariffs": hero_tariffs,
             "shenzhou": hero_shenzhou}


def draw_masthead(d):
    d.rectangle([0, 0, W, 66], fill=INK)
    d.text((18, 8), "THE WORLD IN ONE DAY", font=font(30, True),
           fill=(247, 243, 232))
    d.text((18, 42), "WEDNESDAY 25 NOVEMBER 2026  ·  36 STORIES  ·  6 REGIONS  ·  13 PICTURED",
           font=font(13, True), fill=(212, 176, 60))
    d.text((W - 18, 10), "ONE DAY.", font=font(20, True),
           fill=(247, 243, 232), anchor="ra")
    d.text((W - 18, 36), "ONE IMAGE.", font=font(20, True),
           fill=(212, 176, 60), anchor="ra")


NUMBERS = [
    ("+20%", "new tariff proposed on Chinese goods"),
    ("$93.60", "Brent crude after Ras Tanura claim, +2.4%"),
    ("4.3%", "US Q3 GDP growth, revised up"),
    ("550,000", "barrels/day, Ras Tanura capacity"),
    ("76", "hostages held in Cartagena, all freed"),
    ("1,000,000", "satellites FCC cleared SpaceX to deploy"),
]


def draw_numbers(d, y0=72):
    d.rectangle([0, y0, W, y0 + 52], fill=(255, 255, 255))
    rule(d, 0, W, y0 + 51)
    d.text((18, y0 + 6), "DAY IN NUMBERS", font=font(11, True), fill=RED)
    d.text((18, y0 + 24), "every figure first reported 25 Nov",
           font=font(10), fill=MUTED)
    cw = (W - 260) // 6
    for i, (num, label) in enumerate(NUMBERS):
        x = 250 + i * cw
        d.text((x, y0 + 4), num, font=font(20, True), fill=INK)
        for j, ln in enumerate(wrap(d, label, 9, cw - 8)):
            d.text((x, y0 + 28 + j * 11), ln, font=font(9), fill=MUTED)


REGION_COUNTS = [
    ("North America", 19),
    ("Europe", 8),
    ("Middle East", 3),
    ("Asia-Pacific", 3),
    ("Africa", 2),
    ("Latin America", 1),
]


def draw_region_bar(d, y0=130):
    d.text((18, y0), "STORIES BY REGION", font=font(11, True), fill=INK)
    total = sum(c for _, c in REGION_COUNTS)
    x = 18
    bar_w = W - 36
    y = y0 + 18
    for name, c in REGION_COUNTS:
        w = bar_w * c / total
        d.rectangle([x, y, x + w - 1, y + 14], fill=REGION_COLORS[name])
        x += w
    lx = 18
    for name, c in REGION_COUNTS:
        col = REGION_COLORS[name]
        d.rectangle([lx, y0 + 38, lx + 8, y0 + 46], fill=col)
        t = "%s %d" % (name, c)
        d.text((lx + 12, y0 + 37), t, font=font(10, True), fill=INK)
        lx += int(text_w(d, t, 10, True)) + 26


def draw_hero_card(d, x, y, w, h, story):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=LINE)
    HERO_ILLS[story["ill"]](d, x + 1, y + 1, w - 2, 100)
    yy = y + 106
    yy = headline(d, x + 8, yy, "%d. %s" % (story["n"], story["title"]), 13,
                  w - 16, leading=15)
    yy = para(d, x + 8, yy + 2, story["summary"], 10, w - 16, fill=MUTED,
              leading=12)
    tw = tag(d, x + 8, yy, story["conf"], CONF_COLORS[story["conf"]])
    d.text((x + 8 + tw + 6, yy + 1), story["outlet"], font=font(9), fill=FAINT)
    if "note" in story:
        nw = int(text_w(d, story["note"], 9, True)) + 10
        d.rectangle([x + w - 8 - nw, yy - 1, x + w - 8, yy + 13], fill=RED)
        d.text((x + w - 13 - nw, yy + 1), story["note"], font=font(9, True),
               fill=(255, 255, 255))


def draw_pic_card(d, x, y, w, h, story):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=LINE)
    story["ill"](d, x + 1, y + 1, w - 2, 62)
    yy = y + 68
    yy = headline(d, x + 7, yy, "%d. %s" % (story["n"], story["title"]), 11,
                  w - 14, leading=12)
    yy = para(d, x + 7, yy + 1, story["summary"], 9, w - 14, fill=MUTED,
              leading=11)
    tag(d, x + 7, yy, story["conf"], CONF_COLORS[story["conf"]])


# Simplified continent outlines (lon, lat) for the dotted world map.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-75, 58), (-65, 60), (-60, 52), (-70, 45), (-75, 38),
     (-80, 32), (-85, 29), (-90, 21), (-95, 19), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-135, 58), (-150, 60), (-165, 60)],
    # South America
    [(-80, 9), (-75, 11), (-65, 10), (-55, 6), (-50, 0), (-45, -5),
     (-38, -8), (-35, -15), (-40, -22), (-48, -28), (-55, -35), (-65, -42),
     (-70, -50), (-73, -40), (-73, -30), (-70, -18), (-78, -8), (-80, 0)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (12, 56),
     (18, 56), (21, 55), (24, 59), (28, 61), (30, 70), (40, 68), (45, 60),
     (40, 55), (35, 50), (30, 46), (28, 44), (23, 40), (20, 40), (15, 44),
     (10, 44), (5, 43), (0, 40), (-2, 37)],
    # Africa
    [(-17, 15), (-15, 27), (-10, 31), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (38, 20), (43, 12), (48, 11), (51, 2), (48, -5), (42, -12),
     (38, -20), (33, -26), (28, -33), (20, -35), (15, -28), (12, -18),
     (10, -8), (8, 4), (0, 5), (-8, 5), (-13, 8)],
    # Asia
    [(45, 60), (55, 68), (65, 70), (75, 73), (90, 75), (105, 77), (120, 73),
     (135, 72), (150, 70), (160, 66), (170, 65), (178, 65), (170, 60),
     (160, 55), (150, 45), (140, 40), (130, 35), (125, 30), (120, 25),
     (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20), (80, 8),
     (75, 8), (70, 20), (65, 25), (60, 25), (55, 26), (50, 29), (48, 30),
     (44, 35), (40, 40), (38, 45), (42, 50), (45, 55)],
    # Australia
    [(114, -22), (120, -33), (130, -32), (140, -38), (150, -37), (153, -27),
     (146, -19), (142, -11), (135, -12), (130, -13), (122, -14), (115, -20)],
]


def draw_world_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(238, 244, 248), outline=LINE)
    d.text((x + 8, y + 5), "WHERE IT HAPPENED", font=font(10, True), fill=INK)
    d.text((x + 8, y + 19), "red pins 1-13 picture stories · dots 14-36 briefs",
           font=font(9), fill=MUTED)

    def proj(lon, lat):
        px = x + 8 + (lon + 180) / 360.0 * (w - 16)
        py = y + 34 + (82 - lat) / 142.0 * (h - 40)
        return (px, py)

    for poly in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=LAND,
                  outline=(180, 168, 140))
    for n, (lon, lat, dx, dy) in sorted(PINS.items()):
        px, py = proj(lon, lat)
        pin(d, px + dx, py + dy, n, r=8)
    for n, (lon, lat, dx, dy) in sorted(DOTS.items()):
        px, py = proj(lon, lat)
        dot(d, px + dx, py + dy, r=3)
    d.text((x + w - 8, y + h - 14), "36 = king tides (global)",
           font=font(8), fill=MUTED, anchor="ra")


def draw_briefs(d, x, y, w, h):
    by_n = {b[0]: b for b in BRIEFS}
    cols = [
        [("North America", [14, 15, 16, 18, 19, 20, 21, 22])],
        [("North America", [23, 26, 31, 32, 33, 34, 36]),
         ("Africa", [24])],
        [("Africa", [25]),
         ("Europe", [17, 27, 28, 29, 30, 35])],
    ]
    cw = (w - 24) // 3
    for ci, groups in enumerate(cols):
        cx = x + ci * (cw + 12)
        cy = y
        for gname, nums in groups:
            d.text((cx, cy), gname.upper(), font=font(10, True),
                   fill=REGION_COLORS[gname])
            cy += 13
            for n in nums:
                _, region, conf, head, outlet = by_n[n]
                col = CONF_COLORS[conf]
                d.rectangle([cx, cy + 1, cx + 7, cy + 8], fill=col)
                line = "%d. %s" % (n, head)
                f = font(9, True)
                while d.textlength(line, font=f) > cw - 12 and len(line) > 12:
                    line = line[:-4].rstrip() + "…"
                d.text((cx + 11, cy), line, font=f, fill=INK)
                cy += 12
            cy += 3


def draw_footer(d, y0):
    d.rectangle([0, y0, W, H], fill=(238, 234, 222))
    rule(d, 0, W, y0, fill=INK, width=2)
    # title row: DATE CHECK title left, HOW SURE chips right
    d.text((18, y0 + 6), "DATE CHECK — WEDNESDAY 25 NOVEMBER 2026 ONLY",
           font=font(11, True), fill=RED)
    d.text((W - 18, y0 + 6), "HOW SURE", font=font(10, True), fill=INK,
           anchor="ra")
    lx = W - 18 - int(text_w(d, "HOW SURE", 10, True)) - 12
    chips = []
    for label, col in CONF_COLORS.items():
        f = font(9, True)
        chips.append((label, col, int(d.textlength(label, font=f)) + 10))
    total_w = sum(w for _, _, w in chips) + 5 * (len(chips) - 1)
    lx -= total_w
    for label, col, w in chips:
        tag(d, lx, y0 + 5, label, col)
        lx += w + 5
    # three subcolumns: 24 NOV / 22 NOV & EARLIER / NOT YET
    col_w = 330
    for i, (day, text) in enumerate(DATE_CHECK):
        cx = 18 + i * (col_w + 6)
        d.text((cx, y0 + 24), day, font=font(10, True), fill=INK)
        para(d, cx, y0 + 37, text, 9, col_w - 8, fill=INK, leading=10)
    # legend meanings + HOW TO READ, bottom lines
    d.text((18, y0 + 68),
           "CONFIRMED 2+ outlets · OFFICIAL the body itself · REPORTED 1 "
           "outlet · CLAIM one side · FORECAST expected",
           font=font(9), fill=MUTED)
    d.text((18, y0 + 80),
           "HOW TO READ — thumbnail: date, 3 leads, 6 big numbers. Full size: "
           "13 picture stories, briefs 14-36 by region, world map, date check.",
           font=font(9), fill=INK)

# =====================================================================
# Assemble + write the poster. Deterministic: fixed palette, fixed
# fonts, fixed layout, PNG written with a fixed timestamp-free encoder
# (Pillow writes no time chunk for PNG by default).
# =====================================================================

def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_masthead(d)
    draw_numbers(d, y0=72)
    draw_region_bar(d, y0=130)
    # hero tier: 3 cards
    hx = [18, 350, 682]
    for i, story in enumerate(HEROES):
        draw_hero_card(d, hx[i], 184, 324, 192, story)
    # picture stories: 2 rows of 5
    px = [18 + i * 199 for i in range(5)]
    for row in range(2):
        for col in range(5):
            story = PICTURES[row * 5 + col]
            draw_pic_card(d, px[col], 382 + row * 150, 190, 146, story)
    # world map
    draw_world_map(d, 18, 684, 988, 110)
    # briefs grouped by region
    draw_briefs(d, 18, 800, 988, 128)
    # footer: date check + how sure + how to read
    draw_footer(d, 934)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    img = build()
    img.save(OUT_PATH, format="PNG", optimize=True)
    data = open(OUT_PATH, "rb").read()
    print("wrote %s (%d bytes) sha256=%s" % (
        OUT_PATH, len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
