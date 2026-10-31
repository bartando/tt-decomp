"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('grc_release_reference', 'uint32_t grcResource_ReleaseRef(', [
        ('wrong last-reference test', '(*flags & 255) == 1', '(*flags & 255) == 2'),
        ('skip linked resource', 'if (void* linked = rage::load_ptr32<void>(resource, 0x2C))', 'if (void* linked = static_cast<void*>(nullptr))'),
        ('ignore retained-allocation flags', '(*flags & 0xF80000u) == 0', 'true'),
        ('wrong counter change', '*flags -= 1;', '*flags += 1;'),
        ('wide return instead of byte', 'return *flags & 255;', 'return *flags;'),
    ]),
    ('grc_release_holder', 'void grcDevice_cleanupInternal(', [
        ('wrong counter change', '*references -= 1;', '*references += 1;'),
        ('free with references left', '*references == 0', '*references != 0'),
        ('wrong allocation tag', '0x24800000', '0x24870000'),
        ('omit holder clear', '        *slot = nullptr;', '        (void)slot;'),
    ]),
    ('grc_release_shared', 'void grcDevice_releaseSharedResources(', [
        ('wrong surface order', '&g_grcSharedSurfacePair[1], &g_grcSharedSurfacePair[0]', '&g_grcSharedSurfacePair[0], &g_grcSharedSurfacePair[1]'),
        ('ignore nonzero remaining refs', 'if (grcResource_ReleaseRef(resource) != 0)', 'if (grcResource_ReleaseRef(resource) == 0)'),
        ('omit processed slot clear', '            *slot = nullptr;', '            (void)slot;'),
        ('skip last texture slot', '&g_grcSharedSurface, &g_grcSharedTexture', '&g_grcSharedSurface, &g_grcSharedSurface'),
    ]),
]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/graphics/grc_resource_release.cpp').read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'), Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and 'faulted' not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f'Caught {total}/{total} behavioral mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
