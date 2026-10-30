"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python
 tools/lift-check/specs/_five_hot_mutations.py. Mutations use build-cache copies.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = {
    "cr_anim_dof_vector3_normalize": [
        ("keep x", "currentVec[0] = 0.0f;", "currentVec[0] = 1.0f;"),
        ("keep y", "currentVec[1] = 0.0f;", "currentVec[1] = 1.0f;"),
        ("keep z", "currentVec[2] = 0.0f;", "currentVec[2] = 1.0f;"),
    ],
    "msg_msg_sink_process_pending": [
        ("ignore bit 3", "if (stateFlags & 0x18)", "if (stateFlags & 0x10)"),
        ("ignore queue result", "if (hasData != 0)", "if (true)"),
        ("skip flush", "xactSound_Update(msgObj);", "/* omitted */"),
    ],
    "grm_shader_fx_get_technique_pass": [
        ("wrong slot scaling", "(passDesc >> 16) & 0xFFFC", "(passDesc >> 14) & 0xFFFC"),
        ("wrong variant stride", "techniqueData[(variantIndex << 2) + static_cast<uint32_t>(passIndex)]", "techniqueData[(variantIndex << 1) + static_cast<uint32_t>(passIndex)]"),
        ("ignore pass", "techniqueData[(variantIndex << 2) + static_cast<uint32_t>(passIndex)]", "techniqueData[(variantIndex << 2)]"),
    ],
    "crt_is_lead_byte": [
        ("wrong mask", "& 0x8000;\n}", "& 0x4000;\n}"),
        ("wrong character", "static_cast<unsigned>(ch) & 255", "static_cast<unsigned>(ch + 1) & 255"),
        ("constant result", "return table[static_cast<unsigned>(ch) & 255] & 0x8000;", "return 0;"),
    ],
    "crt_vsnprintf_locale": [
        ("wrong flags", "stream.flags = 0x42;", "stream.flags = 0x40;"),
        ("wrong remaining", "stream.remaining = static_cast<int>(size);", "stream.remaining = static_cast<int>(size + 1);"),
        ("skip termination", "if (buffer) {\n        stream.remaining", "if (false) {\n        stream.remaining"),
        ("wrong validation", "if (!format || (size && !buffer))", "if (!format)"),
    ],
}

def main():
    failed = 0
    for spec, mutations in MUTATIONS.items():
        for label, old, new in mutations:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                try:
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(trials=100, patches=((old, new),))).run()
                except Exception as e:
                    rc = -1
                    print(e)
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}", flush=True)
            failed += rc != 1
    return bool(failed)

if __name__ == "__main__":
    raise SystemExit(main())
