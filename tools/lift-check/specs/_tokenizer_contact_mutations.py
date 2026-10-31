"""Mutation proof for tokenizer pushback/matching and the contact volume query."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
TOK = 'src/rage/io/fiAsciiTokenizer.cpp'
CASES = [
    ('fi_tokenizer_push_back_token', TOK, 'void fiTokenizer_PushBackToken(', [
        ('wrong count', '*count = index + 1;', '*count = index;'),
        ('wrong quote slot', 'index + 2)', 'index + 1)'),
        ('forward copy', '*destination-- = byte;', '*destination++ = byte;'),
        ('wrong prefix', "bytes[0x1c] = ' ';", "bytes[0x1c] = '\\t';"),
    ]),
    ('fi_tokenizer_check_token', TOK, 'bool fiTokenizer_CheckToken(', [
        ('wrong token capacity', 'GetToken(token, 128)', 'GetToken(token, 64)'),
        ('invert consume', 'if (!matched || !consume)', 'if (!matched || consume)'),
        ('omit position restore', '*reinterpret_cast<uint32_t*>(bytes + 0x10) = saved;', '(void)saved;'),
    ]),
    ('fi_tokenizer_check_token_insensitive', TOK, 'bool fiTokenizer_CheckTokenInsensitive(', [
        ('case-sensitive comparison', '_stricmp(expected, token)', 'std::strcmp(expected, token)'),
        ('invert consume', 'if (!matched || !consume)', 'if (!matched || consume)'),
        ('wrong position slot', '*reinterpret_cast<uint32_t*>(bytes + 0x10) = saved;', '*reinterpret_cast<uint32_t*>(bytes + 0x14) = saved;'),
    ]),
    ('ph_contact_scaled_volume', 'src/physics/ph_physics.cpp', 'float phContact_GetScaledVolume(', [
        ('wrong volume sign', 'volume = __builtin_fabsf(volume);', 'volume = volume;'),
        ('skip diagnostic', 'nop_8240E6D0(g_phNegativeVolumeWarning);', '(void)volume;'),
        ('wrong scale', 'volume * g_phContactVolumeScale', 'volume'),
    ]),
]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                    Options(trials=80, seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and 'FAIL' in report and 'the lift faulted' not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
