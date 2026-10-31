"""Mutation proof for command reservation, fence waits and GPU watchdog recovery.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_grc_command_reserve_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [('grc_emergency_command_buffer',
  'src/graphics/grc_command_reserve.cpp',
  'extern "C" void grcDevice_UseEmergencyCommandBuffer(',
  [('wrong emergency process', 'if (KeGetCurrentProcessType() == 2) {', 'if (KeGetCurrentProcessType() == 1) {'),
   ('wrong soft limit', 'start + 0x1220', 'start + 0x12C0'),
   ('wrong failure flag', '|= 0x80', '|= 0x40')]),
 ('grc_reserve_command_window',
  'src/graphics/grc_command_reserve.cpp',
  'extern "C" void* rage_A150(',
  [('ignore emergency flag', '& 0x80', '& 0x40'),
   ('wrong callback kind',
    'reserve(context, device, 0, &bytes, 32)',
    'reserve(context, device, 1, &bytes, 32)'),
   ('wrong word padding', '(words + 12) * 4', 'words * 4'),
   ('wrong safety margin', 'end - 0xA0', 'end - 0x80'),
   ('wrong fence selector', '(device, 0x5070) & 1', '(device, 0x5070) & 2'),
   ('retain pending fence',
    'commandField<uint32_t>(device, fenceOffset) = 0;',
    'commandField<uint32_t>(device, fenceOffset) = fence;'),
   ('discard result', 'return result;', 'return nullptr;')]),
 ('grc_wait_fence',
  'src/graphics/grc_command_reserve.cpp',
  'extern "C" void rage_AA78(',
  [('reverse pending test',
    'producer - *fence < producer - *consumer',
    'producer - *fence > producer - *consumer'),
   ('skip submission', '        rage_A980(device);', '        (void)device;'),
   ('ignore alternate command path',
    'if (commandField<uint32_t>(device, 0x34E0) != 0) return;',
    'if (false) return;'),
   ('wrong initial watchdog head', 'hang.lastQueueHead = *consumer;', 'hang.lastQueueHead = 0;'),
   ('wrong initial tick', 'thread + 0x58', 'thread + 0x54'),
   ('ignore watchdog abort',
    'D3DDeviceXenon_ReportGPUHang(&hang) == 0',
    'D3DDeviceXenon_ReportGPUHang(&hang) != 0')]),
 ('grc_sync_command_window',
  'src/graphics/grc_command_reserve.cpp',
  'extern "C" void rage_AD98(',
  [('wrong first packet word', '*++cursor = 0x5C8;', '*++cursor = 0x5C9;'),
   ('wrong second packet word', '*++cursor = 0x20000;', '*++cursor = 0x10000;'),
   ('overflow on limit equality', 'cursor > limit', 'cursor >= limit'),
   ('discard cursor update', '(device, 0) = cursor;', '(device, 0) = limit;'),
   ('reload fence after callback',
    'if (fence != 0)',
    'if (commandField<uint32_t>(device, 0x289C) != 0)')]),
 ('grc_gpu_watchdog',
  'src/graphics/grc_gpu_hang.cpp',
  'int D3DDeviceXenon_ReportGPUHang(',
  [('wrong reported flag', 'm_hangFlags & 0x04', 'm_hangFlags & 0x08'),
   ('ignore changed queue',
    'pState->lastQueueHead != queueHead',
    'pState->lastQueueHead == queueHead'),
   ('wrong timeout', '< 2000u', '< 1999u'),
   ('wrong rollback head', 'm_queueRollbackHead - 2', 'm_queueRollbackHead - 1'),
   ('omit fatal sentinel', 'g_grcProgressState = 15;', 'g_grcProgressState = 0;')])]

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip declarations: each definition begins at column zero.
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            first = report.splitlines()[0] if report else "no checker output"
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
