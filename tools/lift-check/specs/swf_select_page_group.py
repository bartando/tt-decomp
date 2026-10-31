"""Pool bindings, active-group fast path and low-byte globals selector."""
FUNCTION = 'swfSelectPageGroup'
ADDRESS = 0x823F9040
SOURCE = 'src/rage/swf_page_group.cpp'
TRIALS = 1200


def inputs(t):
    group = t.alloc(0xC0, 'group')
    t.w8(group + 0xA8, t.rng.choice([0, 0, 1, 2, 0x80]))
    for off in (0x9C, 0xA0, 0xA4):
        t.w32(group + off, t.alloc(0x20, 'scope'))
    for addr in (0x82604C50, 0x82604C5C, 0x82604C54, 0x82604C60,
                 0x82604C58, 0x82602844, 0x82602818, 0x8260282C, 0x82602834):
        t.w32(addr, t.u32())
    t.args(r3=group, r4=t.rng.choice([0, 1, 2, 0x80, 0x100, 0x101, t.u32()]))
