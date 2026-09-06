"""Illustrative periodic motion derived solely from a typed BPM value, not ECG."""
import math
import time
import tkinter as tk
from .nlp import normalize


def parse_bpm(text):
    try:
        value = float(normalize(str(text)))
    except (ValueError, TypeError):
        return None
    return value if math.isfinite(value) and value.is_integer() and 20 <= value <= 250 else None


def pulse_points(bpm, width, height, phase=0, seconds=4):
    """Generic smooth oscillation: bpm/60 cycles per second. No P/QRS/T morphology."""
    if bpm is None:
        return []
    points = []
    for pixel in range(0, max(2, int(width)), 2):
        t = pixel / max(1, width-1) * seconds + phase
        y = height / 2 - height * .29 * math.sin(2 * math.pi * bpm / 60 * t)
        points.extend((pixel, y))
    return points


class PulseChart(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=112, background='#f7fafb', highlightthickness=0)
        self.bpm = None
        self.running = True
        self.timer = None
        self.origin = time.monotonic()
        self.paused_phase = 0
        self.bind('<Configure>', lambda event: self.draw())
        self.bind('<Destroy>', self.stop)
        self.tick()

    def set_bpm(self, text):
        self.bpm = parse_bpm(text)
        self.origin = time.monotonic()
        self.paused_phase = 0
        self.draw()

    def draw(self):
        self.delete('all')
        width, height = max(self.winfo_width(), 200), 92
        for fraction in (.25, .5, .75):
            self.create_line(0, height*fraction, width, height*fraction, fill='#e6edef')
        for second in range(5):
            x = 8 + second*(width-16)/4
            self.create_text(x, 103, text=str(second), fill='#84929f', font=('Segoe UI', 8))
        self.create_text(width/2, 12, text='4 seconds · simulated' if self.bpm else 'BPM →',
                         fill='#84929f', font=('Segoe UI', 8))
        if self.bpm is not None:
            phase = time.monotonic()-self.origin if self.running else self.paused_phase
            self.create_line(*pulse_points(self.bpm, width, height, phase), fill='#157d85', width=2)

    def tick(self):
        if self.winfo_exists():
            if self.running:
                self.draw()
            self.timer = self.after(80, self.tick)

    def toggle(self):
        if self.running:
            self.paused_phase = time.monotonic()-self.origin
        else:
            self.origin = time.monotonic()-self.paused_phase
        self.running = not self.running
        self.draw()
        return self.running

    def stop(self, event=None):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
