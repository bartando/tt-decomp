"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_hot_helper_mutations.py

Patches affect cached build copies only. Only a behavioral FAIL counts as a
caught mutation; BUILD/SPEC/UNSUPPORTED errors never do.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = {
    "swf_value_to_integer": ('extern "C" int32_t swfValueToInteger(', (
        ("normalize byte boolean", "return *static_cast<const uint8_t*>(value);",
         "return *static_cast<const uint8_t*>(value) != 0;"),
        ("read tag as integer", "return static_cast<int32_t>(words[0]);",
         "return static_cast<int32_t>(words[1]);"),
        ("accept object payload", "case 3:", "case 3: case 5:"),
        ("wrong positive saturation", "if (number >= 2147483648.0f) return 2147483647;",
         "if (number >= 2147483648.0f) return -2147483647 - 1;"),
        ("wrong NaN/negative saturation", "if (!(number >= -2147483648.0f)) return -2147483647 - 1;",
         "if (!(number >= -2147483648.0f)) return 0;"),
        ("round instead of truncate", "return static_cast<int32_t>(number);",
         "return static_cast<int32_t>(number + (number >= 0 ? 0.5f : -0.5f));"),
        ("lose CRT return", "return std::atoi(", "return 1 + std::atoi("),
    )),
    "swf_find_member": ("uint32_t* swfFindMember(void* list, const char* name) {", (
        ("invert hash match", "fields[4] == hash", "fields[4] != hash"),
        ("return node instead of value", "static_cast<uintptr_t>(node + 4)", "static_cast<uintptr_t>(node)"),
        ("stop after first node", "node = fields[3];", "node = 0;"),
        ("reject hash collision", "fields[4] == hash",
         "fields[4] == hash && std::strcmp(reinterpret_cast<const char*>(static_cast<uintptr_t>(fields[0])), name) == 0"),
    )),
    "swf_dispatch_clip_events": ('extern "C" void swfDispatchClipEvents(', (
        ("require exact event mask", "record[0] & static_cast<uint32_t>(event)",
         "record[0] == static_cast<uint32_t>(event)"),
        ("execute nonmatching event", "if (record[0] & static_cast<uint32_t>(event))",
         "if (!(record[0] & static_cast<uint32_t>(event)))"),
        ("execute the action header", "util_F7E8(actions + 2,", "util_F7E8(actions,"),
        ("lose VM context", "instance, actions, 0, nullptr, 0", "instance, nullptr, 0, nullptr, 0"),
        ("preserve VM stack", "instance, actions, 0, nullptr, 0", "instance, actions, 0, nullptr, 1"),
        ("prefetch next before script", "const auto* record =", "const uint32_t next = link[1];\n        const auto* record ="),
    )),
    "swf_place_object2_clip_event_update": ("void swfCMD_PlaceObject2ClipEvent::UpdateClipEvents(", (
        ("signed child depths", "*reinterpret_cast<uint16_t*>(child + 0xA6) < depth",
         "*reinterpret_cast<int16_t*>(child + 0xA6) < static_cast<int16_t>(depth)"),
        ("accept next greater depth", "if (!child || *reinterpret_cast<uint16_t*>(child + 0xA6) != depth) return;",
         "if (!child) return;"),
        ("swap record pointer and count", "*reinterpret_cast<const uint32_t*>(command + 0x28),\n                     *reinterpret_cast<const int32_t*>(command + 0x24)",
         "*reinterpret_cast<const uint32_t*>(command + 0x24),\n                     *reinterpret_cast<const int32_t*>(command + 0x28)"),
        ("dispatch load event", "swfDispatchClipEvents(child, 2, lbl_82074EF0);",
         "swfDispatchClipEvents(child, 1, lbl_82074EF0);"),
        ("wrong event name", "swfDispatchClipEvents(child, 2, lbl_82074EF0);",
         "swfDispatchClipEvents(child, 2, lbl_82074EE4);"),
    )),
}


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    total = 0
    for spec, (signature, mutations) in CASES.items():
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        body = source[start:end]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, "mutation anchor changed")
            broken = body.replace(old, new)
            if name == "prefetch next before script":
                broken = broken.replace("node = link[1];", "node = next;")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=1200, seed=1, patches=((body, broken),),
                                     workdir=root / "tools/lift-check/build/swf-hot-mutations")).run()
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
