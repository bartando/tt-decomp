"""Only behavioral FAILs count for resource locks; patch build-cache copies."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ('uint32_t grcResource_Lock(', [
        ('empty lock', '    auto* control', '    return data;\n    auto* control'),
        ('ignore wait suppression', '(flags & 0x1010u) == 0', 'true'),
        ('omit fence wait', 'if (pending != 0) rage_AA78(device, &pending);', '(void)pending;'),
        ('wrong shared flags', 'control[0] & 0x00F80000u', 'control[0] & 0x00080000u'),
        ('invert fence owner', 'thread == resourceDeviceWord(device, 0x2888)', 'thread != resourceDeviceWord(device, 0x2888)'),
        ('lose original fence when device fence zero', 'fence != 0 && shared && ownedThread', 'shared && ownedThread'),
        ('ignore invalidate suppression', '(flags & 0x12u) == 0', 'true'),
        ('invert invalidate owner', 'xe_GetCurrentThreadId() != resourceDeviceWord(device, 0x2888)',
         'xe_GetCurrentThreadId() == resourceDeviceWord(device, 0x2888)'),
        ('wrong atomic start half', 'const uint32_t oldStart = uint32_t(observed)',
         'const uint32_t oldStart = uint32_t(observed >> 32)'),
        ('wrong atomic start merge', 'start < oldStart ? start : oldStart', 'start > oldStart ? start : oldStart'),
        ('wrong atomic end merge', 'end > oldEnd ? end : oldEnd', 'end < oldEnd ? end : oldEnd'),
        ('omit atomic update', '!__atomic_compare_exchange_n(range, &observed, desired, false,\n                                                  __ATOMIC_RELAXED, __ATOMIC_RELAXED)', 'false'),
        ('discard refill cursor', 'cursor = static_cast<uint32_t*>(rage_A980(device))', 'rage_A980(device)'),
        ('wrong page alignment', 'const uint32_t pageStart = start & ~0xFFFu', 'const uint32_t pageStart = start & ~0x7FFu'),
        ('omit page-end ceiling', '(end + 0xFFFu) & ~0xFFFu', 'end & ~0xFFFu'),
        ('wrong packet header', '*++cursor = 0xA31;', '*++cursor = 0xA30;'),
        ('wrong cache policy', '*++cursor = cacheFlags;', '*++cursor = 0;'),
        ('wrong final cursor', 'uint32_t(reinterpret_cast<uintptr_t>(cursor));', 'uint32_t(reinterpret_cast<uintptr_t>(cursor + 1));'),
        ('wrong second dirty range gate', 'auxiliary != 0 && auxiliaryBase != 0', 'auxiliary != 0 || auxiliaryBase != 0'),
        ('wrong secondary base', 'second ? auxiliaryBase : base', 'base'),
        ('wrong line granularity', 'offset >> 7', 'offset >> 6'),
        ('omit dirty end ceiling', 'offset + size + 127u', 'offset + size'),
        ('wrong dirty start merge', 'lineStart < oldStart ? lineStart : oldStart', 'lineStart > oldStart ? lineStart : oldStart'),
        ('wrong dirty end merge', 'lineEnd > oldEnd ? lineEnd : oldEnd', 'lineEnd < oldEnd ? lineEnd : oldEnd'),
        ('omit aperture alias', 'if (aperture) data = resourceGpuAddress(data) - 0x40000000u;', '(void)data;'),
        ('wrong lock count', 'control[0] += 0x1000', 'control[0] += 0x2000'),
        ('wrong returned mapping', 'return data;', 'return data + 1;'),
    ]),
    ('static void* resourceKernelDevice(', [
        ('wrong process device', 'KeGetCurrentProcessType() == 2', 'KeGetCurrentProcessType() != 2'),
    ]),
    ('static uint32_t resourceGpuAddress(', [
        ('wrong physical mask', 'address & 0x1FFFFFFFu', 'address & 0x3FFFFFFFu'),
        ('omit aperture carry', '(((address >> 20) + 0x200u) & 0x1000u)', '0u'),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/graphics/grc_gpu_resources.cpp').read_text()
    count = 0
    for signature, mutations in CASES:
        start = source.index('\n' + signature) + 1
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, label
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name('grc_resource_lock.py'),
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
