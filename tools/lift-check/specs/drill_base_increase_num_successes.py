"""pongTrainingDrill::IncreaseNumSuccesses (slot 26, 0x8210D400): capped at TotalNumTries,
shown on the HUD, message 0x5008 "i" 1."""
import zlib

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::IncreaseNumSuccesses"
# other files mark string addresses on rage_debugLog calls, which makes its marker ambiguous
ADDRESS = 0x8210D400
SOURCE = "src/game/drill/pong_drill.cpp"
EXTERNS = {"rage_debugLog": 0x8240E6D0}


def _post_fmt(ctx):
    # "i" is too short for lift-check to compare as text and the variadic r6 isn't
    # compared: record a checksum of both in place of the pointer (r5).
    ctx.rec.gpr[5 - 3] = zlib.crc32(bytes(ctx.read(ctx.r(5), 2)) + ctx.r(6).to_bytes(4, "big"))


def _debug_log(ctx):
    # The message is longer than the 64 bytes lift-check reads as text: compare a
    # checksum of it instead of the pointer.
    text, a = b"", ctx.r(3)
    while (c := bytes(ctx.read(a + len(text), 1))) != b"\0":
        text += c
    ctx.rec.gpr[0] = zlib.crc32(text)


CALLS = {
    0x8240E6D0: model(_debug_log),                  # rage_debugLog
    "PostPageGroupMessageFmt": model(_post_fmt),
}


def inputs(t):
    rng = t.rng
    t.w32(0x82606614, t.alloc(0xC0, "hud"))
    config = t.alloc(0x80, "config")
    total = rng.randrange(0, 12)
    t.w32(config + 0x10, total)
    drill = t.alloc(0x40, "drill")
    t.w32(drill + 0x20, config)
    t.w32(drill + 0x08, total + rng.randrange(-4, 2))
    t.args(r3=drill, r4=rng.choice([1, 1, 2, 0, -1]))
