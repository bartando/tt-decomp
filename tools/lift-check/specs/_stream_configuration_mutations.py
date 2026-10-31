"""Mutation proof for stream configuration guards, overlap, flags and thunk arguments."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CORE = 'src/physics/stream_configuration.cpp'
PHYS = 'src/physics/ph_physics.cpp'
CASES = [
    ('ph_stream_configure_core', CORE, 'int32_t phStream_Configure(', [
        ('wrong word count', 'i < 14', 'i < 13'),
        ('reverse overlap order', 'for (unsigned i = 0; i < 14; ++i)', 'for (unsigned i = 14; i-- > 0;)'),
        ('reject empty sentinel', 'first != bytes + 4 && first !=', 'first != bytes + 4 || first !='),
        ('skip empty-list guard', 'if (first != bytes + 4 && first !=', 'if (false && first != bytes + 4 && first !='),
        ('wrong mode slot', 'bytes[0x99]', 'bytes[0x9a]'),
    ]),
    ('ph_stream_configure_primary', CORE, 'int32_t phStream_ConfigurePrimary(', [
        ('wrong HRESULT sign', 'result >= 0', 'result <= 0'),
        ('wrong first flag', 'bytes + 0x68', 'bytes + 0x6c'),
        ('omit second flag', '*reinterpret_cast<uint16_t*>(bytes + 0x6a) = 1;', '(void)bytes;'),
    ]),
    ('ph_stream_configure_record_field', CORE, 'int32_t phStream_GetRecordField(', [
        ('ignore positive success', 'result >= 0', 'result == 0'),
        ('wrong record field', 'record.get() + 0x10', 'record.get() + 0x14'),
        ('drop returned error', 'return result;', 'return 0;'),
    ]),
    ('ph_stream_configure_packed', CORE, 'int32_t phStream_ConfigurePacked(', [
        ('omit channels', 'width * channels', 'width'),
        ('wrong packed flags', 'bytes + 0x68', 'bytes + 0x6c'),
    ]),
    ('ph_stream_configure_float_field', PHYS, 'int ph_vt5A78_63_GetFloat108(', [
        ('wrong float field', '+ 108', '+ 112'),
    ]),
    ('ph_stream_configure_thunk_7238', PHYS, 'int32_t ph_vt5A60_32_Thunk(', [
        ('drop mode', 'configuration, mode)', 'configuration, 0)'),
    ]),
    ('ph_stream_configure_thunk_8d00', PHYS, 'int32_t ph_vt5A60_24_Thunk(', [
        ('wrong output', ', output)', ', output + 1)'),
    ]),
    ('ph_stream_configure_thunk_8d30', PHYS, 'int32_t ph_vt5A60_33_Thunk(', [
        ('wrong output', ', output)', ', output + 1)'),
    ]),
    ('ph_stream_configure_thunk_8d28', PHYS, 'int32_t ph_vt5B98_12_Thunk(', [
        ('drop mode', 'configuration, mode)', 'configuration, 0)'),
    ]),
]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        if ';' in source[start:source.index('{', start)]:
            start = source.index(signature, start + len(signature))
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
