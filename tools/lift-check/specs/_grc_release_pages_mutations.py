"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [('grc_release_pages',
  'void grc_2CC8(',
  [('wrong page decrement', 'words[0] - 0x1000u', 'words[0] - 1u'),
   ('wrong page-count test', '(flags & 0xF000u) == 0', '(flags & 0xF000u) != 0'),
   ('forget first sentinel', 'words[2] = 0xFFFF0000u;', 'words[2] = 0;'),
   ('ignore first raw-address mode',
    'flags & 0x40000000u ? data : grcCacheBase(data)',
    'false ? data : grcCacheBase(data)'),
   ('forget second sentinel', 'words[3] = 0xFFFF0000u;', 'words[3] = 0;'),
   ('cache stale address-mode flag',
    'words[0] & 0x40000000u ? auxiliary',
    'flags & 0x40000000u ? auxiliary'),
   ('omit terminal sync', '__atomic_thread_fence(__ATOMIC_SEQ_CST);', '(void)0;')])]

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
