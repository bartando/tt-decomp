"""Require behavioral failures for deliberate indexed normal regressions; patch cache only."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ('empty reader', '    auto* buffer', '    return out;\n    auto* buffer'),
    ('wrong attribute gate', 'vertexFormat(buffer) & 8', 'vertexFormat(buffer) & 4'),
    ('invert mapping gate', 'if (!buffer->mapped)', 'if (buffer->mapped)'),
    ('wrong data cursor', 'buffer->dataAddress +', 'buffer->stagingAddress +'),
    ('round down vertex index', 'buffer->stride * index', 'buffer->stride * (index & ~1u)'),
    ('wrong normal offset', 'buffer->normalOffset', 'buffer->positionOffset'),
    ('omit packed unpack', 'unpackNormPacked32(packed, normal);', 'std::memset(normal, 0, 16);'),
    ('force raw format', 'if (buffer->packedNormal)', 'if (false)'),
    ('copy only xyz', 'align16(out)), normal, 16', 'align16(out)), normal, 12'),
    ('wrong return pointer', '    return out;\n}', '    return const_cast<float*>(align16(out));\n}'),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/graphics/grc_vertex_buffer.cpp').read_text()
    count = 0
    for signature, mutations in [('extern "C" float* util_5B08(', MUTATIONS)]:
        start = source.rindex('\n' + signature) + 1
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, label
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name('vertex_buffer_indexed_normal.py'),
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
