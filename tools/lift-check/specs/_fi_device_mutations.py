"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [('fi_device_compare_prefix',
  'int32_t fiDevice_ComparePrefix(',
  [('lose uppercase normalization', "a += 'a' - 'A'", 'a += 0'),
   ('lose slash normalization', "if (a == '\\\\') a = '/'", "if (a == '\\\\') a = '\\\\'"),
   ('reverse comparison result', 'return a - b;', 'return b - a;')]),
 ('fi_device_resolve',
  'void* fiDevice_GetDevice(',
  [('ignore longer prefix', 'length > longest', 'length < longest'),
   ('wrong probe flags', 'device->Open(path, 1)', 'device->Open(path, 0)'),
   ('miss longest mount tie', 'length > longest', 'length >= longest'),
   ('ignore mount read-only restriction',
    'entries[best].readOnly != 0',
    'entries[best].readOnly == 0'),
   ('ignore fallback read-only restriction',
    'g_fiFallbackReadOnly != 0',
    'g_fiFallbackReadOnly == 0'),
   ('test full flags instead of byte',
    'if (static_cast<uint8_t>(flags) == 0 && entries[best].readOnly != 0)',
    'if (flags == 0 && entries[best].readOnly != 0)')])]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/io/fiDevice.cpp').read_text()
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
