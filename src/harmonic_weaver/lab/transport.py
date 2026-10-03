"""Source-time transport independent of inference duration and the audio clock."""
from __future__ import annotations

import math
import time


class Transport:
    def __init__(self, *, clock=time.monotonic):
        self.clock = clock
        self.anchor_clock = clock()
        self.anchor_position = 0.
        self.duration_s = 0.
        self.playing = False
        self.loop = True
        self.epoch = 0

    def position(self):
        position = self.anchor_position + (self.clock() - self.anchor_clock if self.playing else 0.)
        if self.duration_s > 0 and position >= self.duration_s:
            if self.loop and self.playing:
                loops = int(position / self.duration_s)
                position %= self.duration_s
                self.epoch += loops
            else:
                position = self.duration_s
                if self.playing:
                    self.playing = False
                    self.epoch += 1
            self.anchor_position, self.anchor_clock = position, self.clock()
        return max(0., position)

    def seek(self, position):
        if isinstance(position, bool) or not isinstance(position, (float, int)) or not math.isfinite(position) or position < 0:
            raise ValueError("seek requires a non-negative source time")
        if self.duration_s > 0:
            position = min(position, self.duration_s)
        self.anchor_position, self.anchor_clock = float(position), self.clock()
        self.epoch += 1

    def play(self, enabled):
        position = self.position()
        if enabled and self.duration_s > 0 and position >= self.duration_s:
            position = 0.
        if self.playing != enabled:
            self.epoch += 1
        self.anchor_position, self.anchor_clock = position, self.clock()
        self.playing = bool(enabled)

    def reset(self, *, duration_s=0., playing=False):
        self.duration_s = duration_s
        self.anchor_position, self.anchor_clock = 0., self.clock()
        self.playing = playing
        self.epoch += 1
