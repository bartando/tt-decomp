"""Require behavioral failures for deliberate skinning regressions; patch cache only."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ('empty skinning', '    auto* source =', '    return;\n    auto* source ='),
    ('skip first mapping', 'if (!source->mapped) pg_7578_g(source);', 'if (false) pg_7578_g(source);'),
    ('skip source cursor reset', '    pg_54B0_g(source, 0);', '    (void)source;'),
    ('skip output cursor reset', 'if (outputBuffer) pg_54B0_g(output, 0);', 'if (false) pg_54B0_g(output, 0);'),
    ('skip single vertex', 'vertexCount <= 0', 'vertexCount <= 1'),
    ('wrong index gate', 'vertexFormat(source) & 4', 'vertexFormat(source) & 2'),
    ('wrong weights gate', 'vertexFormat(source) & 2', 'vertexFormat(source) & 4'),
    ('natural byte order', 'palette[(indices >> 16) & 255]', 'palette[indices >> 24]'),
    ('swap second bone', 'palette[(indices >> 8) & 255]', 'palette[indices & 255]'),
    ('retain subnormal matrix inputs', 'vmxFloat(matrices[bones[0] * 16 + component])', 'matrices[bones[0] * 16 + component]'),
    ('ignore matrix alignment', 'align16(static_cast<const float*>(pose))', 'static_cast<const float*>(pose)'),
    ('wrong first weight', 'vmxFloat(weights[0])', 'vmxFloat(weights[1])'),
    ('omit fourth influence', 'influence < 4', 'influence < 3'),
    ('discard accumulated matrix', 'sum = vmxFloat(sum + product)', 'sum = product'),
    ('wrong source position', 'loadStagingVector(position, source, 0)', 'loadStagingVector(position, source, 16)'),
    ('omit normal read', 'pg_5BD8_g(normal, source);', '(void)normal;'),
    ('omit source tangent', 'vertexFormat(source) & 0x4000', 'vertexFormat(source) & 0x8000'),
    ('wrong output position gate', 'vertexFormat(output) & 1', 'vertexFormat(output) & 2'),
    ('omit output normals', 'vertexFormat(output) & 8', 'vertexFormat(output) & 0x10'),
    ('omit output tangent', 'pg_6B20_g(output, 0, skinnedTangent);', '(void)skinnedTangent;'),
    ('wrong source stride', 'source->stagingAddress += source->stride', 'source->stagingAddress += 16'),
    ('advance aliases twice', 'if (output != source)', 'if (true)'),
    ('wrong output stride', 'output->stagingAddress += output->stride', 'output->stagingAddress += source->stride'),
]
TRANSFORM_MUTATIONS = [
    ('omit translation', ' | one;', ';'),
    ('transpose matrix', 'matrix[row * 4 + column]', 'matrix[column * 4 + row]'),
    ('omit fourth dot term', 'row < 4', 'row < 3'),
    ('round each dot product', 'sum += double(vmxFloat(homogeneous[row])) * vmxFloat(matrix[row * 4 + column]);',
     'sum = float(sum + float(vmxFloat(homogeneous[row]) * vmxFloat(matrix[row * 4 + column])));'),
    ('wrong leftover w', 'out[3] = homogeneous[0]', 'out[3] = 1.0f'),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/graphics/grc_vertex_buffer.cpp').read_text()
    count = 0
    for signature, mutations in [('extern "C" void pg_5510_g(', MUTATIONS),
                                  ('void skinTransform(', TRANSFORM_MUTATIONS)]:
        start = source.index('\n' + signature) + 1
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, label
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name('vertex_buffer_skin.py'),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f'MISSED {label}: BUILD {exc}', flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and 'faulted' not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {label}: " +
                  (report.splitlines()[0] if report else 'no checker output'), flush=True)
            if not caught:
                print(report)
                return 1
            count += 1
    print(f'Caught {count}/{count} mutations', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
