"""Patch cached bodies only; every mutant must fail behaviorally, never fault.
Run with PYTHONPATH=tools/lift-check and tools/lift-check/.venv/bin/python.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('grc_state_surface_defaults', 'void grc_36E8(', [
        ('wrong samples', 'descriptor >> 16', 'descriptor >> 18'),
        ('lose cached bits', '& 0xFFFE1FF8u', '& 0u'),
        ('wrong dirty word', 'UINT64_C(0x20000000)', 'UINT64_C(0x10000000)'),
        ('wrong viewport source', 'grcDevice_SetViewport(device, g_grcResolveViewport);', 'grcDevice_SetViewport(device, g_grcResolveScissor);'),
    ]),
    ('grc_state_apply_scissor', 'void grc_5E08(', [
        ('invert intersection flag', 'if (enabled)', 'if (!enabled)'),
        ('unsigned left comparison', 'static_cast<int32_t>(x0) <= static_cast<int32_t>(left)', 'x0 <= left'),
        ('lose reserved bits', '(read<uint32_t>(device, 0x2D04) & 0x80008000u)', '0u'),
        ('retain too many coord bits', '(x0 & 0x7FFFu)', '(x0 & 0xFFFFu)'),
    ]),
    ('grc_state_clip_plane', 'void rage_6858(', [
        ('omit fourth cached lane', 'lane < 4; ++lane)\n        write', 'lane < 3; ++lane)\n        write'),
        ('wrong packet register', 'index + 0x8E2', 'index + 0x8E1'),
        ('wrong dirty bit', 'index + 46', 'index + 45'),
        ('upload modified cache instead of source', 'read<uint32_t>(plane, lane * 4)', 'read<uint32_t>(static_cast<uint8_t*>(device) + 0x3230 + index * 16, lane * 4)'),
    ]),
    ('grc_state_resolve_packet', 'uint32_t* grc_DBF8(', [
        ('wrong zero mask sentinel', 'mask ? mask : 0xFFFFFFFFu', 'mask'),
        ('wrong fixed register', '0x22204', '0x22208'),
        ('wrong dirty bits', '0xE000000380000000', '0xE000000300000000'),
        ('wrong cursor result', 'return cursor;', 'return cursor - 1;'),
    ]),
    ('grc_state_shader_fallback', 'void grc_3410(', [
        ('wrong fallback mode', '| 5u', '| 4u'),
        ('wrong synchronization word', '0x8000, 0x10A2F', '0, 0x10A2F'),
        ('omit cursor publication', '    publish(device, cursor);', '    (void)cursor;'),
    ]),
    ('grc_state_shader_fallback', 'uint32_t* reserve(', [
        ('refill at equality', '(cursor) > reinterpret_cast', '(cursor) >= reinterpret_cast'),
    ]),
    ('grc_state_flush_resolve_groups', 'void grc_3E20(', [
        ('miss group boundary', '0x3FFFC000', '0x3FFF8000'),
        ('wrong mask shift', '21, 0x2180', '20, 0x2180'),
        ('wrong register base', '0x2380, 0x2E90', '0x2381, 0x2E90'),
        ('clear unrelated flags', 'read<uint64_t>(device, group.offset) & ~group.mask', 'UINT64_C(0)'),
    ]),
    ('grc_state_register_overflow', 'uint32_t* grcDevice_WriteRegisterRunOverflow(', [
        ('ignore stride rounding', 'available / static_cast<int32_t>(stride)', 'available'),
        ('wrong packet count', '((words - 1) << 16)', '(words << 16)'),
        ('wrong register advance', 'firstRegister += words;', 'firstRegister += 1;'),
        ('use refill return instead of publication',
         "        rage_A980(device);\n        // The refill's stored cursor, not its return register, is authoritative.\n        cursor = rage::load_ptr32<uint32_t>(device, 0);",
         '        cursor = static_cast<uint32_t*>(rage_A980(device));'),
    ]),

]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/graphics/grc_state_helpers.cpp').read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label, body.count(old))
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
