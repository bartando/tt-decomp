"""Require behavioral FAIL; mutate cached translations only."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'dat_base_clear_field12': [
        ('omit count clear', 'header->references = 0;', '/* count retained */'),
        ('wrong count offset', 'uint8_t prefix[0x0C]; uint32_t references;', 'uint8_t prefix[0x08]; uint32_t references;'),
        ('clear only one byte', 'header->references = 0;', 'header->references &= 0xFFFFFF00u;'),
    ],
    'dat_base_clear_field12_thunk': [
        ('omit forwarding', '    datBase_ClearField12(object);', '    ;'),
        ('wrong forwarded pointer', '    datBase_ClearField12(object);', '    datBase_ClearField12(static_cast<uint8_t*>(object) + 4);'),
    ],
}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/core/rage_core_utils.cpp').read_text()
    for spec, cases in CASES.items():
        for name, old, new in cases:
            assert source.count(old) == 1, name
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=256, seed=1, patches=((old, new),))).run()
            first = out.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith('FAIL ')
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {name}: {first}", flush=True)
            if not caught:
                print(out.getvalue())
                return 1
    print(f'Caught {sum(map(len, CASES.values()))}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
