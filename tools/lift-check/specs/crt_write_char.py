"""CRT character output: buffered, flush success/failure, and count-only paths."""
from liftcheck.spec import model

FUNCTION = "crtWriteChar"
ADDRESS = 0x824347A0
SOURCE = "src/crt/printf.cpp"
TRIALS = 1200


def flush(ctx):
    # Exercise failure and non--1 results independently of the character.
    ctx.ret(r3=ctx.rng.choice([-1, 0, 1, 255, -2]))


CALLS = {"crtFlushChar": model(flush)}


def inputs(t):
    rng = t.rng
    output = t.alloc(32, "outputAndGuards")
    stream = t.alloc(32, "file")
    count = t.alloc(12, "countAndGuards") + 4
    t.w32(stream, output + 8)
    t.w32(stream + 4, rng.choice([0, 1, 2, -1, -2, 0x80000000, 0x7fffffff]))
    t.w32(stream + 8, rng.choice([0, output + 8]))
    t.w32(stream + 12, rng.getrandbits(32))
    t.w32(count, rng.choice([0, 1, -1, 0x7fffffff, 0x80000000, rng.getrandbits(32)]))
    t.args(r3=rng.choice([0, 1, 127, 128, 255, 256, -1, rng.getrandbits(32)]),
           r4=stream, r5=count)
