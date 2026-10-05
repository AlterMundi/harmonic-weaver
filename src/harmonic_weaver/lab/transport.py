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
        self.loop_end_s = None
        self.epoch = 0

    def boundary(self):
        if self.loop and self.loop_end_s is not None:
            return min(self.duration_s, self.loop_end_s) if self.duration_s > 0 else self.loop_end_s
        return self.duration_s

    def position(self):
        position = self.anchor_position + (self.clock() - self.anchor_clock if self.playing else 0.)
        boundary = self.boundary()
        if boundary > 0 and position >= boundary:
            if self.loop and self.playing:
                loops = int(position / boundary)
                position %= boundary
                self.epoch += loops
            else:
                position = boundary
                if self.playing:
                    self.playing = False
                    self.epoch += 1
            self.anchor_position, self.anchor_clock = position, self.clock()
        return max(0., position)

    def seek(self, position):
        if isinstance(position, bool) or not isinstance(position, (float, int)) or not math.isfinite(position) or position < 0:
            raise ValueError("seek requires a non-negative source time")
        if self.boundary() > 0:
            position = min(position, self.boundary())
        self.anchor_position, self.anchor_clock = float(position), self.clock()
        self.epoch += 1

    def play(self, enabled):
        position = self.position()
        if enabled and self.boundary() > 0 and position >= self.boundary():
            position = 0.
        if self.playing != enabled:
            self.epoch += 1
        self.anchor_position, self.anchor_clock = position, self.clock()
        self.playing = bool(enabled)

    def reset(self, *, duration_s=0., playing=False):
        self.duration_s = duration_s
        self.loop_end_s = None
        self.anchor_position, self.anchor_clock = 0., self.clock()
        self.playing = playing
        self.epoch += 1
