"""pongPlayer_TossServeBall: float/VMX math, a virtual call and two direct calls.

The original takes 1/t with vrefp plus a Newton-Raphson step on the vector
unit; the lift divides. lift-check runs vrefp exactly, so the two agree to a
few ulps, hence FTOL.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongPlayer_TossServeBall"
ADDRESS = 0x821934A0
SOURCE = "src/game/player/pong_player.cpp"
FTOL = 1e-5

# game_D1C0(&hitPoint, swingAnim) writes the hit point: the default stub fills
# non-const pointer arguments into the stack, so nothing to say here. The
# impulse handed to phSimulator_CBB8_g lives on the stack too; lift-check
# compares what a const pointer argument points at, member by member.


def inputs(t):
    rng = t.rng
    player = t.alloc(0x200, "player", fill="zero")
    creature = t.alloc(0x100, "creature", fill="zero")
    blender = t.alloc(0x100, "blender", fill="zero")
    swing_anim = t.alloc(0x40, "swingAnim")
    t.w32(player + 0x1C4, creature)
    t.w32(creature + 0xBC, blender)
    t.w32(blender + 0x80, swing_anim)

    ball = t.alloc(0xE0, "ball", ctype="pongBallBody")
    t.w32(ball + 0x00, t.vtable("ball"))
    t.wf32(ball + 0x64, rng.uniform(0.001, 0.1))                 # mass
    t.floats(ball + 0xD0, 4, -3.0, 3.0)                          # position (+ w lane)
    t.args(r3=player, r4=ball, f1=rng.uniform(0.15, 2.0))        # flightTime
