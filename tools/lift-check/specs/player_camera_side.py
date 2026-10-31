"""0x821E7CC0: mode-selected camera index, checked node cast and side flag."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_7CC0_g"
ADDRESS = 0x821E7CC0
SOURCE = "src/game/player/player_camera_side.cpp"
TRIALS = 1000


def cast(ctx):
    ctx.ret(r3=ctx.r(3) if ctx.rng.choice([False, True]) else 0)


CALLS = {0x82101700: model(cast, args=("r3",))}


def inputs(t):
    rng = t.rng
    settings = t.alloc(0x40, "settings")
    t.w32(settings + 0x38, rng.choice([0, 1, 1, 2, 0x101, -1]))
    t.w32(settings + 0x3C, rng.choice([0, 1, 1, 2, 0x101, -1]))
    t.w32(t.sym("g_input_obj_ptr"), settings)
    court = t.alloc(0x40, "court")
    nodes = t.alloc(8 * 4, "cameraNodes")
    for i in range(8):
        record = t.alloc(0x40, f"record{i}")
        t.w32(record + 0x30, rng.choice([0, 0, 1, 2, 0x100, 0x80000000, 0xFFFFFFFF]))
        t.w32(nodes + 4 * i, rng.choice([0, record, record]))
    t.w32(court + 0x2C, nodes)
    t.w32(0x8271A314, court)
    camera = t.alloc(0x10, "camera")
    t.w32(camera + 0x08, rng.choice([-1, 0, 1, 2, 3]))
    t.w32(camera + 0x0C, rng.choice([-1, 4, 5, 6, 7]))
    t.args(r3=camera)
