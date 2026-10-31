"""Timestamp conversion/formatting and the retail diagnostic caller."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES = {
    'network_timestamp_format': ('src/game/network/network_timestamp.cpp', [
        ('fraction scale', 'fraction * 1000.0f', 'fraction * 100.0f'),
        ('minute divisor', 'whole / 60', 'whole / 59'),
        ('second modulus', 'whole % 60', 'whole % 59'),
        ('saturation', 'milliseconds = UINT32_MAX;', 'milliseconds = 0;'),
        ('format bound', 'g_networkTimestampLogBuffer, 50,', 'g_networkTimestampLogBuffer, 49,'),
    ]),
    'network_force_time_log': ('src/game/network/pong_network.cpp', [
        ('timestamp offset', 'FormatTimestampForLog(static_cast<uint8_t*>(thisPtr) + 8)', 'FormatTimestampForLog(static_cast<uint8_t*>(thisPtr) + 4)'),
        ('format argument', 'nop_8240E6D0("ForceSessionTimeSyncMessage %s", formattedTime);', 'nop_8240E6D0(formattedTime);'),
    ]),
}
def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, (path, mutations) in CASES.items():
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=128,seed=1,patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
