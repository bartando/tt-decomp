"""Patch cache copies only; every broken lift must yield behavioral FAIL."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'grc_command_fixup_grow': [
        ('skip old tail', 'if (list->tail != nullptr)', 'if (false)'),
        ('lose GPU aperture', '(((address >> 20) + 0x200u) & 0x1000u)', '0u'),
        ('wrong GPU base', '- 0x40000000u;', '+ 0x40000000u;'),
        ('wrong allocation size', 'list->device, 0x1080, 0x80', 'list->device, 0x107C, 0x80'),
        ('wrong fallback process', 'KeGetCurrentProcessType() == 2', 'KeGetCurrentProcessType() == 1'),
        ('retain failed count', '        list->count = 0;', '        /* count retained */'),
        ('lose first link', 'block[0] = gpuChainAddress(block + 1);', 'block[0] = gpuChainAddress(block);'),
        ('lose previous cursor link', 'if (list->cursor != nullptr)', 'if (false)'),
        ('wrong end sentinel', 'list->end = block + 0x41F;', 'list->end = block + 0x420;'),
        ('wrong returned cursor', 'return block + 1;', 'return block;'),
    ],
    'grc_command_stream_refill': [
        ('ignore active guard', 'field<uint32_t>(device, 0x34E0) == 0', 'true'),
        ('wrong disabled bit', '(field<uint8_t>(device, 0x28C0) & 0x80) == 0 &&\n        g_grcThreadCommandTracking', '(field<uint8_t>(device, 0x28C0) & 0x40) == 0 &&\n        g_grcThreadCommandTracking'),
        ('reload source after allocate', 'commands, count, capturedSource, 0,', 'commands, count, source, 0,'),
        ('wrong append flags', 'commands, count, capturedSource, 0,', 'commands, count, capturedSource, 1,'),
        ('omit finalize', '    rage_A780(device);', '    /* finalize lost */'),
        ('ignore tracking global', 'g_grcThreadCommandTracking != 0', 'true'),
        ('wrong handle adjustment', 'field<uint32_t>(device, 0x289C) - 2', 'field<uint32_t>(device, 0x289C) - 1'),
        ('lose tracking bit', 'field<uint8_t>(device, 0x28C1) |= 4;', 'field<uint8_t>(device, 0x28C1) = 4;'),
        ('omit handle retirement', '            rage_AA78(device, &handle);', '            ;'),
    ],
    'grc_command_stream_submit': [
        ('clear wrong flag', 'field<uint8_t>(device, 0x28C0) &= 0xFD;', 'field<uint8_t>(device, 0x28C0) &= 0xFE;'),
        ('grow on exact fit', 'reinterpret_cast<uintptr_t>(list->end))', 'reinterpret_cast<uintptr_t>(list->end) - 1)'),
        ('wrong command opcode', '*cursor = 0x85000000u;', '*cursor = 0x84000000u;'),
        ('lose cursor advance', 'list->cursor = cursor + 1;', 'list->cursor = cursor;'),
        ('wrong skip-submit bit', '(field<uint8_t>(device, 0x28C0) & 0x10) == 0', '(field<uint8_t>(device, 0x28C0) & 0x20) == 0'),
        ('wrap large shift', 'shift < 32 ? 0x01000000u << shift : 0', '0x01000000u << (shift & 31)'),
        ('wrong submit flags', 'rage_7BD0(device, 1, mask)', 'rage_7BD0(device, 0, mask)'),
        ('lose error result', 'return static_cast<int32_t>(0x8007000Eu);', 'return 0;'),
        ('skip successful reset', 'if ((field<uint8_t>(device, 0x28C0) & 1) == 0)', 'if (false)'),
    ],
}


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/graphics/grc_command_stream.cpp').read_text()
    count = 0
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
            count += 1
    print(f'Caught {count}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
