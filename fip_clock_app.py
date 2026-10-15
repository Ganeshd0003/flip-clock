"""
Flip Clock (Hours : Minutes)  -  big rounded cards, black screen
- Works fully offline (only Python's built-in tkinter + your system clock)
- Updates exactly on the system clock's second boundary, so it never drifts

Keys:
    F  or  F11  -> toggle fullscreen
    H           -> toggle 12-hour / 24-hour format
    Esc         -> exit fullscreen / quit
"""

import time
import tkinter as tk
import tkinter.font as tkfont

BG = "#000000"        # screen background
CARD = "#111111"      # card colour
LINE = "#1b1b1b"      # split line across the screen
FG = "#B8B8B8"        # number colour (use "#FFFFFF" for pure white)
LABEL = "#BDB5AD"     # AM / PM colour

# condensed bold fonts, first one installed on your PC is used
FONT_CANDIDATES = [
    "Bahnschrift SemiBold Condensed", "Bahnschrift Condensed", "Bebas Neue",
    "Oswald", "Roboto Condensed", "Impact",
    "Arial Narrow", "Arial", "Helvetica", "DejaVu Sans",
]
CAP_RATIO = {          # digit height / font size
    "Bahnschrift SemiBold Condensed": 0.70, "Bahnschrift Condensed": 0.70,
    "Bebas Neue": 0.70, "Oswald": 0.81, "Impact": 0.79,
    "Roboto Condensed": 0.71, "Arial Narrow": 0.72,
}
# fonts drawn at normal weight (slimmer strokes); others fall back to bold
NO_BOLD = {"Bahnschrift SemiBold Condensed", "Bahnschrift Condensed", "Impact",
           "Bebas Neue", "Oswald", "Roboto Condensed"}

GAP = 6               # thickness of the split line (px)


def pick_font(root):
    available = {f.lower(): f for f in tkfont.families(root)}
    for name in FONT_CANDIDATES:
        if name.lower() in available:
            return available[name.lower()]
    return "TkDefaultFont"


class FlipCard(tk.Frame):
    """One big rounded flip card (top half + bottom half) with flip animation."""

    def __init__(self, parent, w, h, font, px, cap, descent, lfont=None):
        super().__init__(parent, bg=BG)
        self.w, self.h = w, h
        self.half = (h - GAP) // 2
        self.r = int(w * 0.11)
        self.font, self.px, self.cap, self.descent = font, px, cap, descent
        self.lfont = lfont
        self.label_text = ""
        self.value = None
        self._job = None
        self._flap = None

        self.top = tk.Canvas(self, width=w, height=self.half, bg=BG, highlightthickness=0)
        self.sep = tk.Frame(self, width=w, height=GAP, bg=LINE)
        self.bot = tk.Canvas(self, width=w, height=self.half, bg=BG, highlightthickness=0)
        self.top.pack()
        self.sep.pack()
        self.bot.pack()

    # ---------- drawing ----------
    def _round_rect(self, c, x1, y1, x2, y2, r):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
               x1 + r, y1]
        c.create_polygon(pts, smooth=True, fill=CARD, outline="")

    def _paint(self, c, val, top, yoff=0):
        """Draw one half of the card. yoff lets a flap canvas act as a window."""
        c.delete("all")
        r = self.r
        if top:
            self._round_rect(c, 0, yoff, self.w, yoff + self.half + 2 * r, r)
            hinge = yoff + self.half + GAP / 2
        else:
            self._round_rect(c, 0, yoff - 2 * r, self.w, yoff + self.half, r)
            hinge = yoff - GAP / 2
        # digits are centred vertically on the hinge (split line)
        y = hinge + self.cap * self.px / 2 + self.descent
        c.create_text(self.w / 2, y, text=val, anchor="s", fill=FG, font=self.font)
        if not top and self.label_text and self.lfont:
            c.create_text(self.w * 0.075, yoff + self.half - self.h * 0.10,
                          text=self.label_text, anchor="sw", fill=LABEL, font=self.lfont)

    def _paint_both(self, val):
        self._paint(self.top, val, True)
        self._paint(self.bot, val, False)

    def _kill_flap(self):
        if self._flap is not None:
            self._flap.destroy()
            self._flap = None

    def _cancel(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        self._kill_flap()

    # ---------- public ----------
    def set(self, val, animate=True, label=None):
        if label is not None:
            self.label_text = label
        if val == self.value:
            return
        self._cancel()
        old, self.value = self.value, val
        if old is None or not animate:
            self._paint_both(val)
            return
        self._old, self._new = old, val
        self._t0 = time.time()
        self._phase = 0
        self._step()

    def _step(self, dur=0.5):
        p = min(1.0, (time.time() - self._t0) / dur)
        half = self.half
        if p < 0.5:
            if self._phase != 1:                       # old top folds down
                self._phase = 1
                self._paint(self.top, self._new, True)
                self._paint(self.bot, self._old, False)
                self._kill_flap()
                self._flap = tk.Canvas(self.top, width=self.w, height=half,
                                       bg=BG, highlightthickness=0)
            fh = max(1, int((1 - 2 * p) * half))
            self._flap.config(height=fh)
            self._flap.place(x=0, y=half - fh)
            self._paint(self._flap, self._old, True, yoff=-(half - fh))
        elif p < 1.0:
            if self._phase != 2:                       # new bottom opens
                self._phase = 2
                self._kill_flap()
                self._flap = tk.Canvas(self.bot, width=self.w, height=half,
                                       bg=BG, highlightthickness=0)
            gh = max(1, int((2 * p - 1) * half))
            self._flap.config(height=gh)
            self._flap.place(x=0, y=0)
            self._paint(self._flap, self._new, False, yoff=0)
        if p >= 1.0:
            self._kill_flap()
            self._paint_both(self._new)
            self._job = None
        else:
            self._job = self.after(16, self._step)


class FlipClock:
    def __init__(self, root):
        self.root = root
        self.use_24h = False
        self.container = None
        self.line = None
        self.hour = self.minute = None
        self._resize_job = None
        self.family = pick_font(root)

        root.title("Flip Clock")
        root.configure(bg=BG)
        root.geometry("1000x560")
        root.minsize(480, 280)

        root.bind("<Configure>", self._on_resize)
        for k in ("<f>", "<F>", "<F11>"):
            root.bind(k, lambda e: self.toggle_fullscreen())
        for k in ("<h>", "<H>"):
            root.bind(k, lambda e: self.toggle_format())
        root.bind("<Escape>", self._escape)

        root.attributes("-fullscreen", True)
        root.update_idletasks()
        self._build()
        self._tick()

    # ---------- window controls ----------
    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def _escape(self, _=None):
        if self.root.attributes("-fullscreen"):
            self.root.attributes("-fullscreen", False)
        else:
            self.root.destroy()

    def toggle_format(self):
        self.use_24h = not self.use_24h
        self._update(animate=False)

    # ---------- layout ----------
    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(150, self._build)

    def _build(self):
        self._resize_job = None
        for card in (self.hour, self.minute):
            if card:
                card._cancel()
        W = max(self.root.winfo_width(), 480)
        H = max(self.root.winfo_height(), 280)

        margin = W * 0.045
        gapx = int(W * 0.014)
        card_w = int((W - 2 * margin - gapx) / 2)
        card_h = int(min(H * 0.75, card_w * 1.0))
        card_h -= card_h % 2

        # font that fits the card
        cap = CAP_RATIO.get(self.family, 0.72)
        px = int(0.63 * card_h / cap)
        weight = "normal" if self.family in NO_BOLD else "bold"
        font = tkfont.Font(family=self.family, size=-px, weight=weight)
        while px > 20 and font.measure("00") > 0.88 * card_w:
            px -= 4
            font.configure(size=-px)
        descent = font.metrics("descent")
        lfont = tkfont.Font(family=self.family, size=-max(12, int(card_h * 0.09)),
                            weight="bold")
        self._fonts = (font, lfont)   # keep references alive

        # full-width split line (behind the cards)
        if self.line:
            self.line.destroy()
        self.line = tk.Frame(self.root, bg=LINE, height=GAP)
        self.line.place(relx=0, rely=0.5, relwidth=1, anchor="w")

        if self.container:
            self.container.destroy()
        self.container = tk.Frame(self.root, bg=BG)
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        self.hour = FlipCard(self.container, card_w, card_h, font, px, cap, descent, lfont)
        self.minute = FlipCard(self.container, card_w, card_h, font, px, cap, descent, lfont)
        self.hour.grid(row=0, column=0, padx=(0, gapx // 2))
        self.minute.grid(row=0, column=1, padx=(gapx // 2, 0))

        self._update(animate=False)

    # ---------- time ----------
    def _time_strings(self):
        t = time.localtime()
        if self.use_24h:
            return f"{t.tm_hour:02d}", f"{t.tm_min:02d}", ""
        suffix = "AM" if t.tm_hour < 12 else "PM"
        return str(t.tm_hour % 12 or 12), f"{t.tm_min:02d}", suffix

    def _update(self, animate=True):
        if not self.hour:
            return
        hh, mm, suffix = self._time_strings()
        label_changed = self.hour.label_text != suffix
        self.hour.set(hh, animate, label=suffix)
        self.minute.set(mm, animate)
        if label_changed and self.hour._job is None and self.hour.value is not None:
            self.hour._paint(self.hour.bot, self.hour.value, False)   # redraw AM/PM

    def _tick(self):
        self._update(animate=True)
        # wait exactly until the next second boundary of the system clock (no drift)
        delay_ms = int((1.0 - (time.time() % 1.0)) * 1000) + 5
        self.root.after(delay_ms, self._tick)


if __name__ == "__main__":
    root = tk.Tk()
    FlipClock(root)
    root.mainloop()