from liftcheck.spec import *
SOURCE = "src/game/player/player_shot_position.cpp"
TRIALS = 512

def position(ctx):
    output, entry = ctx.r(3), ctx.r(4)
    ctx.write(output, ctx.read(entry + 0x170, 16))
    ctx.write(entry + 0xe0, ctx.read(entry + 0x180, 16))
    ctx.write(entry + 0xf0, ctx.read(entry + 0x190, 16))
    ctx.ret(r3=output)

CALLS = {"pongPlayer_ComputeTargetPosition": model(position, args=("r4", "r5"))}

def inputs(t):
    entry = t.alloc(0x1b0, "shot entry")
    values = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
              0x00800000, 0x80800000, 0x3f800000, 0xbf800000,
              0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000]
    for base in [0x170, 0x180, 0x190]:
        for i in range(4):
            t.w32(entry + base + i * 4, t.rng.choice(values))
    t.args(r3=entry, r4=t.rng.choice([0, 1, 2, 255, 256, 0xffffffff]))
