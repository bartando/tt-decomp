"""Both players/layers, all fallback branches, signed counts and nullable slots."""
FUNCTION = 'game_53C8'
ADDRESS = 0x821453C8
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1200


def inputs(t):
    r = t.rng
    shadow = t.alloc(0x470, 'shadow')
    config = t.alloc(0x800, 'config')
    t.w32(shadow + 8, config)
    for i in range(7):
        t.w8(config + 0x110 + i * 0xE0, r.choice([0, 0, 1, 2, 128, 255]))
    for offset in range(0x3E0, 0x400, 4):
        t.w32(shadow + offset, r.choice([0, t.alloc(16, f'texture{offset}')]))
    t.w32(shadow + 0x444, r.choice([-0x80000000, -2, -1, 0, 1, 2, 3, 0x7FFFFFFF]))
    t.w32(shadow + 0x448, r.choice([-1, 0, 1, 2, 0x7FFFFFFF]))
    t.w32(0x825EBA20, r.choice([0, t.alloc(16, 'fallback')]))
    t.args(r3=shadow, r4=r.randrange(2), r5=r.randrange(2))
