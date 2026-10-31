"""Find/create numeric member, retained scope and late active-flag cleanup.
Dictionary callbacks can change the scope global and the group's active byte.
No ignored memory; the array-pool slot must survive cleanup.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'SinglesNetworkClient_BindEntry'
ADDRESS = 0x823F9318
SOURCE = 'src/rage/swf_page_group.cpp'
TRIALS = 1400
state = {}


def select(ctx):
    ctx.write(0x8260282C, struct.pack('>I', state['scope']))


def find(ctx):
    side = ctx.side
    i = state[side]
    state[side] += 1
    ctx.write(0x8260282C, struct.pack('>I', state['otherScope']))
    ctx.write(state['group'] + 0xA8, bytes([state['lateActive']]))
    ctx.ret(r3=state['entry'] if i or state['found'] else 0)


CALLS = {
    'swfSelectPageGroup': model(select, args=('r3', 'r4')),
    'swfFindMember': model(find, args=('r3', 'r4'), preserves=('r4',)),
    'swfSetMember': stub(ret='void', args=('r3', 'r4', 'r5'), deref={'r5': 8}),
}


def inputs(t):
    r = t.rng
    group = t.alloc(0xC0, 'group')
    t.w8(group + 0xA8, r.choice([0, 1, 0x80]))
    state.update(group=group, scope=t.alloc(0x30, 'scope'), otherScope=t.alloc(0x30, 'otherScope'),
                 entry=t.alloc(16, 'entry') if t.index % 5 else 0,
                 found=t.index % 2, lateActive=r.choice([0, 0, 1, 0x80]), orig=0, lift=0)
    for addr in (0x82604C50, 0x82604C5C, 0x82604C54, 0x82604C60,
                 0x82604C58, 0x82602844, 0x82602818, 0x8260282C, 0x82602834):
        t.w32(addr, t.u32())
    name = r.choice([b'possible', b'completed', b'time_low', b'arrow_direction'])
    t.args(r3=group, r4=t.alloc(len(name) + 1, 'key', fill=name + b'\0'))
