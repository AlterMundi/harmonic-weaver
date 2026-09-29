"""Aperiodic, acceleration-triggered envelopes; no metronome or repeat timer."""
from collections import deque


class Pluck:
    def __init__(self):
        self.armed = True
        self.events = deque(maxlen=32)
        self.count = 0

    def observe(self, acceleration, threshold, now, attack, tail):
        # Hysteresis: a sustained acceleration is ONE impulse, not one per frame.
        if acceleration < threshold * .5:
            self.armed = True
        if self.armed and acceleration >= threshold:
            self.events.append((now, attack, tail, min(1., acceleration)))
            self.count += 1
            self.armed = False

    def gain(self, now, speed):
        self.events = deque((e for e in self.events if now-e[0] < e[1]+e[2]), maxlen=32)
        total = 0.
        for start, attack, tail, strength in self.events:
            age = max(0., now-start)
            if age < attack:
                x = age / attack
                env = x*x*(3-2*x)
            else:
                x = min(1., (age-attack)/tail)
                env = (1-x)**2
            total += strength * env
        # A finite residual tail survives a stop; speed shapes its loudness.
        return min(1., total) * (.2 + .8 * min(1., speed))
