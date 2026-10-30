"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_shape_fetch_value_mutations.py

Passing full baselines first; mutate only cached build copies. Require a
behavioral FAIL (exit 1), never a BUILD/SPEC/UNSUPPORTED error, for each mutant.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'swf_value_to_float': ('src/rage/swf.cpp', 'extern "C" float swfValueToFloat(', (
        ('normalize boolean', '*static_cast<const uint8_t*>(value)', '(*static_cast<const uint8_t*>(value) != 0)'),
        ('unsigned integer', 'static_cast<int32_t>(words[0])', 'words[0]'),
        ('reject tag-zero text', 'case 0: case 1:', 'case 1:'),
        ('wrong string pointer', 'static_cast<uintptr_t>(words[0])', 'static_cast<uintptr_t>(words[0] + 1)'),
        ('accept object payload', 'case 3:', 'case 3: case 5:'),
        ('negate float', 'return number;', 'return -number;'),
        ('wrong unsupported result', 'return 0.0f;', 'return 1.0f;'),
    )),
    'grc_patch_vertex_fetch_instructions': ('src/graphics/grc_gpu_resources.cpp', '\nvoid grcPatchVertexFetchInstructions(', (
        ('semantic index', '((location >> 16) & 15)', '((location >> 12) & 15)'),
        ('last matching element', '                break;', '                /* keep looking */'),
        ('missing attribute opcode', '0x05F00000u', '0x05E00000u'),
        ('missing attribute stride', '| strides[0]', '| 0u'),
        ('unsigned normalization', 'if ((format & 0xC0) == 0x40)', 'if (false)'),
        ('stream stride', 'strides[element->stream]', 'strides[0]'),
        ('unaligned byte offset', '& 0x7FFFFF00u', '& 0x7FFFFFFFu'),
        ('drop constant swizzles', 'swizzle |= 0xE;', 'swizzle |= 0;'),
        ('wrong swizzle lane', 'selected((instruction.format >> 6) & 7)', 'selected((instruction.format >> 3) & 7)'),
        ('skip sorting', 'if (swap || order > 0)', 'if (false)'),
        ('move fixed final fetch', 'fixedLast ? end : end + 1', 'end + 1'),
        ('reverse offset order', 'fetchOffset(left.offset) - fetchOffset(right.offset)', 'fetchOffset(right.offset) - fetchOffset(left.offset)'),
        ('ignore format tie break', 'if (!order) order =', 'if (false) order ='),
        ('short burst limit', 'span <= 8', 'span <= 7'),
        ('merge different streams', 'fetchConstantIndex(head.opcode) == fetchConstantIndex(current.opcode)', 'true'),
        ('drop merged fetch bit', 'patched[i].format |= 0x40000000u;', 'patched[i].format |= 0;'),
        ('wrong output instruction', 'input->fetchLocations[i] & 0xFFF', 'i'),
    )),
    'swf_render_instance_tree': ('src/rage/swf.cpp', 'void swfRenderInstanceTree(', (
        ('wrong virtual draw slot', 'definition->Render(node + 8, mode);',
         'definition->Destroy(static_cast<uint32_t>(mode));'),
    )),
    'swf_shape_render': ('src/rage/swf.cpp', 'void swfSHAPE::Render(', (
        ('default stroke width', 'uint16_t width = 20;', 'uint16_t width = 1;'),
        ('default fill colour', 'defaultFill = {0, 0xFFFFFFFFu,', 'defaultFill = {0, 0u,'),
        ('polyline endpoint order', 'endpoints[0], endpoints[1], endpoints[2], endpoints[3]', 'endpoints[2], endpoints[3], endpoints[0], endpoints[1]'),
        ('fan primitive', 'rage_2A78(5, remaining);', 'rage_2A78(3, remaining);'),
        ('texture override', 'if (state[140] == 0)', 'if (state[140] != 0)'),
        ('texture resource field', 'static_cast<void**>(fill->texture)[2]', 'static_cast<void**>(fill->texture)[1]'),
        ('missing UV state', 'std::memcpy(g_swfLineRenderState.uvMatrix, fill->textureMatrix, 24);', ''),
        ('triangle command advance', 'command += swfDrawShapeTriangles(this, command, transform, fill);', 'command += swfDrawShapeTriangles(this, command, transform, fill) - 1;'),
        ('unsigned fan coordinates', 'static_cast<int32_t>(command[0])', 'command[0]'),
        ('drop gradient', 'fill->gradient ?', 'false ?'),
        ('unsigned colour multiplier', 'static_cast<int8_t>(state[56 + channel])', 'state[56 + channel]'),
        ('alpha divisor', 'value * state[71] / 255', 'value * state[71] / 256'),
        ('unfused transform', 'std::fma(py, m[2], m[0] * px)', '(py * m[2] + m[0] * px)'),
        ('UV translation', '+ uv[4];', '+ uv[5];'),
        ('pixel scale', 'screenX * g_swfPixelScaleX', 'screenX * g_swfPixelScaleY'),
        ('missing vertex', 'fxEmitVertex2D(screenX * g_swfPixelScaleX, screenY * g_swfPixelScaleY);', ''),
        ('cursor cleanup', 'g_fxVertexCursor = 0;', ''),
        ('device completion', 'device[0] = device[0x3554 / 4];', ''),
        ('count-only cleanup', 'g_fxCountOnly = 0;', 'g_fxCountOnly = 1;'),
        ('metadata skip', 'command += 2; // Metadata pair', 'command += 0; // Metadata pair'),
        ('fill style index', 'fill = fills + index - 1', 'fill = fills + index % 3'),
        ('stroke style index', 'stroke = strokes[index - 1]', 'stroke = strokes[index % 3]'),
        ('unknown opcode termination', 'break; // Unknown words', 'return; // Unknown words'),
    )),
}


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, (path, signature, mutations) in CASES.items():
        spec = Path(__file__).with_name(spec_name + '.py')
        for seed in (1, 7):
            if Checker(spec, Options(seed=seed)).run() != 0:
                return 1
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index('\n}', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f'mutation anchor changed: {spec_name}/{label}'
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec, Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}/{label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
        print(f'{spec_name}: caught {len(mutations)}/{len(mutations)}', flush=True)
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
