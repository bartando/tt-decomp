"""0x8218EE10: press routing, callback reloads, and replay power charging."""
from liftcheck.spec import *

FUNCTION = "pongPlayer::CheckButtonInput"
ADDRESS = 0x8218EE10
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
EXTERNS = {"g_loop_obj_ptr": 0x825EAB30, "g_input_obj_ptr": 0x825EAB28,
           "g_pPlayerDataTable": 0x8271A31C, "g_pReplayStateData": 0x8271A2EC,
           "g_kPowerBlend": 0x825C2EA0}
ENABLED = 0
PRESSED = 0
DELTA = 0.0
INPUT = REPLAY = PLAYER = 0
AFTER_QUERY = AFTER_PRESS = 0


def query(c):
    c.write(0x825EAB28, INPUT.to_bytes(4, 'big'))
    c.write(0x8271A2EC, REPLAY.to_bytes(4, 'big'))
    c.write(PLAYER + 0x1D0, AFTER_QUERY.to_bytes(4, 'big'))
    c.ret(r3=ENABLED)


def pressed(c):
    c.write(PLAYER + 0x1D0, AFTER_PRESS.to_bytes(4, 'big'))
    c.ret(r3=PRESSED)


def axis(c):
    c.ret(f1=DELTA)


CALLS = {
    "player.vfn_1": model(query, args=('r3',)),
    "CheckButtonPressed": model(pressed, args=('r3',)),
    "pongPlayer_0508_g": model(axis, args=('r3', 'r4')),
    "PostGameMessage": stub(ret='void', args=('r3', 'r4', 'r5', 'r6')),
}


def inputs(t):
    global ENABLED, PRESSED, DELTA, INPUT, REPLAY, PLAYER, AFTER_QUERY, AFTER_PRESS
    r = t.rng
    PLAYER = t.alloc(0x200, 'player')
    t.w32(PLAYER, t.vtable('player', 2))
    # Known game input slots; include masks that truncate to zero.
    slot = r.choice([0, 0, 0, 1, 1, 2, 7, 8])
    AFTER_QUERY = r.choice([slot, slot, 0, 1])
    AFTER_PRESS = r.choice([AFTER_QUERY, AFTER_QUERY, 0, 1])
    t.w32(PLAYER + 0x1D0, slot)
    clock = t.alloc(0x20, 'loop')
    t.w32(clock + 12, r.choice([0, 0, 8, 10]))
    t.w32(t.sym('g_loop_obj_ptr'), clock)
    original = t.alloc(0x100, 'originalInput')
    INPUT = t.alloc(0x100, 'reloadedInput')
    for obj in [original, INPUT]:
        for i in range(32):
            t.w32(obj + 4*i, r.choice([0, 1, 1, 1, 2, 0xFFFFFFFF]))
    # Make every gate pass frequently enough to exercise all branches.
    if t.index % 2 == 0:
        t.w32(original + 4*(slot+14), 1)
        t.w32(INPUT + 56, 1)
    t.w32(t.sym('g_input_obj_ptr'), original)
    REPLAY = t.alloc(0x68D10, 'reloadedReplay')
    old_replay = t.alloc(0x68D10, 'originalReplay')
    t.w32(t.sym('g_pReplayStateData'), old_replay)
    t.w8(REPLAY + 0x68CFA, r.choice([0, 1, 1, 0x80]))
    t.w32(REPLAY + 0x68D00, r.choice([0, 1, 8]))
    table = t.alloc(4*0x328, 'records')
    for i in range(16):
        t.w32(table + 4*(i+1), r.randrange(1, 4))
    for i in range(1, 4):
        buttons = t.alloc(0x20, f'buttons{i}')
        t.w32(table + i*0x328 + 12 + 0x31C, buttons)
    t.w32(t.sym('g_pPlayerDataTable'), table)
    t.f32(t.sym('g_kPowerBlend'), r.choice([3., 0.25, -2., 1.125]))
    # The retail fcmpu compares zero and adds one; its f1 entry is unused.
    t.f32(0x8202D108, 1.)
    t.f32(0x8202D110, 0.)
    ENABLED = r.choice([0, 1, 1, 0x100, 0x101, 0xFFFFFFFF])
    PRESSED = r.randrange(2)
    DELTA = r.choice([-1., -0.375, -0., 0., 0.125, 1.])
    t.args(r3=PLAYER)
