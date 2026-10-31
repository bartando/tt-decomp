"""0x8220E1B0: special/type precedence, four direction columns and default."""
from liftcheck.spec import *

FUNCTION = "util_E1B0"
ADDRESS = 0x8220E1B0
SOURCE = "src/game/player/player_spin_helpers.cpp"
TRIALS = 1000


def inputs(t):
    settings = t.alloc(0x40, "spinSettings", floats=[(0x10, 12)])
    t.floats(settings + 0x10, 12, -100, 100)
    direction = [0, 1, 2, 3, 4, 0xFFFFFFFF][t.index % 6]
    shot_type = [10, 9, 8, 0, 11, -1][(t.index // 6) % 6]
    special = [0, 1, 2, 255][(t.index // 36) % 4]
    t.args(r3=settings, r4=direction, r5=shot_type, r6=special)
