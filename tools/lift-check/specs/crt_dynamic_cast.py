"""MSVC RTTI entry: SI search, MI/VI dispatch, complete/virtual adjustment, bad_cast."""
from liftcheck.spec import model, stub

FUNCTION = "RTDynamicCast"
ADDRESS = 0x82430978
SOURCE = "src/crt/rtti.cpp"
TRIALS = 1200


def find_target(ctx):
    # Return a descriptor selected by the input builder, independently of arguments.
    ctx.ret(r3=int.from_bytes(ctx.read(0x825D0000, 4), 'big'))


def construct_bad_cast(ctx):
    ctx.write(ctx.r(3), bytes.fromhex('821014f812345678'))
    ctx.ret(r3=ctx.r(3))


CALLS = {
    0x824305D0: model(find_target, args=('r3', 'r4', 'r5', 'r6', 'r7')),
    0x82430768: model(find_target, args=('r3', 'r4', 'r5', 'r6', 'r7')),
    0x82430418: model(construct_bad_cast, args=('r3', 'r4')),
    0x82435A00: stub(ret=0, args=('r3', 'r4'), deref={'r3': 8}),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(1024, 'completeObject') + 256
    locator = t.alloc(20, 'completeObjectLocator')
    vtable = t.alloc(8, 'vtable') + 4
    hierarchy = t.alloc(16, 'hierarchy')
    target = t.alloc(64, 'targetType', fill=b'\0' * 8 + b'.?AVTarget@@\0')
    source = t.alloc(64, 'sourceType', fill=b'\0' * 8 + b'.?AVSource@@\0')
    same_name = t.alloc(64, 'sameNameType', fill=b'\0' * 8 + b'.?AVTarget@@\0')
    other = t.alloc(64, 'otherType', fill=b'\0' * 8 + rng.choice([b'.?AVTargets@@\0', b'.?AVTarge@@\0', b'.?AVtarget@@\0', b'\0']))
    offset = rng.choice([0, 4, 16, 32, 64])
    cd_offset = rng.choice([0, 4, 8, 12])
    cd_value = rng.choice([-32, -16, 0, 16, 32]) if cd_offset else 0
    complete = obj - offset + cd_value
    t.w32(obj, vtable)
    t.w32(vtable - 4, locator)
    t.w32(locator + 4, offset)
    t.w32(locator + 8, cd_offset)
    if cd_offset:
        t.w32(obj - cd_offset, cd_value)
    t.w32(locator + 16, hierarchy)
    flags = rng.choice([0, 0, 0, 1, 3, 5, 7])
    t.w32(hierarchy + 4, flags)
    count = rng.choice([0, 1, 2, 3, 6])
    entries = t.alloc(4 * max(1, count), 'baseClassArray')
    t.w32(hierarchy + 8, count)
    t.w32(hierarchy + 12, entries)
    candidates = []
    for i in range(max(1, count)):
        base = t.alloc(24, f'baseDescriptor{i}')
        t.w32(entries + 4 * i, base)
        t.w32(base, rng.choice([target, same_name, other]))
        t.w32(base + 8, rng.choice([-64, -4, 0, 4, 48, 128]))
        pdisp = rng.choice([-1, -4, 128, 160])
        t.w32(base + 12, pdisp)
        t.w32(base + 16, 4 * i)
        t.w32(base + 20, rng.choice([0, 1, 2, 3, 4, 6]))
        candidates.append(base)
        if pdisp >= 0:
            # Keep displacement tables distinct from the object's vfptr/CD slot.
            table = t.alloc(32, f'vbtable{i}')
            t.w32(complete + pdisp, table)
            for j in range(8):
                t.w32(table + 4 * j, rng.choice([-32, 0, 16, 48]))
    # Complete-object pdisp slots can coincide; last table still contains all entries.
    result = rng.choice([0, *candidates])
    t.w32(0x825D0000, result)
    t.args(r3=rng.choice([0, obj, obj, obj, obj]),
           r4=rng.choice([-16, 0, 4, 32]), r5=source, r6=target,
           r7=rng.choice([0, 0, 1, -1]))
