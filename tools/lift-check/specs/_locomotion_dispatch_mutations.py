"""Mutation proof for 88E0, BEF8 and BB98. Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_locomotion_dispatch_mutations.py

Only build-cache copies are patched. A behavioral FAIL (exit 1) is required;
BUILD, SPEC and UNSUPPORTED never count as caught. Each replacement is scoped
to the target body and must have exactly one anchor. The checked-in lifts
are left intact, including when the proof fails.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = [
    ("locomotion_state_anim_88e0", "src/anim/locomotion.cpp",
     "bool LocomotionStateAnim_88E0_g(", [
         ("empty dispatch", "    (void)unusedR4;", "    return false;\n    (void)unusedR4;"),
         ("wrong sample count", "clip + 10", "clip + 8"),
         ("omit sample-count decrement", "sampleCount - 1", "sampleCount"),
         ("skip integral rounding", "if ((integralFrames & 0xFF) != 0)", "if (false)"),
         ("use full integral flag", "integralFrames & 0xFF", "integralFrames"),
         ("use full reset flag", "flags & 0xFF", "flags"),
         ("wrong clip type byte", "uint32_t(channel[0])", "uint32_t(channel[1])"),
         ("reverse merge ordering", "if (channelKey > key)", "if (channelKey < key)"),
         ("reuse matched clip channel", "++clipIndex;", "if (channelKey != key) ++clipIndex;"),
         ("wrong evaluation slot", "vtable[4](entry, sample)", "vtable[3](entry, sample)"),
         ("omit unmatched resets", "if (!found && resetUnmatched)", "if (false)"),
         ("always report complete", "return matched == frameCount;", "return true;"),
     ]),
    ("locomotion_state_anim_bef8", "src/game/creature/pong_creature.cpp",
     "void* LocomotionStateAnim::FindAnimationByID(", [
         ("signed count", "*reinterpret_cast<uint16_t*>(bytes + 12)",
          "*reinterpret_cast<int16_t*>(bytes + 12)"),
         ("read count as uint32", "*reinterpret_cast<uint16_t*>(bytes + 12)",
          "*reinterpret_cast<uint32_t*>(bytes + 12)"),
         ("read table as uint64", "*reinterpret_cast<void***>(bytes + 8)",
          "reinterpret_cast<void**>(static_cast<uintptr_t>(*reinterpret_cast<uint64_t*>(bytes + 8)))"),
         ("unmasked type", "type & 0xFF", "type"),
         ("truncate ID to byte", "id & 0xFFFF", "id & 0xFF"),
         ("unmasked ID", "id & 0xFFFF", "id"),
         ("wrong entry ID offset", "channel + 6", "channel + 4"),
         ("reverse search ordering", "if (entryKey > searchKey)", "if (entryKey < searchKey)"),
         ("skip lower neighbor", "high = mid - 1;", "high = mid - 2;"),
         ("reject exact hits", "return entry;", "return nullptr;"),
     ]),
    ("locomotion_state_anim_bb98", "src/game/creature/pong_creature.cpp",
     "void LocomotionStateAnim_BB98(", [
         ("empty thunk", "    VCALL(entry", "    return;\n    VCALL(entry"),
         ("wrong virtual slot", "VCALL(entry, 7,", "VCALL(entry, 6,"),
         ("use destination as source", "entry, source, weight, unusedR5, flags", "entry, entry, weight, unusedR5, flags"),
         ("drop weight", "entry, source, weight, unusedR5, flags", "entry, source, 0.0f, unusedR5, flags"),
         ("drop r5", "entry, source, weight, unusedR5, flags", "entry, source, weight, 0, flags"),
         ("drop flags", "entry, source, weight, unusedR5, flags", "entry, source, weight, unusedR5, 0"),
         ("swap integer arguments", "entry, source, weight, unusedR5, flags", "entry, source, weight, flags, unusedR5"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
