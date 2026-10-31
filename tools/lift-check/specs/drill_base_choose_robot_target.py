"""Easy centered shots, repeat probability and nonrepeating random target selection."""
import zlib
from liftcheck.spec import *

FUNCTION = "pongTrainingDrill::ChooseRobotTarget"
ADDRESS = 0x8210D8B0
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1200
EXTERNS = {"rage_debugLog": 0x8240E6D0}


def _log(ctx):
    text = bytearray()
    while (c := ctx.read(ctx.r(3) + len(text), 1)) != b'\0':
        text.extend(c)
    ctx.rec.gpr[0] = zlib.crc32(text)


CALLS = {"rage_debugLog": model(_log)}


def inputs(t):
    r = t.rng
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())
    config = t.alloc(0x80, 'config')
    easy = r.randrange(0, 5)
    t.w32(config + 0x3C, easy)
    t.wf32(config + 0x40, r.choice([0.0, 0.5, 1.0, -1.0, 2.0, float('nan')]))
    for i in range(3):
        t.wf32(config + 0x48 + i * 8, r.choice([0.0, -0.0, -1.0, 1.0, float('nan')]))
        t.wf32(config + 0x4C + i * 8, r.uniform(-2, 2))
    drill = t.alloc(0x40, 'drill')
    t.w32(drill + 0x20, config)
    t.w32(drill + 4, r.choice([easy - 1, easy, easy + 1, easy + 5]))
    t.w32(drill + 0x1C, r.choice([-1, 0, 1, 2]))
    t.args(r3=drill, r4=t.alloc(0x110, 'event'))
