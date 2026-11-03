import time

class GameClock:
    """Monotonic, server-side Fischer clock; callers serialize access."""
    def __init__(self, seconds, increment):
        self.remaining = {'w': float(seconds), 'b': float(seconds)}
        self.increment = float(increment)
        self.running = None
        self.stamp = None
        self.flagged = None

    def start(self, now=None):
        if self.stamp is not None:
            raise ValueError('Clock already started')
        self.stamp = time.monotonic() if now is None else now
        self.running = 'w'

    def charge(self, now=None):
        if self.running is None:
            return self.flagged
        now = time.monotonic() if now is None else now
        elapsed = max(0.0, now - self.stamp)
        self.stamp = max(self.stamp, now)
        side = self.running
        self.remaining[side] = max(0.0, self.remaining[side] - elapsed)
        if self.remaining[side] <= 0:
            self.flagged = side
            self.running = None
        return self.flagged

    def complete_turn(self, now=None):
        if self.charge(now) is not None or self.running is None:
            return False
        side = self.running
        self.remaining[side] += self.increment
        self.running = 'b' if side == 'w' else 'w'
        return True

    def stop(self):
        self.running = None
