"""Patch cache copies; require behavioral FAIL for every broken matrix lift."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('drop fallback count', '((descriptor[0] >> 2) & 0x3FFFu)', '0u'),
    ('wrong descriptor', '        descriptor += 2;', '        descriptor += 4;'),
    ('wrong format bits', '(descriptor[0] >> 4) & 7', '(descriptor[0] >> 3) & 7'),
    ('retain slot high bits', 'const uint32_t slot = descriptor[1] & 0xFFFFu;', 'const uint32_t slot = descriptor[1];'),
    ('always transpose', 'g_shaderMatrixTransposeMasks[(format + 1) / 4]', 'g_shaderMatrixTransposeMasks[1]'),
    ('wrong mask lane', '~mask[lane]', '~mask[row]'),
    ('drop transposed source', 'matrix[lane][row] & mask[lane]', 'matrix[row][lane] & mask[lane]'),
    ('wrong dirty mask', 'table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];\n        memcpy(reinterpret_cast<void*>', 'table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[7 - (bit & 7)];\n        memcpy(reinterpret_cast<void*>'),
    ('lose source alignment', 'reinterpret_cast<uintptr_t>(matrices) & ~uintptr_t(15)', 'reinterpret_cast<uintptr_t>(matrices)'),
    ('lose output alignment', 'reinterpret_cast<uintptr_t>(bank + slot)\n                                      & ~uintptr_t(15)', 'reinterpret_cast<uintptr_t>(bank + slot)'),
    ('truncate matrix', 'output, sizeof(output));', 'output, 48);'),
    ('wrong input stride', '        matrices += 4;', '        matrices += 3;'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/pong_render.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('render_shader_set_matrix_array.py'),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        first = out.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {first}", flush=True)
        if not caught:
            print(out.getvalue())
            return 1
    print(f'Caught {len(CASES)}/{len(CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
