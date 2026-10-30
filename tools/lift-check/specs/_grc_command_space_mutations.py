"""Catch behavioral defects in disposable build copies; never edit the checkout.

Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python tools/lift-check/specs/_grc_command_space_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = {
    "grc_device_allocate_command_data": (
        ("wrong word-to-byte conversion", "uint32_t bytes = wordCount * 4u;", "uint32_t bytes = wordCount * 8u;"),
        ("ignore sticky allocation failure", "(state[0x28C1] & 0x80u) != 0", "(state[0x28C1] & 0x40u) != 0"),
        ("wrong reserve flags", "device, 1, &bytes, alignment);", "device, 0, &bytes, alignment);"),
        ("wrong reserve alignment", "device, 1, &bytes, alignment);", "device, 1, &bytes, 4);"),
        ("ignore adjusted reservation size", "field(0x36D0) += bytes;", "field(0x36D0) += wordCount * 4u;"),
        ("threshold equality resets ring", "field(0x36D0) > field(0x36D4)", "field(0x36D0) >= field(0x36D4)"),
        ("ignore reset suppression", "&& field(0x34E0) == 0", "&& true"),
        ("wrong command limit", "field(8) = cursor;", "field(8) = cursor + 4;"),
        ("wrong command end", "field(4) = cursor + 0xA0u;", "field(4) = cursor + 0x80u;"),
        ("invert secondary-ring test", "field(0x36C8) != field(0x36B4)", "field(0x36C8) == field(0x36B4)"),
        ("wrong reset cursor", "field(0x36C0) = field(0x36B8);", "field(0x36C0) = field(0x36B4);"),
        ("drop sticky failure publication", "state[0x28C1] |= 0x80u;", "state[0x28C1] |= 0x40u;"),
    ),
    "grc_device_commit_command_space": (
        ("wrong wrap-sequence mask", "(sequence - fence) & 3u", "(sequence - fence) & 1u"),
        ("wait when sequence matches", "return lag != 0 &&", "return lag == 0 &&"),
        ("wait at equal fence", "end > (fence & ~3u)", "end >= (fence & ~3u)"),
        ("signed fence comparison", "end > (fence & ~3u)", "static_cast<int32_t>(end) > static_cast<int32_t>(fence & ~3u)"),
        ("wrong watchdog queue head", "hang.lastQueueHead = initialQueue[0];", "hang.lastQueueHead = initialQueue[1];"),
        ("wrong watchdog tick", "thread + 0x58", "thread + 0x54"),
        ("invert watchdog result", "D3DDeviceXenon_ReportGPUHang(&hang) == 0", "D3DDeviceXenon_ReportGPUHang(&hang) != 0"),
        ("reuse old queue pointer", "while (pending(queue()[1]));", "while (pending(initialQueue[1]));"),
        ("discard watchdog state on retry", "    do {\n        if (D3DDeviceXenon_ReportGPUHang", "    do {\n        hang.lastGpuTick = 0;\n        if (D3DDeviceXenon_ReportGPUHang"),
        ("skip subsequent ownership checks", "while (pending(queue()[1]));", "while (false);"),
    ),
}


def main():
    source = (Path(__file__).resolve().parents[3] / "src/graphics/grc_device.cpp").read_text()
    total = 0
    for spec, mutations in MUTATIONS.items():
        for name, old, new in mutations:
            assert source.count(old) == 1, f"mutation anchor changed: {name}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f'{"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
