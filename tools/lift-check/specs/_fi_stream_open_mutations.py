"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [('fi_stream_open',
  'void* fiStream_Open(',
  [('drop resolver flags', 'fiDevice_GetDevice(path, flags)', 'fiDevice_GetDevice(path, 0)'),
   ('reject valid zero handle', 'handle == -1', 'handle == 0'),
   ('ignore byte callback veto',
    'static_cast<uint8_t>(g_fiOpenCallback.get()(path, flags)) == 0',
    'g_fiOpenCallback.get()(path, flags) == 0'),
   ('lose constructed result',
    'return fiStreamBuf_Attach(path, handle, device);',
    'fiStreamBuf_Attach(path, handle, device); return nullptr;')]),
 ('fi_stream_attach',
  'void* fiStreamBuf_Attach(',
  [('skip init on fresh lock', '(g_fiStreamLockInit & 1) == 0', '(g_fiStreamLockInit & 1) != 0'),
   ('wrong pool capacity', 'index < 12', 'index < 11'),
   ('wrong buffer capacity', 'stream->capacity = 4096;', 'stream->capacity = 2048;'),
   ('forget ownership', 'stream->device = device;', 'stream->device = nullptr;'),
   ('wrong high water update', 'index > highWater', 'index < highWater'),
   ('skip success unlock', 'if (scope.locked != 0)', 'if (scope.locked == 0)')]),
 ('fi_stream_open_failed',
  'void* fiStreamBuf_OpenFailed(',
  [('invert missing-file option',
    'if (g_fiMissingFileOptionValue)',
    'if (!g_fiMissingFileOptionValue)')]),
 ('fi_stream_lock_acquire',
  'void fiStreamLock_Acquire(',
  [('reenter already locked scope', 'scope->locked == 0', 'scope->locked != 0'),
   ('wrong locked flag', 'scope->locked = 1;', 'scope->locked = 0;')]),
 ('fi_stream_lock_release',
  'void fiStreamLock_Release(',
  [('release wrong state', 'scope->locked == 1', 'scope->locked == 0'),
   ('retain locked flag', 'scope->locked = 0;', 'scope->locked = 1;')])]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/io/fiStreamOpen.cpp').read_text()
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
