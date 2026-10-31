"""Require cache-effect FAIL; ordinary memory equality must not hide a no-op lift."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('omit cache flush', '        flushGpuCacheLine(cursor);', '        ;'),
    ('wrong line stride', '        cursor += 128;', '        cursor += 256;'),
    ('truncate partial end line', '(reinterpret_cast<uintptr_t>(end) + 127)', '(reinterpret_cast<uintptr_t>(end))'),
    ('round source up', 'begin & ~uintptr_t(127)', '(begin + 127) & ~uintptr_t(127)'),
    ('flush coherent window', 'static_cast<uint32_t>(begin - coherentWindowBase) <= coherentWindowSpan', 'false'),
    ('skip upper boundary line', 'coherentWindowSpan = 0x07EFFFFFu', 'coherentWindowSpan = 0x07F00000u'),
    ('omit ordering barrier', '    __builtin_ppc_sync();', '    ;'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/graphics/grc_cache.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('grc_gpu_cache_flush.py'),
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
