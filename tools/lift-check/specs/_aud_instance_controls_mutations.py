"""Require behavioral failures for the cue controls and pitch lookup."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "aud_instance_pause": ("void aud_F5F0(audInstance* instance) {", [
        ("ignore stopped flag", "flags & 0x30u", "flags & 0x10u"),
        ("ignore paused flag", "flags & 0x30u", "flags & 0x20u"),
        ("resume instead", "->Pause(1)", "->Pause(0)"),
    ]),
    "aud_instance_resume": ("void aud_F670(audInstance* instance) {", [
        ("ignore stopped flag", "flags & 0x30u", "flags & 0x10u"),
        ("ignore paused flag", "flags & 0x30u", "flags & 0x20u"),
        ("pause instead", "->Pause(0)", "->Pause(1)"),
    ]),
    "aud_instance_stop": ("void aud_F6F0(audInstance* instance) {", [
        ("ignore stopped flag", "flags & 0x30u", "flags & 0x10u"),
        ("ignore paused flag", "flags & 0x30u", "flags & 0x20u"),
        ("wrong stop flags", "->Stop(0)", "->Stop(1)"),
    ]),
    "aud_instance_pitch": ("void aud_FD10(audInstance* instance, float pitch) {", [
        ("whole-word sentinel", "static_cast<uint16_t>(index) != 0xFFFFu", "index != 0xFFFFu"),
        ("truncate variable index", "->SetVariable(index, pitch)", "->SetVariable(static_cast<uint16_t>(index), pitch)"),
        ("wrong pitch", "->SetVariable(index, pitch)", "->SetVariable(index, pitch * 0.5f)"),
    ]),
}


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/aud_instance_update.cpp").read_text()
    for spec, (signature, cases) in CASES.items():
        start = source.index(signature)
        body = source[start:source.index("\n}", start) + 2]
        # All four routines must reload a backend replaced by the callback.
        callback = "GetVariableIndex" if spec.endswith("pitch") else "GetState"
        statement = ("const uint32_t index = instance->voice->GetVariableIndex(g_audPitchParameter);"
                     if callback == "GetVariableIndex" else "instance->voice->GetState(&flags);")
        stale = body.replace(statement, "audCue* previous = instance->voice.get();\n    " + statement)
        stale = stale.replace("instance->voice->SetVariable", "previous->SetVariable")
        stale = stale.replace("instance->voice->Pause", "previous->Pause")
        stale = stale.replace("instance->voice->Stop", "previous->Stop")
        patches = [(label, body.replace(old, new)) for label, old, new in cases]
        patches.append(("retain stale backend", stale))
        for label, broken in patches:
            assert broken != body, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((body, broken),))).run()
            first = output.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith("FAIL ")
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(output.getvalue())
                return 1
    print("Caught 16 mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
