"""
Dependency-free PNG drawing library for EditEase report figures.

Pure stdlib (zlib + struct). Provides a small raster canvas with rectangles,
lines, arrows and a scalable 5x7 bitmap font, styled in the project's
GitHub-Dark palette. Used by make_figures.py to generate UML/ERD/wireframe
figures without matplotlib/PIL/cairo (none are installable in this env).
"""
import zlib, struct

# ---- GitHub-Dark palette (matches the project design system) ----
BG      = (13, 17, 23)      # canvas background  (#0d1117)
PANEL   = (22, 27, 34)      # box fill           (#161b22)
PANEL2  = (33, 38, 45)      # alt box fill       (#21262d)
BORDER  = (48, 54, 61)      # box border         (#30363d)
INK     = (230, 237, 243)   # primary text       (#e6edf3)
MUTED   = (139, 148, 158)   # secondary text     (#8b949e)
ACCENT  = (88, 166, 255)    # blue               (#58a6ff)
GREEN   = (63, 185, 80)      # (#3fb950)
PURPLE  = (188, 140, 255)    # (#bc8cff)
ORANGE  = (219, 109, 40)     # (#db6d28)
PINK    = (219, 97, 162)     # (#db61a2)


class Canvas:
    def __init__(self, w, h, bg=BG):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def _set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i+3] = bytes(c)

    def fill(self, c):
        self.px = bytearray(bytes(c) * (self.w * self.h))

    def rect(self, x, y, w, h, fill=None, border=None, bw=1):
        if fill is not None:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self._set(xx, yy, fill)
        if border is not None:
            for t in range(bw):
                for xx in range(x, x + w):
                    self._set(xx, y + t, border)
                    self._set(xx, y + h - 1 - t, border)
                for yy in range(y, y + h):
                    self._set(x + t, yy, border)
                    self._set(x + w - 1 - t, yy, border)

    def hline(self, x0, x1, y, c, t=1):
        if x1 < x0: x0, x1 = x1, x0
        for x in range(x0, x1 + 1):
            for dt in range(t):
                self._set(x, y + dt, c)

    def vline(self, x, y0, y1, c, t=1):
        if y1 < y0: y0, y1 = y1, y0
        for y in range(y0, y1 + 1):
            for dt in range(t):
                self._set(x + dt, y, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        # Bresenham with thickness (square nib)
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for ox in range(t):
                for oy in range(t):
                    self._set(x0 + ox, y0 + oy, c)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def arrow(self, x0, y0, x1, y1, c, t=2, head=9):
        self.line(x0, y0, x1, y1, c, t)
        import math
        ang = math.atan2(y1 - y0, x1 - x0)
        for a in (ang + 2.6, ang - 2.6):
            hx = int(x1 - head * math.cos(a)); hy = int(y1 - head * math.sin(a))
            self.line(x1, y1, hx, hy, c, t)

    def text(self, x, y, s, c=INK, scale=2, spacing=1):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT.get(ch.upper(), FONT['?']) if ch != ' ' else FONT[' '])
            for ry, row in enumerate(g):
                for rx, bit in enumerate(row):
                    if bit == '#':
                        for sx in range(scale):
                            for sy in range(scale):
                                self._set(cx + rx*scale + sx, y + ry*scale + sy, c)
            cx += (5 + spacing) * scale
        return cx

    def text_w(self, s, scale=2, spacing=1):
        return len(s) * (5 + spacing) * scale

    def text_center(self, cx, y, s, c=INK, scale=2, spacing=1):
        self.text(cx - self.text_w(s, scale, spacing)//2, y, s, c, scale, spacing)

    def save(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw.extend(self.px[y*self.w*3:(y+1)*self.w*3])
        comp = zlib.compress(bytes(raw), 9)
        def chunk(tag, data):
            return (struct.pack('>I', len(data)) + tag + data +
                    struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))
        png = (b'\x89PNG\r\n\x1a\n'
               + chunk(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0))
               + chunk(b'IDAT', comp)
               + chunk(b'IEND', b''))
        with open(path, 'wb') as f:
            f.write(png)


# ---- 5x7 bitmap font ('#' = on). Authored for the glyphs the figures use. ----
_F = {
' ': ["     "]*7,
'A': [" ### ","#   #","#   #","#####","#   #","#   #","#   #"],
'B': ["#### ","#   #","#   #","#### ","#   #","#   #","#### "],
'C': [" ### ","#   #","#    ","#    ","#    ","#   #"," ### "],
'D': ["###  ","#  # ","#   #","#   #","#   #","#  # ","###  "],
'E': ["#####","#    ","#    ","#### ","#    ","#    ","#####"],
'F': ["#####","#    ","#    ","#### ","#    ","#    ","#    "],
'G': [" ### ","#   #","#    ","# ###","#   #","#   #"," ### "],
'H': ["#   #","#   #","#   #","#####","#   #","#   #","#   #"],
'I': ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","#####"],
'J': ["  ###","   # ","   # ","   # ","#  # ","#  # "," ##  "],
'K': ["#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #"],
'L': ["#    ","#    ","#    ","#    ","#    ","#    ","#####"],
'M': ["#   #","## ##","# # #","#   #","#   #","#   #","#   #"],
'N': ["#   #","##  #","# # #","#  ##","#   #","#   #","#   #"],
'O': [" ### ","#   #","#   #","#   #","#   #","#   #"," ### "],
'P': ["#### ","#   #","#   #","#### ","#    ","#    ","#    "],
'Q': [" ### ","#   #","#   #","#   #","# # #","#  # "," ## #"],
'R': ["#### ","#   #","#   #","#### ","# #  ","#  # ","#   #"],
'S': [" ####","#    ","#    "," ### ","    #","    #","#### "],
'T': ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  "],
'U': ["#   #","#   #","#   #","#   #","#   #","#   #"," ### "],
'V': ["#   #","#   #","#   #","#   #","#   #"," # # ","  #  "],
'W': ["#   #","#   #","#   #","#   #","# # #","## ##","#   #"],
'X': ["#   #","#   #"," # # ","  #  "," # # ","#   #","#   #"],
'Y': ["#   #","#   #"," # # ","  #  ","  #  ","  #  ","  #  "],
'Z': ["#####","    #","   # ","  #  "," #   ","#    ","#####"],
'0': [" ### ","#   #","#  ##","# # #","##  #","#   #"," ### "],
'1': ["  #  "," ##  ","  #  ","  #  ","  #  ","  #  ","#####"],
'2': [" ### ","#   #","    #","   # ","  #  "," #   ","#####"],
'3': ["#####","   # ","  #  ","   # ","    #","#   #"," ### "],
'4': ["   # ","  ## "," # # ","#  # ","#####","   # ","   # "],
'5': ["#####","#    ","#### ","    #","    #","#   #"," ### "],
'6': [" ### ","#    ","#    ","#### ","#   #","#   #"," ### "],
'7': ["#####","    #","   # ","  #  "," #   "," #   "," #   "],
'8': [" ### ","#   #","#   #"," ### ","#   #","#   #"," ### "],
'9': [" ### ","#   #","#   #"," ####","    #","    #"," ### "],
'.': ["     ","     ","     ","     ","     ","  ## ","  ## "],
',': ["     ","     ","     ","     ","  ## ","  #  "," #   "],
':': ["     ","  ## ","  ## ","     ","  ## ","  ## ","     "],
';': ["     ","  ## ","  ## ","     ","  ## ","  #  "," #   "],
'-': ["     ","     ","     ","#####","     ","     ","     "],
'_': ["     ","     ","     ","     ","     ","     ","#####"],
'/': ["    #","    #","   # ","  #  "," #   ","#    ","#    "],
'(': ["  ## "," #   "," #   "," #   "," #   "," #   ","  ## "],
')': [" ##  ","   # ","   # ","   # ","   # ","   # "," ##  "],
'[': [" ### "," #   "," #   "," #   "," #   "," #   "," ### "],
']': [" ### ","   # ","   # ","   # ","   # ","   # "," ### "],
'<': ["   # ","  #  "," #   ","#    "," #   ","  #  ","   # "],
'>': [" #   ","  #  ","   # ","    #","   # ","  #  "," #   "],
'=': ["     ","     ","#####","     ","#####","     ","     "],
'+': ["     ","  #  ","  #  ","#####","  #  ","  #  ","     "],
'?': [" ### ","#   #","    #","   # ","  #  ","     ","  #  "],
'!': ["  #  ","  #  ","  #  ","  #  ","  #  ","     ","  #  "],
'%': ["##  #","##  #","   # ","  #  "," #   ","#  ##","#  ##"],
'&': [" ##  ","#  # ","#  # "," ##  ","#  ##","#  # "," ## #"],
'*': ["     ","# # #"," ### ","#####"," ### ","# # #","     "],
'#': [" # # ","#####"," # # ","#####"," # # ","     ","     "],
"'": ["  #  ","  #  "," #   ","     ","     ","     ","     "],
'"': [" # # "," # # "," # # ","     ","     ","     ","     "],
}
# lowercase: render as scaled-down uppercase forms but keep distinct where easy
_LOWER = {
'a': ["     ","     "," ### ","    #"," ####","#   #"," ####"],
'b': ["#    ","#    ","#### ","#   #","#   #","#   #","#### "],
'c': ["     "," ### ","#    ","#    ","#    "," ### ","     "],
'd': ["    #","    #"," ####","#   #","#   #","#   #"," ####"],
'e': ["     "," ### ","#   #","#####","#    "," ### ","     "],
'f': ["  ## "," #   ","###  "," #   "," #   "," #   "," #   "],
'g': [" ####","#   #","#   #"," ####","    #","#   #"," ### "],
'h': ["#    ","#    ","#### ","#   #","#   #","#   #","#   #"],
'i': ["  #  ","     "," ##  ","  #  ","  #  ","  #  "," ### "],
'j': ["   # ","     ","  ## ","   # ","   # ","#  # "," ##  "],
'k': ["#    ","#    ","#  # ","# #  ","##   ","# #  ","#  # "],
'l': [" ##  ","  #  ","  #  ","  #  ","  #  ","  #  ","  ###"],
'm': ["     ","     ","## # ","# # #","# # #","#   #","#   #"],
'n': ["     ","     ","#### ","#   #","#   #","#   #","#   #"],
'o': ["     "," ### ","#   #","#   #","#   #"," ### ","     "],
'p': ["     ","#### ","#   #","#   #","#### ","#    ","#    "],
'q': ["     "," ####","#   #","#   #"," ####","    #","    #"],
'r': ["     ","     ","# ## ","##   ","#    ","#    ","#    "],
's': ["     "," ####","#    "," ### ","    #","#### ","     "],
't': [" #   "," #   ","###  "," #   "," #   "," #  #","  ## "],
'u': ["     ","     ","#   #","#   #","#   #","#  ##"," ## #"],
'v': ["     ","     ","#   #","#   #","#   #"," # # ","  #  "],
'w': ["     ","     ","#   #","#   #","# # #","# # #"," # # "],
'x': ["     ","     ","#   #"," # # ","  #  "," # # ","#   #"],
'y': ["     ","#   #","#   #"," ####","    #","#   #"," ### "],
'z': ["     ","#####","   # ","  #  "," #   ","#####","     "],
}
FONT = {}
FONT.update(_F)
FONT.update(_LOWER)
