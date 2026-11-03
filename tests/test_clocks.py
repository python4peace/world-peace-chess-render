import unittest
from clocks import GameClock

class ClockTests(unittest.TestCase):
    def test_waiting_does_not_tick(self):
        c=GameClock(300,3); c.charge(100); self.assertEqual(c.remaining['w'],300)
    def test_white_starts(self):
        c=GameClock(300,3); c.start(0); c.charge(2); self.assertEqual(c.remaining,{'w':298,'b':300})
    def test_increment_and_switch(self):
        c=GameClock(300,3); c.start(0); self.assertTrue(c.complete_turn(2)); self.assertEqual(c.remaining['w'],301); self.assertEqual(c.running,'b')
    def test_black_ticks(self):
        c=GameClock(300,3); c.start(0); c.complete_turn(2); c.charge(7); self.assertEqual(c.remaining['b'],295)
    def test_exact_flag(self):
        c=GameClock(1,3); c.start(0); self.assertEqual(c.charge(1),'w'); self.assertIsNone(c.running)
    def test_increment_cannot_revive_flag(self):
        c=GameClock(1,3); c.start(0); self.assertFalse(c.complete_turn(2)); self.assertEqual(c.remaining['w'],0)
    def test_black_flag(self):
        c=GameClock(1,0); c.start(0); c.complete_turn(.2); self.assertEqual(c.charge(2),'b')
    def test_stopped_clock(self):
        c=GameClock(10,0); c.start(0); c.charge(2); c.stop(); c.charge(20); self.assertEqual(c.remaining['w'],8)
    def test_clock_cannot_restart(self):
        c=GameClock(10,0); c.start(0)
        with self.assertRaises(ValueError):c.start(3)
    def test_backwards_time_does_not_add_time(self):
        c=GameClock(10,0); c.start(5); c.charge(4); c.charge(6); self.assertEqual(c.remaining['w'],9)

if __name__=='__main__':unittest.main()
