#!/usr/bin/env python3
"""news-image-20261123, variant 3.

A vertical timeline of Monday 23 November 2026: six moments of the
day's world news, hung in order on one central spine, with a short
"also today" strip at the foot. Pure standard library, deterministic,
no network. Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png).

Stories, all verified against reporting dated 23 November 2026:
 1. COP31 ends in Antalya with no deal (Le Monde / AP).
 2. Trump says it will be "very hard" to work with Schumer (Reuters).
 3. South Korea's education minister Choi Kyo-jin resigns over the
    AI-cheating exam chaos (Reuters, 23 Nov 2026).
 4. Ian "Molly" Meldrum dies in Melbourne, aged 83, at 5.30am
    (AAP / Mediaweek, 23 Nov 2026).
 5. A lion is loose in Sariyer, Istanbul; thermal cameras join the
    hunt (Al Jazeera, 23 Nov 2026).
 6. India close in on a Test win in Wellington: NZ 157-4 at lunch
    on day five after India's record 720-9 (Reuters, 23 Nov 2026).
Also today: the US holds its first deep-sea mining lease sale off
American Samoa (Pacific Islands News Association, 23 Nov 2026).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# Palette: warm paper, ink navy, brick red, teal, ochre.
PAPER = (250, 244, 232)
CARD = (255, 252, 246)
INK = (24, 32, 54)
RED = (178, 44, 36)
TEAL = (15, 110, 110)
OCHRE = (196, 128, 28)
MUTED = (96, 96, 104)
LINE = (200, 188, 168)
SPINE = (178, 44, 36)

# ------------------------------------------------------------------ font ---
# 5x7 bitmap font, each glyph is 7 rows of 5 bits (MSB first).
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
}

CHAR_W = 6  # glyph advance: 5 pixels + 1 spacing


def text_width(text, scale):
    return len(text) * CHAR_W * scale


# ---------------------------------------------------------------- canvas ---
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            row = bytes(color) * w
            self.px[base:base + 3 * w] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thick) ** 2 <= d2 <= (r + thick) ** 2:
                    self.set(xx, yy, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch, FONT[" "])
        for r, bits in enumerate(rows):
            for c in range(5):
                if bits & (1 << (4 - c)):
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        for i, ch in enumerate(s):
            self.glyph(x + i * CHAR_W * scale, y, ch, scale, color)

    def text_centred(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)


# -------------------------------------------------------------------- png ---
def png_bytes(canvas):
    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

# ------------------------------------------------------------- pictograms ---
def icon_globe(c, ox, oy):
    c.ring(ox + 20, oy + 20, 17, TEAL, 2)
    c.hline(ox + 5, oy + 20, 30, TEAL, 2)
    c.hline(ox + 9, oy + 11, 22, TEAL, 2)
    c.hline(ox + 9, oy + 29, 22, TEAL, 2)
    c.line(ox + 20, oy + 4, ox + 20, oy + 36, TEAL)
    c.line(ox + 8, oy + 10, ox + 32, oy + 30, TEAL)


def icon_capitol(c, ox, oy):
    c.line(ox + 20, oy + 4, ox + 4, oy + 16, INK)
    c.line(ox + 20, oy + 4, ox + 36, oy + 16, INK)
    c.hline(ox + 4, oy + 16, 32, INK, 2)
    for cx in (8, 15, 22, 29):
        c.vline(ox + cx, oy + 19, 12, INK, 2)
    c.hline(ox + 4, oy + 32, 32, INK, 3)
    c.disc(ox + 20, oy + 12, 3, RED)


def icon_exam(c, ox, oy):
    c.rect(ox + 8, oy + 3, 24, 34, CARD)
    c.hline(ox + 8, oy + 3, 24, INK, 2)
    c.hline(ox + 8, oy + 35, 24, INK, 2)
    c.vline(ox + 8, oy + 3, 34, INK, 2)
    c.vline(ox + 30, oy + 3, 34, INK, 2)
    c.hline(ox + 13, oy + 10, 14, MUTED, 2)
    c.hline(ox + 13, oy + 16, 14, MUTED, 2)
    c.line(ox + 13, oy + 26, ox + 18, oy + 31, RED)
    c.line(ox + 18, oy + 31, ox + 28, oy + 21, RED)


def icon_music(c, ox, oy):
    c.disc(ox + 13, oy + 30, 6, INK)
    c.vline(ox + 19, oy + 6, 25, INK, 3)
    c.hline(ox + 19, oy + 6, 12, INK, 3)
    c.disc(ox + 31, oy + 26, 5, RED)
    c.vline(ox + 36, oy + 4, 23, RED, 2)


def icon_lion(c, ox, oy):
    c.disc(ox + 20, oy + 21, 16, OCHRE)
    c.disc(ox + 8, oy + 8, 5, OCHRE)
    c.disc(ox + 32, oy + 8, 5, OCHRE)
    c.disc(ox + 20, oy + 21, 11, (232, 196, 138))
    c.disc(ox + 15, oy + 18, 2, INK)
    c.disc(ox + 25, oy + 18, 2, INK)
    c.line(ox + 20, oy + 23, ox + 16, oy + 27, INK)
    c.line(ox + 20, oy + 23, ox + 24, oy + 27, INK)
    c.hline(ox + 16, oy + 27, 8, INK, 2)


def icon_cricket(c, ox, oy):
    c.vline(ox + 8, oy + 6, 28, INK, 2)
    c.vline(ox + 14, oy + 6, 28, INK, 2)
    c.vline(ox + 20, oy + 6, 28, INK, 2)
    c.line(ox + 28, oy + 34, ox + 36, oy + 10, INK)
    c.line(ox + 30, oy + 34, ox + 38, oy + 12, INK)
    c.disc(ox + 33, oy + 6, 4, RED)


# ---------------------------------------------------------------- stories ---
# (number, tag, accent, icon, headline lines, body lines)
STORIES = [
    (1, "CLIMATE", RED, icon_globe,
     ["COP31 ENDS WITH", "NO DEAL"],
     ["ANTALYA TALKS END WITH NO",
      "PACT. FOSSIL FUELS LEFT OUT."]),
    (2, "USA", TEAL, icon_capitol,
     ["TRUMP WARNS", "ON SCHUMER"],
     ["IT WILL BE VERY HARD TO WORK",
      "WITH HIM AS SENATE LEADER."]),
    (3, "SOUTH KOREA", OCHRE, icon_exam,
     ["KOREA MINISTER", "QUITS"],
     ["CHOI KYO-JIN QUITS OVER AI",
      "CHEATING CHAOS IN EXAMS."]),
    (4, "AUSTRALIA", RED, icon_music,
     ["MOLLY MELDRUM", "DIES AT 83"],
     ["COUNTDOWN HOST DIES AT 5.30AM",
      "IN MELBOURNE, AGED 83."]),
    (5, "TURKIYE", TEAL, icon_lion,
     ["LION LOOSE IN", "ISTANBUL"],
     ["THERMAL CAMERAS HUNT THE LION",
      "SEEN IN SARIYER, ISTANBUL."]),
    (6, "SPORT", OCHRE, icon_cricket,
     ["INDIA 720: NZ", "157-4 AT LUNCH"],
     ["DAY FIVE IN WELLINGTON. INDIA",
      "NEED SIX WICKETS TO WIN."]),
]

CARD_H = 116
CARD_GAP = 8
TOP = 168
CARD_W = 440
LEFT_X = 36
RIGHT_X = 548
SPINE_X = 512


def draw_card(c, x, y, story):
    num, tag, accent, icon, head, body = story
    # Card body and frame.
    c.rect(x, y, CARD_W, CARD_H, CARD)
    c.rect(x, y, CARD_W, 4, accent)
    c.hline(x, y + CARD_H - 1, CARD_W, LINE, 1)
    c.vline(x, y, CARD_H, LINE, 1)
    c.vline(x + CARD_W - 1, y, CARD_H, LINE, 1)
    # Tag and icon.
    c.text(x + 14, y + 12, tag, 2, accent)
    icon(c, x + CARD_W - 54, y + 8)
    # Headline, two lines, scale 3.
    hy = y + 36
    for line in head:
        c.text(x + 14, hy, line, 3, INK)
        hy += 23
    # Body, two lines, scale 2.
    by = y + 84
    for line in body:
        c.text(x + 14, by, line, 2, (52, 52, 62))
        by += 16


def build():
    c = Canvas(W, H, PAPER)
    # Header.
    c.text_centred(512, 26, "THE WORLD IN ONE DAY", 2, RED)
    c.text_centred(512, 54, "MONDAY 23 NOVEMBER 2026", 5, INK)
    c.hline(112, 116, 800, INK, 3)
    c.hline(112, 122, 800, RED, 2)
    c.text_centred(512, 134, "SIX MOMENTS ON ONE TIMELINE", 2, MUTED)
    # Cards, alternating sides down the page.
    for i, story in enumerate(STORIES):
        y = TOP + i * (CARD_H + CARD_GAP)
        x = LEFT_X if i % 2 == 0 else RIGHT_X
        draw_card(c, x, y, story)
    # Spine, connectors and numbered nodes.
    c.vline(SPINE_X - 2, TOP + 20, 6 * CARD_H + 5 * CARD_GAP - 40, SPINE, 4)
    for i, story in enumerate(STORIES):
        y = TOP + i * (CARD_H + CARD_GAP)
        cy = y + CARD_H // 2
        if i % 2 == 0:
            c.hline(LEFT_X + CARD_W, cy - 2, SPINE_X - 17 - (LEFT_X + CARD_W), SPINE, 4)
        else:
            c.hline(SPINE_X + 17, cy - 2, RIGHT_X - (SPINE_X + 17), SPINE, 4)
        c.disc(SPINE_X, cy, 17, SPINE)
        c.ring(SPINE_X, cy, 17, PAPER, 2)
        c.text(SPINE_X - 6, cy - 7, str(story[0]), 2, PAPER)
    # Foot strip: one more story, then the sources line.
    c.hline(36, 918, 952, INK, 2)
    c.text_centred(512, 932,
                   "ALSO TODAY: FIRST US DEEP-SEA MINING LEASE SALE OFF AMERICAN SAMOA",
                   2, INK)
    c.text_centred(512, 962,
                   "AS REPORTED ON 23 NOVEMBER 2026 - SOURCES: REUTERS, AP, AL JAZEERA, AAP",
                   2, MUTED)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes(build()))
    print("wrote", path)


if __name__ == "__main__":
    main()
