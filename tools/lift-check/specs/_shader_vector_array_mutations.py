"""Only behavioral FAIL counts. Mutate the cached translation unit, never sources."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = (
    ('wrong counter direction', '    ++g_grmShaderFx_boundContext;\n    uint32_t length', '    --g_grmShaderFx_boundContext;\n    uint32_t length'),
    ('lose default array length', '((header >> 2) & 0x3FFFu)', '0u'),
    ('dirty bit off by one', 'uint32_t bit = (handle >> 1) & 0x1FFFFu;\n    uint32_t header', 'uint32_t bit = ((handle >> 1) & 0x1FFFFu) + 1;\n    uint32_t header'),
    ('wrong dirty mask', 'g_shaderParameterDirtyMasks[bit & 7];\n        entry += 2;', 'g_shaderParameterDirtyMasks[7 - (bit & 7)];\n        entry += 2;'),
    ('lose vector source alignment', 'reinterpret_cast<uintptr_t>(values) & ~uintptr_t(15)', 'reinterpret_cast<uintptr_t>(values)'),
    ('truncate vector', 'memcpy(destination, vector, sizeof(vector));', 'memcpy(destination, vector, 12);'),
    ('lose destination alignment', 'reinterpret_cast<uintptr_t>(bank + slot) & ~uintptr_t(15)', 'reinterpret_cast<uintptr_t>(bank + slot)'),
    ('use wrong descriptor', '        entry += 2;\n        uint32_t slot', '        entry += 4;\n        uint32_t slot'),
    ('retain descriptor high bits', 'uint32_t slot = entry[1] & 0xFFFFu;', 'uint32_t slot = entry[1];'),
    ('skip input vector', '        ++values;\n    }\n}', '        values += 2;\n    }\n}'),
)


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/pong_render.cpp').read_text()
    start = source.index('void game_A670(')
    target = source[start:source.index('// @ 0x82154320', start)]
    for name, old, new in CASES:
        assert target.count(old) == 1 and old not in source[:start], name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name('render_shader_set_vector_array.py'),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        detected = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
        if not detected:
            print(output.getvalue())
            return 1
    print(f'Caught {len(CASES)}/{len(CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
