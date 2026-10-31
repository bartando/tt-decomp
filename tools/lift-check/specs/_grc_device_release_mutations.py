"""Patch cache copies; BUILD/SPEC/UNSUPPORTED do not count as detection."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('wrong last-reference boundary', 'if (references != 1)', 'if (references != 0)'),
    ('increment count', 'return --references;', 'return ++references;'),
    ('omit teardown', '    grcDeviceXenon_teardown(device);', '    ;'),
    ('free device instead of allocation', '_locale_register(allocation, 0x24800000u);', '_locale_register(device, 0x24800000u);'),
    ('wrong allocation tag', '_locale_register(allocation, 0x24800000u);', '_locale_register(allocation, 0x24000000u);'),
    ('capture header before teardown', '    grcDeviceXenon_teardown(device);\n    void* allocation = *reinterpret_cast<void**>(state - sizeof(void*));', '    void* allocation = *reinterpret_cast<void**>(state - sizeof(void*));\n    grcDeviceXenon_teardown(device);'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/graphics/grc_device.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('grc_device_release.py'),
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
