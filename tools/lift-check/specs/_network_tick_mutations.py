"""Reject incorrect kernel-tick offsets and timer/state-machine regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'network_uptime': ('src/xam/time_stamp.cpp', [
        ('bundle field', 'return hostGetKeTimeStampBundle()->milliseconds;', 'return hostGetKeTimeStampBundle()->reserved[0];'),
    ]),
    'network_sink_pause': ('src/game/network/pong_network_io.cpp', [
        ('pause tick offset', 'bytes + 0x6C) = atSingleton_6F98_g();', 'bytes + 0x68) = atSingleton_6F98_g();'),
        ('elapsed sign', 'atSingleton_6F98_g() - *reinterpret_cast<uint32_t*>(bytes + 0x6C)', '*reinterpret_cast<uint32_t*>(bytes + 0x6C) - atSingleton_6F98_g()'),
        ('deadline offset', 'node + 0x14);', 'node + 0x10);'),
        ('child flag', 'result = game_9D70_h(child, flag);', 'result = game_9D70_h(child, 0);'),
    ]),
    'network_sink_poll': ('src/game/network/pong_network_io.cpp', [
        ('probe branch', 'if (session()->IsPending() == 0) {', 'if (session()->IsPending() != 0) {'),
        ('poll tick offset', 'bytes + 0x64) = atSingleton_6F98_g();', 'bytes + 0x60) = atSingleton_6F98_g();'),
        ('ready callback', 'session()->OnReady();', 'session()->OnClosed();'),
        ('pending notification', 'bytes + 0x54) = 1;', 'bytes + 0x54) = 0;'),
        ('error result', 'return 0x8AC70008u;', 'return 0x8AC70006u;'),
    ]),
}

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, (source_path, mutations) in CASES.items():
        source = (root / source_path).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=192, seed=1, patches=((old, new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
