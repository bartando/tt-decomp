"""Behavioral mutation checks; source patches affect build-cache copies only.

Run: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this_file.py
Only a behavioral FAIL (exit 1), never BUILD/SPEC/UNSUPPORTED, counts as caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/rage/swf.cpp"
CASES = {
    "swf_instance_goto_frame": ("void swfINSTANCE::GotoFrame(", [
        ("target truncation", "targetFrame = static_cast<uint16_t>(targetFrame);", "targetFrame = targetFrame;"),
        ("skip flag width", "skipActions = static_cast<uint8_t>(skipActions);", "skipActions = static_cast<uint16_t>(skipActions);"),
        ("wrap reset", "SwfWrapResetFlagRef(child) = 0;", "SwfWrapResetFlagRef(child) = 1;"),
        ("command slot", "cmdVtable[2]", "cmdVtable[3]"),
        ("definition slot", "defVtable[2]", "defVtable[3]"),
    ]),
    "swf_instance_next_frame": ("void swfINSTANCE::NextFrame(", [
        ("dispatch slot", "vtable[1]", "vtable[2]"),
        ("full context", "(this, nextFrame, context);", "(this, nextFrame, reinterpret_cast<void*>(static_cast<uint8_t>(reinterpret_cast<uintptr_t>(context))));"),
        ("wrap boundary", "nextFrame >= maxFrames", "nextFrame > maxFrames"),
        ("play during callback", "isPlaying = 1;", "isPlaying = 0;"),
        ("restore play state", "isPlaying = savedPlaying;", "isPlaying = 1;"),
    ]),
    "swf_scriptobject_set_member": ("uint32_t swfSCRIPTOBJECT::SetMember(", [
        ("status", "return 1;", "return 0;"),
        ("table offset", "(char*)this + 4", "(char*)this + 8"),
        ("converted key", "internedName, static_cast", "name, static_cast"),
    ]),
    "swf_instance_set_member": ("uint32_t swfINSTANCE::SetMember(", [
        ("builtin status", "return 1;", "return 0;"),
        ("fallback status", "return reinterpret_cast<ScriptSetter>(vtable[11])(script, name, value);", "return static_cast<uint8_t>(reinterpret_cast<ScriptSetter>(vtable[11])(script, name, value));"),
        ("definition low byte", "if (uint8_t(reinterpret_cast<DefinitionSetter>(definitionVtable[5])(definition, property, value)))", "if (reinterpret_cast<DefinitionSetter>(definitionVtable[5])(definition, property, value))"),
    ]),
    "swf_actionfunc_set_member": ("uint32_t swfACTIONFUNC::SetMember(", [
        ("status width", "return reinterpret_cast<Setter>(vtable[11])(innerObj, name, value);", "return static_cast<uint8_t>(reinterpret_cast<Setter>(vtable[11])(innerObj, name, value));"),
        ("dispatch slot", "vtable[11]", "vtable[10]"),
    ]),
    "swf_scriptarray_set_member": ("uint32_t swfSCRIPTARRAY::SetMember(", [
        ("upper bound", "if (index >=", "if (index >"),
        ("signed indices", "if (index >=", "if (static_cast<uint32_t>(index) >="),
        ("value word", "destination[1] = pair[1];", "destination[1] = pair[0];"),
        ("failure status", "return 0;", "return 1;"),
    ]),
}


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, (signature, mutations) in CASES.items():
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        body = source[start:end]
        for name, old, new in mutations:
            assert old in body, (spec, name)
            patch = (body, body.replace(old, new))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1, patches=(patch,))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
        print(f"{spec}: caught {len(mutations)}/{len(mutations)}", flush=True)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
