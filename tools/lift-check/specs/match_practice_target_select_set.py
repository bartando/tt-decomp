"""Global target selection, changed/unchanged sets, capacity fallback and grid data.
Execute the original shuffle, next and grid callees on both sides; their lifts
also have dedicated specs. The incoming object argument is deliberately null.
"""
from liftcheck.spec import *

FUNCTION = 'gmPracticeTarget_SelectSet'
ADDRESS = 0x821137B0
SOURCE = 'src/game/match/pong_match.cpp'
TRIALS = 1400
CALLS = {
    'gmPracticeTargetWordArray_Shuffle': run(args=('r3',)),
    'gmPracticeTargetWordArray_Next': run(args=('r3',)),
    'gmPracticeTarget_LayOutTableGrid': run(args=()),
}


def inputs(t):
    r = t.rng
    target = t.alloc(0x80, 'target')
    t.w32(0x826063A8, target)
    cap = r.randrange(1, 9)
    count = r.randrange(1, cap + 1)
    array = t.alloc(0x20, 'wordArray')
    words = t.alloc(cap * 4, 'words')
    previousOrder = list(range(cap))
    r.shuffle(previousOrder)
    for i in range(cap):
        t.w32(words + 4 * i, previousOrder[i])
    t.w32(array, words)
    t.w32(array + 4, count)
    t.w32(array + 8, cap)
    t.w32(array + 12, r.randrange(count))
    t.w8(array + 16, r.choice([0, 0x80, 0x40, 0xC0]))
    t.w32(target + 0x18, array)
    sets = t.alloc(3 * 8, 'sets')
    t.w32(target + 0x48, sets)
    chosen = r.randrange(3)
    t.w32(target + 0x44, r.choice([chosen, (chosen + 1) % 3]))
    for i in range(3):
        t.w32(sets + i * 8, r.choice([-1, 1, cap]))
        definitions = t.alloc((cap + 2) * 0x44, 'definitions' + str(i))
        t.w32(sets + i * 8 + 4, definitions)
        for j in range(cap + 2):
            for k in range(9):
                t.w32(definitions + j * 0x44 + 4 * k, r.choice([-1, 0, 1, 2, t.u32()]))
            t.floats(definitions + j * 0x44 + 0x24, 8, -2, 2)
    table = t.alloc(0x30, 'table')
    t.w32(0x8271A304, table)
    t.wf32(table + 0x10, r.uniform(.1, 4))
    t.wf32(table + 0x18, r.uniform(.1, 6))
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())
    t.args(r3=0, r4=chosen, r5=t.u32(), r6=t.u32())
