#!/usr/bin/env python3
"""THE WORLD — front page for Saturday 21 November 2026.

A pure-stdlib generator that draws a 1024x1024 newspaper front page
summing up the day's world news. No third-party modules: the picture is
painted pixel by pixel into a bytearray, the letters come from a small
hand-built 5x7 bitmap alphabet, and the PNG bytes are assembled with
struct + zlib. Every run writes identical bytes.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 240, 222)   # warm newsprint cream
NAVY = (18, 35, 70)      # masthead ink
INK = (28, 28, 34)       # body ink
RED = (178, 34, 34)      # date band + kickers
GOLD = (198, 158, 42)    # rules and accents
PURPLE = (88, 48, 130)   # cyclone band
GREEN = (46, 110, 70)    # climate band
SKY = (70, 120, 160)     # storm blue
GREY = (118, 118, 122)   # building grey
CREAM = (250, 244, 228)   # light text on dark bands
DARKRED = (120, 22, 22)


# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is seven rows of five cells; '#' is ink, '.' is blank.
# Shapes drawn from memory of ordinary block capitals.
# v2 audit: 'V' is a sharp chevron converging from row 2 (never a 'U',
# whose sides stay vertical to a flat base); 'K' has no top-right tip
# so its top row cannot read as a 'T' bar; 'Y' keeps wide arms through
# row 2 so it cannot read as 'V'; '5' keeps a clean right stem. The
# rest of A-Z / 0-9 were checked for downscale confusion (M/N, G/C,
# D/O, B/8, I/1, S/5, R/P, O/0) and left as drawn.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#....", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", "#...#", ".#.#.", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "....#", "####."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
}


def text_width(text, scale):
    """Pixel width of `text` drawn at `scale` (one blank column between glyphs)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_words(text, scale, max_width):
    """Greedy word wrap; every returned line fits inside max_width pixels."""
    lines = []
    for chunk in text.split("\n"):
        words = chunk.split(" ")
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if text_width(trial, scale) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


# ------------------------------------------------------------------ canvas
class FrontPage:
    """A 1024x1024 RGB canvas painted with simple filled shapes."""

    def __init__(self):
        self.pixels = bytearray(PAGE_W * PAGE_H * 3)
        for i in range(0, len(self.pixels), 3):
            self.pixels[i] = PAPER[0]
            self.pixels[i + 1] = PAPER[1]
            self.pixels[i + 2] = PAPER[2]

    # -- primitives ------------------------------------------------------
    def dot(self, x, y, colour):
        if 0 <= x < PAGE_W and 0 <= y < PAGE_H:
            off = (y * PAGE_W + x) * 3
            self.pixels[off] = colour[0]
            self.pixels[off + 1] = colour[1]
            self.pixels[off + 2] = colour[2]

    def block(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(PAGE_W, x + w)
        y1 = min(PAGE_H, y + h)
        for yy in range(y0, y1):
            base = (yy * PAGE_W + x0) * 3
            for xx in range(x0, x1):
                off = base + (xx - x0) * 3
                self.pixels[off] = colour[0]
                self.pixels[off + 1] = colour[1]
                self.pixels[off + 2] = colour[2]

    def outline(self, x, y, w, h, colour, thick=2):
        self.block(x, y, w, thick, colour)
        self.block(x, y + h - thick, w, thick, colour)
        self.block(x, y, thick, h, colour)
        self.block(x + w - thick, y, thick, h, colour)

    def disc(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            span = math.isqrt(max(0, r * r - dy * dy))
            for dx in range(-span, span + 1):
                self.dot(cx + dx, cy + dy, colour)

    def ring(self, cx, cy, r, thick, colour, background):
        self.disc(cx, cy, r, colour)
        self.disc(cx, cy, max(0, r - thick), background)

    def stroke(self, x0, y0, x1, y1, colour, width=1):
        """Bresenham line, thickened by stamping small discs along it."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            if width <= 1:
                self.dot(x, y, colour)
            else:
                self.disc(x, y, width // 2, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_poly(self, points, colour):
        """Scanline fill of a polygon given as a list of (x, y) corners."""
        if len(points) < 3:
            return
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        for yy in range(top, bottom + 1):
            crossings = []
            for i in range(len(points)):
                ax, ay = points[i]
                bx, by = points[(i + 1) % len(points)]
                if ay == by:
                    continue
                if (ay <= yy < by) or (by <= yy < ay):
                    t = (yy - ay) / (by - ay)
                    crossings.append(ax + t * (bx - ax))
            crossings.sort()
            for j in range(0, len(crossings) - 1, 2):
                xa = int(math.ceil(crossings[j]))
                xb = int(math.floor(crossings[j + 1]))
                for xx in range(xa, xb + 1):
                    self.dot(xx, yy, colour)

    def star(self, cx, cy, outer, inner, colour):
        points = []
        for k in range(10):
            radius = outer if k % 2 == 0 else inner
            angle = -math.pi / 2 + k * math.pi / 5
            points.append(
                (int(cx + radius * math.cos(angle)), int(cy + radius * math.sin(angle)))
            )
        self.fill_poly(points, colour)

    def burst(self, cx, cy, outer, inner, colour):
        """Jagged explosion: a 12-point star with uneven spikes."""
        points = []
        for k in range(24):
            radius = outer if k % 2 == 0 else inner
            angle = -math.pi / 2 + k * math.pi / 12
            wobble = 1.0 if k % 4 else 0.82
            points.append(
                (
                    int(cx + radius * wobble * math.cos(angle)),
                    int(cy + radius * wobble * math.sin(angle)),
                )
            )
        self.fill_poly(points, colour)

    # -- text ------------------------------------------------------------
    def glyph(self, x, y, char, scale, colour):
        rows = GLYPHS.get(char.upper(), GLYPHS["?"])
        for row_i, row in enumerate(rows):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    self.block(
                        x + col_i * scale, y + row_i * scale, scale, scale, colour
                    )

    def write(self, x, y, text, scale, colour, align="left"):
        """Draw one line; returns its pixel width. Asserts it stays on-page."""
        width = text_width(text, scale)
        if align == "center":
            x = x - width // 2
        elif align == "right":
            x = x - width
        assert x >= 0 and x + width <= PAGE_W, "text overflows page: %r" % text
        cursor = x
        for char in text:
            self.glyph(cursor, y, char, scale, colour)
            cursor += 6 * scale
        return width

    def paragraph(self, x, y, text, scale, colour, max_width, gap=5):
        lines = wrap_words(text, scale, max_width)
        for line in lines:
            self.write(x, y, line, scale, colour)
            y += 7 * scale + gap
        return y


# ------------------------------------------------------------- pictograms
def lead_art(page):
    """Polish flag, missile and burst for the lead panel."""
    # Polish flag: white over red (v2: enlarged to fill the lead panel).
    page.block(48, 196, 168, 48, CREAM)
    page.block(48, 244, 168, 48, RED)
    page.outline(48, 196, 168, 96, INK, 3)
    page.write(48, 300, "POLAND", 2, INK)
    # Missile body, horizontal, nose to the right.
    page.block(240, 236, 96, 14, NAVY)
    page.fill_poly([(336, 230), (368, 243), (336, 256)], NAVY)
    page.fill_poly([(248, 250), (232, 266), (256, 250)], NAVY)
    page.fill_poly([(248, 240), (232, 224), (256, 240)], NAVY)
    page.block(226, 238, 14, 10, GOLD)
    # Flame trail behind the missile.
    page.burst(230, 243, 12, 5, GOLD)
    page.burst(230, 243, 8, 3, RED)
    # Explosion burst and a ring of small gold stars (NATO allies).
    # v2: burst enlarged and moved up to close the empty gap under the flag.
    page.burst(290, 345, 54, 22, GOLD)
    page.burst(290, 345, 36, 14, RED)
    page.burst(290, 345, 19, 8, CREAM)
    for k in range(8):
        angle = k * math.pi / 4
        sx = int(290 + 76 * math.cos(angle))
        sy = int(345 + 76 * math.sin(angle))
        page.star(sx, sy, 10, 4, GOLD)


def strike_art(page, x, y, w, h):
    """Broken city blocks under a burst for the Kryvyi Rih panel."""
    page.block(x, y, w, h, NAVY)
    page.burst(x + w // 2, y + 22, 18, 8, GOLD)
    page.burst(x + w // 2, y + 22, 11, 5, RED)
    base = y + h - 6
    heights = (22, 32, 16, 26, 20, 30)
    for i, tall in enumerate(heights):
        page.block(x + 18 + i * 44, base - tall, 34, tall, GREY)
    page.stroke(x + 62, base - 32, x + 82, base - 12, RED, 3)
    page.stroke(x + 238, base - 30, x + 256, base - 10, RED, 3)
    page.block(x, base, w, 6, GOLD)


def cyclone_art(page, x, y, w, h):
    """Spiral storm with rain for the cyclone panel."""
    page.block(x, y, w, h, PURPLE)
    cx, cy = x + w // 2, y + h // 2
    for r in (24, 18, 12, 6):
        page.ring(cx, cy, r, 4, CREAM, PURPLE)
    page.disc(cx, cy, 4, GOLD)
    for rx, ry in ((20, 38), (w - 24, 38), (40, 8), (w - 44, 8)):
        page.stroke(x + rx, y + ry, x + rx - 4, y + ry + 8, SKY, 3)
    page.stroke(x + 16, y + h - 8, x + w - 16, y + h - 8, GOLD, 3)


def cyber_art(page, x, y, w, h):
    """Cracked shield over payment cards for the cyberattack panel."""
    page.block(x, y, w, h, NAVY)
    shield = [
        (x + w // 2 - 28, y + 6),
        (x + w // 2 + 28, y + 6),
        (x + w // 2 + 28, y + 28),
        (x + w // 2, y + 46),
        (x + w // 2 - 28, y + 28),
    ]
    page.fill_poly(shield, GOLD)
    page.stroke(x + w // 2 - 4, y + 10, x + w // 2 + 6, y + 22, NAVY, 3)
    page.stroke(x + w // 2 + 6, y + 22, x + w // 2 - 2, y + 32, NAVY, 3)
    page.stroke(x + w // 2 - 2, y + 32, x + w // 2 + 4, y + 42, NAVY, 3)
    page.block(x + 16, y + h - 16, 62, 10, CREAM)
    page.block(x + w - 78, y + h - 16, 62, 10, RED)
    page.block(x + 24, y + h - 13, 20, 4, NAVY)
    page.block(x + w - 70, y + h - 13, 20, 4, CREAM)


def cop_art(page, x, y, w, h):
    """Globe with sun rays for the climate-talks panel."""
    page.block(x, y, w, h, GREEN)
    cx, cy = x + 58, y + h // 2
    for k in range(8):
        angle = k * math.pi / 4
        x0 = int(cx + 21 * math.cos(angle))
        y0 = int(cy + 21 * math.sin(angle))
        x1 = int(cx + 25 * math.cos(angle))
        y1 = int(cy + 25 * math.sin(angle))
        page.stroke(x0, y0, x1, y1, GOLD, 3)
    page.disc(cx, cy, 20, SKY)
    page.disc(cx - 7, cy - 6, 6, GREEN)
    page.disc(cx + 7, cy + 7, 7, GREEN)
    page.disc(cx + 8, cy - 8, 4, GREEN)
    page.ring(cx, cy, 20, 3, CREAM, SKY)
    # v2: band names the venue (COP31 - TURKEY) instead of repeating the
    # headline below it ("COP31 ENTERS FINAL STAGE"). The bitmap font has
    # no middle-dot glyph, so the separator is a hyphen.
    page.write(x + 112, y + 14, "COP31 - TURKEY", 3, CREAM)


def car_art(page, x, y, w, h):
    """Sleek sedan silhouette for the Elantra debut panel."""
    page.block(x, y, w, h, RED)
    body = [
        (x + 28, y + 40),
        (x + 42, y + 28),
        (x + 108, y + 20),
        (x + 168, y + 22),
        (x + 238, y + 30),
        (x + 266, y + 40),
    ]
    page.fill_poly(body, NAVY)
    page.fill_poly(
        [(x + 94, y + 20), (x + 116, y + 10), (x + 166, y + 10),
         (x + 182, y + 20)],
        SKY,
    )
    page.disc(x + 84, y + 38, 12, INK)
    page.disc(x + 84, y + 38, 6, GREY)
    page.disc(x + 220, y + 38, 12, INK)
    page.disc(x + 220, y + 38, 6, GREY)
    page.write(x + 300, y + 4, "2027", 4, CREAM)
    page.write(x + 300, y + 36, "NEW", 2, GOLD)


# -------------------------------------------------------------- page build
def story_panel(page, x, y, w, h, art, kicker, headline, body):
    """One grid panel: pictogram band, kicker, headline, body text.

    The cursor walks down the panel and the final line must land inside
    the frame; a body that does not fit fails loudly instead of spilling.
    """
    page.outline(x, y, w, h, INK, 2)
    art(page, x + 2, y + 2, w - 4, 50)
    cursor = y + 58
    page.write(x + 12, cursor, kicker, 2, RED)
    cursor += 19
    for line in headline:
        page.write(x + 12, cursor, line, 3, INK)
        cursor += 24
    cursor += 4
    end = page.paragraph(x + 12, cursor, body, 2, INK, w - 24, gap=3)
    assert end <= y + h - 6, "panel text overflows: %r" % kicker


def build_page():
    page = FrontPage()

    # -- masthead: deep navy band with the cream wordmark ----------------
    page.block(0, 0, PAGE_W, 104, NAVY)
    # v2: small texts sit at y=82 so their 14px glyphs (82..95) clear the
    # gold rule at y=100; at y=88 their bottom rows were sliced by it.
    page.write(40, 82, "No. 325", 2, GOLD)
    page.write(984, 82, "PRICE: FREE", 2, GOLD, align="right")
    page.write(PAGE_W // 2, 14, "THE WORLD", 10, CREAM, align="center")
    page.block(0, 100, PAGE_W, 4, GOLD)

    # -- red date band ---------------------------------------------------
    page.block(0, 104, PAGE_W, 54, RED)
    page.write(512, 122, "SATURDAY 21 NOVEMBER 2026", 4, CREAM, align="center")
    page.block(836, 114, 132, 34, CREAM)
    page.write(902, 122, "EXTRA", 4, RED, align="center")

    # -- lead story ------------------------------------------------------
    page.outline(16, 168, 992, 302, INK, 3)
    lead_art(page)
    page.write(380, 186, "WAR IN EUROPE", 2, RED)
    page.write(380, 210, "RUSSIAN MISSILES", 5, INK)
    page.write(380, 252, "CROSS INTO POLAND", 5, INK)
    page.block(380, 300, 560, 4, GOLD)
    page.paragraph(
        380,
        316,
        "Russian missiles and drones cross into Polish territory, and a "
        "detonation triggers an airspace-incursion probe. NATO allies "
        "respond as the alarm is raised over the breach.",
        2,
        INK,
        600,
        gap=5,
    )

    # -- grid row one: three panels --------------------------------------
    story_panel(
        page, 16, 482, 318, 244, strike_art, "UKRAINE",
        ["KRYVYI RIH", "STRIKE KILLS 2,", "WOUNDS 42"],
        "A Russian strike on Kryvyi Rih kills two people and injures 42, "
        "including four children.",
    )
    story_panel(
        page, 353, 482, 318, 244, cyclone_art, "WEATHER",
        ["CYCLONE AKVAN", "CROSSES ODISHA", "COAST"],
        "Cyclone Akvan crosses the Odisha and Andhra coast near Gopalpur, "
        "with strong winds and heavy rain.",
    )
    story_panel(
        page, 690, 482, 318, 244, cyber_art, "TECH",
        ["BANKS HIT IN", "CYBERATTACK"],
        "JPMorgan, Visa and Mastercard report a cyberattack on "
        "third-party vendors. Core networks are unaffected.",
    )

    # -- grid row two: two wider panels ----------------------------------
    story_panel(
        page, 16, 738, 484, 204, cop_art, "CLIMATE",
        ["COP31 ENTERS", "FINAL STAGE"],
        "UN climate talks in Turkey reach their crucial final phase. "
        "Fossil-fuel use and climate finance are the sticking points.",
    )
    story_panel(
        page, 524, 738, 484, 204, car_art, "MOTORS",
        ["2027 ELANTRA", "DEBUTS"],
        "Hyundai unveils the eighth-generation Elantra at the Los Angeles "
        "Auto Show, with a redesigned exterior and hybrid options.",
    )

    # -- bottom strip: seventh story -------------------------------------
    page.block(16, 952, 992, 48, NAVY)
    page.write(512, 958, "ESTONIA TO CLOSE RUSSIA BORDER CROSSINGS", 3, CREAM,
               align="center")
    page.write(512, 982, "FROM 1 DECEMBER", 2, GOLD, align="center")

    # -- footer ----------------------------------------------------------
    page.block(16, 1006, 992, 2, INK)
    page.write(
        PAGE_W // 2, 1009,
        "THE WORLD - SATURDAY 21 NOVEMBER 2026 - SIX STORIES, ONE PAGE",
        2, INK, align="center",
    )
    return page


# --------------------------------------------------------------- PNG out
def png_bytes(page):
    raw = bytearray()
    for yy in range(PAGE_H):
        raw.append(0)  # filter: none
        start = yy * PAGE_W * 3
        raw.extend(page.pixels[start:start + PAGE_W * 3])

    def chunk(tag, data):
        crc = zlib.crc32(tag)
        crc = zlib.crc32(data, crc)
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", PAGE_W, PAGE_H, 8, 2, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out.extend(chunk(b"IHDR", ihdr))
    out.extend(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    out.extend(chunk(b"IEND", b""))
    return bytes(out)


def main():
    page = build_page()
    data = png_bytes(page)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    with open(path, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o644)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
