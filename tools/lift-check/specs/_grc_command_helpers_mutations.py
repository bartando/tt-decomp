"""Mutate one cached function body at a time; only behavioral FAIL counts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'query': [
        ('wrong empty sentinel', 'emptyRange = UINT64_C(0xFFFFFFFF)', 'emptyRange = UINT64_C(0)'),
        ('ignore pending range', 'if (pending) {', 'if (false) {'),
        ('lose wrapped-ring packet', 'if (ringWrapped) {', 'if (false) {'),
        ('wrong sync command', 'output[5] = 0xC0043C00;', 'output[5] = 0xC0043C01;'),
        ('truncate end page', '(static_cast<uint32_t>(range >> 32) + 4095)', '(static_cast<uint32_t>(range >> 32))'),
        ('retain atomic range', 'const uint64_t range = __atomic_exchange_n(&field<uint64_t>(device, 0x2C98), emptyRange, __ATOMIC_SEQ_CST);', 'const uint64_t range = __atomic_load_n(&field<uint64_t>(device, 0x2C98), __ATOMIC_RELAXED);'),
        ('overwrite address on allocation failure', 'if (packet == nullptr) {\n        *wordCount = 0;', 'if (packet == nullptr) {\n        *gpuAddress = 0;\n        *wordCount = 0;'),
    ],
    'append': [
        ('ignore locked recheck', 'if (field<uint32_t>(device, 0x28FC) != 0) {\n            commands', 'if (true) {\n            commands'),
        ('swap words and address', 'commands, wordCount, gpuAddress);', 'commands, gpuAddress, wordCount);'),
        ('publish count before linking', 'commands = rage_9C88(fixups, commands, wordCount, gpuAddress);\n            field<uint32_t>(device, 0x28FC) += flags;', 'field<uint32_t>(device, 0x28FC) += flags;\n            commands = rage_9C88(fixups, commands, wordCount, gpuAddress);'),
        ('lose saved IRQL', 'KfReleaseSpinLock(lock, irql);', 'KfReleaseSpinLock(lock, 0);'),
        ('drop direct submission', 'phInst_A340_p42(device, packet, 1);', '/* direct path lost */'),
        ('swap direct packet', 'packet[2] = {wordCount, gpuAddress}', 'packet[2] = {gpuAddress, wordCount}'),
    ],
    'finalize': [
        ('grow on exact fit', 'reinterpret_cast<uintptr_t>(entry) + 8 >', 'reinterpret_cast<uintptr_t>(entry) + 8 >='),
        ('wrong batch count', 'entry[0] = 0x81000000u | words;', 'entry[0] = 0x81000000u | (words + 1);'),
        ('emit zero-sized batch', 'if (words != 0) {', 'if (true) {'),
        ('wrong fence cursor', 'phInst_A6A8_p42(device, cursor)', 'phInst_A6A8_p42(device, cursor + 1)'),
        ('wrong cursor alignment', '(reinterpret_cast<uintptr_t>(cursor) + 31)', '(reinterpret_cast<uintptr_t>(cursor) + 15)'),
        ('skip ring allocation rounding', 'field<uint32_t>(device, 0x36C0) = (field<uint32_t>(device, 0x36C0) + 4095) & 0xFFFFF000u;', '; /* rounding lost */'),
    ],
    'reset': [
        ('invert first flag', 'if ((flags & 1) == 0)', 'if ((flags & 1) != 0)'),
        ('lose zero-mask default', 'mask != 0 ? mask : 0xFFFFFFFFu', 'mask'),
        ('lose sixth clip plane', 'index < 6;', 'index < 5;'),
        ('wrong plane stride', '0x3230 + index * 16', '0x3230 + index * 12'),
        ('invert restore flag', 'if ((flags & 2) == 0)', 'if ((flags & 2) != 0)'),
        ('lose last dirty word', 'offset <= 0x30;', 'offset <= 0x28;'),
    ],
    'submit_lists': [
        ('wrong restore bit', 'if ((mode & 0x80) != 0)', 'if ((mode & 0x40) != 0)'),
        ('retain closed list end', 'list->end = nullptr;', '/* stale end retained */'),
        ('wrong flush enum boundary', 'flush > 1u ? 2u : 1u', 'flush != 0 ? 2u : 1u'),
        ('wrong packet end', 'mask | 1, rage_7A20, fixups) + 1', 'mask | 1, rage_7A20, fixups)'),
        ('lose pending range submission', 'if (wordCount != 0)', 'if (false)'),
        ('wrong restored limit', 'field<uint32_t>(device, 0x3530) - 0xA0', 'field<uint32_t>(device, 0x3530) - 0xA4'),
    ],
    'refill_integrated': [
        ('drop generated range packet', 'const uint32_t capturedWordCount = wordCount;', 'const uint32_t capturedWordCount = 0;'),
    ],
}
ADDRESSES = {'query': 0x8235A4E0, 'append': 0x8235A8C0, 'finalize': 0x8235A780,
             'reset': 0x823535A8, 'submit_lists': 0x82367BD0, 'refill_integrated': 0x8235A980}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/graphics/grc_command_stream.cpp').read_text()
    count = 0
    for spec, cases in CASES.items():
        start = source.index(f'// @ 0x{ADDRESSES[spec]:08X} |')
        end = source.find('// @ ', start + 6)
        target = source[start:end if end >= 0 else len(source)]
        for label, old, new in cases:
            assert target.count(old) == 1, f'{spec}: {label}'
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = Checker(Path(__file__).with_name('grc_command_' + spec + '.py'),
                             Options(trials=256, seed=1, patches=((target, target.replace(old, new, 1)),))).run()
            first = out.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith('FAIL ')
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(out.getvalue())
                return 1
            count += 1
    print(f'Caught {count}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
