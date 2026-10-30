"""Queued XACT instance commands, both pools, holes and 16-bit dispatch.

Default: 1000 trials. The play model exposes both stack arguments as memory
effects so the normal differential comparison checks them along with r3..r10.
"""
from liftcheck.spec import *

FUNCTION = "rage::audXactSound_ProcessCommand"
ADDRESS = 0x821AEAE0
SOURCE = "src/rage/audio/aud_instance_update.cpp"
TRIALS = 1000
RET = None
FP_CONTRACT = "off"

POOL_2000 = 0x825EE658
POOL_4000 = 0x825EE298
NOOPS = (0x2003, 0x200b, 0x4007, 0x400c)
COMMANDS = (*range(0x2002, 0x2012), *range(0x4002, 0x4012),
            0, 1, 0x2001, 0x2012, 0x4001, 0x4012, 0x7fff, 0x8000, 0xffff)
SIGNED_EDGES = (0x80000000, 0x80000001, 0x7fffffff, 0x7fffec77, 0x7fffec78,
                -16777217, -16777216, -5001, -5000, -4999, -1, 0, 1, 16777217)


def play(ctx):
    # Xenon reserves the eight register home slots before stack arguments;
    # the compiled SysV PPC32 lift has its first stack argument at sp+8.
    sp = ctx.m.gpr(1)
    word, byte = (0x54, 0x5f) if ctx.side == "orig" else (8, 15)
    ctx.write(ctx.r(3) + 256, ctx.read(sp + word, 4) + ctx.read(sp + byte, 1))


CALLS = {
    "aud_F098": model(play, args=tuple(f"r{n}" for n in range(3, 11))),
    "aud_F508": stub(ret=1),
    "aud_F5F0": stub(ret="void"),
    "aud_F670": stub(ret="void"),
    "aud_F6F0": stub(ret="void"),
    "audInstance_UpdateParameters": stub(ret="void"),
    "aud_FB50": stub(ret="void"),
    "aud_FC28": stub(ret="void"),
    "aud_FD10": stub(ret="void"),
    "nop_8240E6D0": stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    opcode = rng.choice(COMMANDS)
    command = opcode | (rng.getrandbits(16) << 16)
    params = t.alloc(40, "command payload")
    words = [t.u32() for _ in range(10)]
    for n in range(1, 4):
        words[n] = rng.choice((*SIGNED_EDGES, t.u32())) & 0xffffffff
    for n in (7, 9):
        words[n] = rng.choice((0, 1, 2, 0x100, 0x80000000, 0xffffffff))

    selected = t.alloc(272, "selected instance", ctype="audInstance")
    decoy2000 = t.alloc(272, "other 2000 instance", ctype="audInstance")
    decoy4000 = t.alloc(272, "other 4000 instance", ctype="audInstance")
    count = 16 if opcode < 0x4000 else 240
    index = rng.choice((0, count - 1, rng.randrange(count)))
    words[0] = index
    for slot in range(16):
        t.w32(POOL_2000 + 4 * slot, selected if opcode < 0x4000 and slot == index else decoy2000)
    for slot in range(240):
        t.w32(POOL_4000 + 4 * slot, selected if opcode >= 0x4000 and slot == index else decoy4000)
    # Both the unchanged-group and changed-group paths must still normalize
    # the enable flag, including nonzero values whose low byte is zero.
    t.w32(selected + 8, words[1] if rng.randrange(2) else words[1] ^ 1)
    if opcode in (0x2010, 0x4010):
        words[2] = rng.choice((0, 1, 2, 0x100, 0x80000000, 0xffffffff))
    for n, value in enumerate(words):
        t.w32(params + 4 * n, value)
    # The four empty switch slots must not even read the payload.
    t.args(r3=command, r4=0 if opcode in NOOPS and rng.randrange(2) else params)
