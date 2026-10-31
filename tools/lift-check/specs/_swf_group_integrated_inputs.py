"""A live page-group scope and free member nodes for end-to-end Flash setters."""
import zlib
from liftcheck.spec import *


def setup(t):
    r = t.rng
    group = t.alloc(0xB0, 'group', fill='zero')
    scope = t.alloc(0x30, 'scope', fill='zero')
    t.w32(group + 0x9C, t.alloc(16, 'globalObject'))
    t.w32(group + 0xA0, scope)
    t.w32(group + 0xA4, t.alloc(16, 'auxiliary'))
    t.w8(group + 0xA8, r.choice([0, 1, 0x80]))
    # Active groups already have their globals selected.
    for addr, off in [(0x82604C50, 0x24), (0x82604C5C, 0x38), (0x82604C54, 0x4C),
                      (0x82604C60, 0x60), (0x82604C58, 0x74), (0x82602844, 0x88)]:
        t.w32(addr, group + off)
    t.w32(0x8260282C, scope)
    nodes = [t.alloc(20, 'freeNode') for _ in range(3)]
    for i, node in enumerate(nodes):
        t.w32(node, nodes[i + 1] if i < 2 else 0)
    t.w16(group + 0x4C + 6, 3)
    t.w32(group + 0x4C + 12, nodes[0])
    t.w8(0x826066C8, 1)
    for i in range(13):
        t.w32(0x82604CE8 + 4 * i, 0xF0000000 + i)
    return group


class RunKey(run):
    """Execute unchanged; normalize only the trace's string pointer to its text.
    Nested original callees have no DWARF in the HUD caller's translation unit.
    """
    def __init__(self, key_reg, **kwargs):
        super().__init__(**kwargs)
        self.key_reg = key_reg

    def handle(self, ctx):
        key = bytearray()
        while (c := ctx.read(ctx.r(self.key_reg) + len(key), 1)) != b'\0':
            key.extend(c)
        ctx.rec.gpr[self.key_reg - 3] = zlib.crc32(key)
        return 'run'


CALLS = {
    'swfSelectPageGroup': run(args=('r3', 'r4')),
    'swfFindMember': RunKey(4, args=('r3', 'r4')),
    'swfSetMember': RunKey(4, args=('r3', 'r4', 'r5'), deref={'r5': 8}),
    'swfHashMemberName': RunKey(3, args=('r3',)),
}
