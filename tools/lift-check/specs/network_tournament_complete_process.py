"""0x823BC8C8: conditional input state and a sign-extended tournament byte."""
from liftcheck.spec import *

FUNCTION = 'TournamentCompleteMessage::Process'
ADDRESS = 0x823BC8C8
SOURCE = 'src/game/network/pong_network.cpp'
TRIALS = 500
EXTERNS = {'g_loop_obj_ptr': 0x825EAB30, 'g_input_obj_ptr': 0x825EAB28,
           'g_szTopSpin': 0x8206CB54}
PAYLOAD = b''


def post(c):
    assert c.r(5) == 1 and c.in_stack(c.r(6))
    assert c.read(c.r(6), 4) == PAYLOAD


CALLS = {0x8240E6D0: stub(ret='void', args=('r3',)),
         'PostGameMessage': model(post, args=('r3', 'r4', 'r5', 'r6'))}


def inputs(t):
    global PAYLOAD
    r = t.rng
    msg = t.alloc(0x10, 'message')
    byte = r.choice([0, 1, 127, 128, 255, r.randrange(256)])
    t.w8(msg+8, byte)
    PAYLOAD = (byte if byte < 128 else byte - 256).to_bytes(4, 'big', signed=True)
    loop = t.alloc(0x250, 'loop')
    input_obj = t.alloc(0x40, 'input')
    t.w8(loop+0x242, r.choice([0, 0, 1, 128]))
    t.w32(loop+12, r.choice([0, 8, 9, 0xFFFFFFFF]))
    t.w32(t.sym('g_loop_obj_ptr'), loop)
    t.w32(t.sym('g_input_obj_ptr'), input_obj)
    t.args(r3=msg)
