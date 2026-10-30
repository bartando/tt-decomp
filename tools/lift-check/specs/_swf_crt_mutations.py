"""Mutate build-cache copies and require behavioral failures from each spec."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    'swf_hash_member_name': ('src/rage/swf_clip_events.cpp', [
        ('case folding', "ch -= 32", "ch -= 31"),
        ('signed characters', 'static_cast<int8_t>(*name++)', 'static_cast<uint8_t>(*name++)'),
        ('avalanche', 'high ^ (high >> 24)', 'high ^ (high >> 20)'),
    ]),
    'swf_value_to_boolean': ('src/rage/swf_vm.cpp', [
        ('boolean byte', 'return *reinterpret_cast<const uint8_t*>(&value->payload);', 'return value->payload != 0;'),
        ('integer zero', 'case 3: case 5: return value->payload != 0;', 'case 3: case 5: return value->payload == 0;'),
        ('float zero', 'return number != g_swfZero;', 'return number == g_swfZero;'),
        ('unknown tag', 'default: return 0;\n    }\n}\n\n// @ 0x823FF7E8', 'default: return 1;\n    }\n}\n\n// @ 0x823FF7E8'),
    ]),
    'crt_blkmov': ('src/crt/memory.c', [
        ('word byte order', 'd[0] = a; d[1] = b; d[2] = c; d[3] = e;', 'd[0] = e; d[1] = b; d[2] = c; d[3] = a;'),
        ('short copy', 'while (count--) *d++ = *s++;', 'while (count > 1) { *d++ = *s++; --count; }'),
        ('extra byte', 'while (count--) *d++ = *s++;', 'do { *d++ = *s++; } while (count--);'),
        ('return value', 'while (count--) *d++ = *s++;\n    return dst;', 'while (count--) *d++ = *s++;\n    return d;'),
    ]),
}


def main():
    for spec, (path, mutations) in CASES.items():
        source = (ROOT / path).read_text()
        for name, old, new in mutations:
            assert source.count(old) == 1, name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f'{spec}: {"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
