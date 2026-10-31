"""Full shot child reset, exact scalar writes, flags and retained padding."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_5F70_g"
ADDRESS = 0x821D5F70
SOURCE = "src/game/player/player_shot_reset.cpp"
TRIALS = 256
CALLS = {0x821D51C8: run(args=("r3",), deref={"r3": 0xc0})}
# The full-shot reset only writes f0/f12/f13; this caller keeps zero in f11.

def inputs(t):
    entry = t.alloc(0x180, "shot entry")
    t.args(r3=entry)
