"""Only behavioral divergences count; build errors and faults fail the proof.
Run with PYTHONPATH=tools/lift-check and tools/lift-check/.venv/bin/python.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("aud_sfx_set_pitch", "void audVoiceSfx::SetPitch(", [
        ("include zero in log path", "pitch > 0.0f", "pitch >= 0.0f"),
        ("skip logarithm scale", "logarithm * 1.4426950216293335f", "logarithm"),
        ("wrong cent scale", "cents * 1200.0f", "cents * 1000.0f"),
        ("wrong positive saturation", "command = INT32_MAX", "command = 0"),
        ("wrong command", "16394, params, 2", "16391, params, 2"),
    ]),
    ("aud_sfx_set_pan", "void audVoiceSfx::SetPan(", [
        ("wrong lower clamp", "double(pan) : -1.0", "double(pan) : 0.0"),
        ("wrong upper clamp", "low - 3.0 >= 0.0 ? 3.0 : low", "low - 1.0 >= 0.0 ? 1.0 : low"),
        ("lose negative wrap", "clamped, 90.0, 360.0", "clamped, 90.0, 0.0"),
        ("wrong command", "16391, params, 2", "16394, params, 2"),
        ("drop handle", "*static_cast<uint32_t*>(m_pSfxRef)", "0"),
    ]),
    ("aud_sfx_set_stereo_volume", "void audVoiceSfx::SetStereoVolume(", [
        ("wrong gain scale", "volume * 1000.0f", "volume * 100.0f"),
        ("truncate to 32 bits early", "integer = static_cast<int64_t>(scaled)", "integer = scaled >= 0x1p31f ? INT32_MAX : (scaled <= -0x1p31f ? INT32_MIN : static_cast<int32_t>(scaled))"),
        ("swap channels", "commandWord(left), commandWord(right)", "commandWord(right), commandWord(left)"),
        ("wrong count", "16396, params, 3", "16396, params, 2"),
        ("wrong command", "16396, params, 3", "16390, params, 3"),
    ]),
]

def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/rage_audio.cpp").read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label)
            report = io.StringIO()
            with contextlib.redirect_stdout(report):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            output = report.getvalue()
            caught = rc == 1 and "faulted" not in output
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {output.splitlines()[0]}", flush=True)
            if not caught:
                print(output)
                return 1
            total += 1
    print(f"Caught {total}/{total} behavioral mutations", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
