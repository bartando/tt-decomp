"""Behavioral mutation proof. Run from the checkout root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ambient_matrix_array_mutations.py

Only function-scoped build-cache copies are changed. Only exit 1 with FAIL
counts; build errors, exceptions, unsupported instructions and timeouts do not.
Each spec defaults to 1000 trials. Mutations use 160 trials and seed 1.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ('mat44_compose_affine_in_place', 'src/rage/math/mat44.cpp',
     'void mat44ComposeAffineInPlace(', [
         ('omit composition', '    float rows[4][4], right[4][4], result[4][4];',
          '    return;\n    float rows[4][4], right[4][4], result[4][4];'),
         ('omit early translation store', '    std::memcpy(out + 12, translation, 16);',
          '    /* early store lost */'),
         ('omit homogeneous mask', '(translation[lane] & g_affineXYZMask[lane]) | g_affineHomogeneousW[lane]',
          'translation[lane]'),
         ('drop translation product', '(row == 3 ? 4u : 3u)', '3u'),
         ('transpose transform', 'right[k][col]', 'right[col][k]'),
         ('replace packed x-to-w with w', '&rows[row][0], 4', '&rows[row][3], 4'),
         ('retain denormal operands', 'flushComposeVmx(rows[row][k])', 'rows[row][k]'),
         ('round each dot product early',
          'static_cast<double>(flushComposeVmx(rows[row][k])) * flushComposeVmx(right[k][col])',
          'static_cast<float>(flushComposeVmx(rows[row][k]) * flushComposeVmx(right[k][col]))'),
         ('omit third basis row', '    std::memcpy(out + 8, result[2], 16);', '    /* lost row */'),
     ]),
    ('grm_shader_parameter_set_float_array', 'src/rage/rage_grm.cpp',
     'void grmShaderParameter_SetFloatArray(', [
         ('drop descriptor default length', 'count : ((entry[0] >> 2) & 0x3FFFu)', 'count : 0'),
         ('wrong descriptor index', '(handle >> 18) * 2', '(handle >> 19) * 2'),
         ('write array header instead of element', 'entry[(lane + 1) * 2 + 1]', 'entry[lane * 2 + 1]'),
         ('wrong batch stride', '        entry += 8;', '        entry += 4;'),
         ('lose four-element source snapshot', '&vector[lane], 4', '&values[lane], 4'),
         ('drop batch dirty bits', 'g_shaderParameterFourDirtyMasks[(bit & 7) * 2]', '0'),
         ('drop crossing dirty byte', 'g_shaderParameterFourDirtyMasks[(bit & 7) * 2 + 1]', '0'),
         ('wrong tail dirty bit', 'g_shaderParameterDirtyMasks[bit & 7]',
          'g_shaderParameterDirtyMasks[(bit + 1) & 7]'),
         ('drop scalar remainder', '    while (bit < end) {', '    while (false) {'),
         ('read through lvlx boundary', 'available < 4 ? available : 4', '4'),
     ]),
    ('pong_lighting_apply_ambient_cube', 'src/game/pong_render.cpp',
     'void pongLighting_ApplyAmbientCube(', [
         ('skip all uploads', '    uint8_t* lighting = nullptr;', '    return;\n    uint8_t* lighting = nullptr;'),
         ('ignore state-8 gate', 'loop + 12) != 8', 'loop + 12) != 7'),
         ('reverse key selection', 'loop[0x240] != 0', 'loop[0x240] == 0'),
         ('accept negative key', 'if (key > -1)', 'if (true)'),
         ('skip all interning on missing lighting', '    uint32_t handles[7];',
          '    if (lighting == nullptr) return;\n    uint32_t handles[7];'),
         ('wrong Z-negative name', 'g_ambientCubeParameterNames + 40, 1',
          'g_ambientCubeParameterNames + 32, 1'),
         ('wrong colour record stride', 'lightIndex * 0x120', 'lightIndex * 0x110'),
         ('use another light weight', '0x1660 + lightIndex * 4', '0x1660 + ((lightIndex + 1) % 5) * 4'),
         ('lose scale bias', '0x1674), one)', '0x1674), 0.0f)'),
         ('scale colour w', 'color[2] * scale, color[3]', 'color[2] * scale, color[3] * scale'),
         ('omit last face', 'face < 6', 'face < 5'),
         ('lose dirty marking', 'g_shaderParameterDirtyMasks[bit & 7]', '0'),
         ('omit reused falloff tail', '            std::memcpy(falloff, vector, 16);',
          '            std::memcpy(falloff, vector, 8);'),
         ('wrong falloff constant', 'std::memcpy(&falloff[0], &kFastTurnMul, 4);',
          'std::memcpy(&falloff[0], &lbl_8202D108, 4);'),
         ('omit falloff counter', '        ++g_grmShaderFx_boundContext;\n        const uint32_t* entry',
          '        /* counter lost */\n        const uint32_t* entry'),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    caught = 0
    for name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) >= 1, f'anchor changed: {name}: {label}'
            changed = body.replace(old, new)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(name + '.py'),
                             Options(trials=160, seed=1, patches=((body, changed),))).run()
            first = output.getvalue().splitlines()[0]
            detected = (rc == 1 and first.startswith('FAIL ')
                        and 'timeout' not in output.getvalue().lower())
            print(f'{"CAUGHT" if detected else "MISSED"} {name}: {label}: {first}', flush=True)
            if not detected:
                print(output.getvalue())
                return 1
            caught += 1
    print(f'Caught {caught}/{sum(len(case[3]) for case in CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
