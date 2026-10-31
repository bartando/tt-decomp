"""Run: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this_file.

Only build-cache copies are mutated. Only a behavioral FAIL counts as caught;
BUILD, SPEC, UNSUPPORTED, exceptions and timeouts never count as successes.
The specs themselves default to 1200 trials; mutations use 256, seed 1.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = {
    "sg_typed_iterator_prime": (
        "src/scene/sg_scene_graph.cpp", [
            ("type ID address instead of value", "isType(current, g_sgNode_typeId)",
             "isType(current, 0x825C93D0u)"),
            ("full-word type result", "& 0xFFu) != 0", "& 0xFFFFFFFFu) != 0"),
            ("wrong type slot", "current->vtable[20]", "current->vtable[21]"),
            ("cached cursor after type callback", "m_pCurrent->vtable[19])(m_pCurrent)",
             "current->vtable[19])(current)"),
            ("omit skip log", "nop_8240E6D0(kTypeMismatchFmt, name);", "(void)name;"),
            ("omit skip advance", "    Advance();\n}", "    /* missing advance */\n}"),
        ]),
    "sg_typed_iterator_advance": (
        "src/scene/sg_scene_graph.cpp", [
            ("drop child descent", "next = current->m_pFirstChild;", "next = nullptr;"),
            ("walk beyond root", "} else if (current != m_pRoot)", "} else if (true)"),
            ("drop direct sibling", "next = current->m_pNextSibling;", "next = nullptr;"),
            ("drop ancestor search", "next = FindAncestorSibling(parent);", "next = nullptr;"),
            ("omit cursor publication", "    m_pCurrent = next;", "    (void)next;"),
            ("omit type filtering", "    Prime();\n}", "    /* missing prime */\n}"),
        ]),
    "pong_match_get_character_for_slot": (
        "src/game/player/pong_player.cpp", [
            ("reject loaded manager on odd slots", "if (!g_plrPlayerMgr_state)",
             "if (!g_plrPlayerMgr_state || (playerSlot & 1))"),
            ("omit missing-manager log", "nop_8240E6D0(g_pongMatchMissingPlayerMgr);",
             "/* missing diagnostic */"),
            ("wrong player slot", "pongMatch_GetCharacterIndex(playerSlot);",
             "pongMatch_GetCharacterIndex(playerSlot ^ 1u);"),
            ("wrong fallback character", "uint32_t characterIndex = 0;", "uint32_t characterIndex = 1;"),
            ("ignore selected character", "const uint32_t byteOffset = characterIndex * 4u;", "const uint32_t byteOffset = 0;"),
            ("cache manager across resolver", "    uint32_t characterIndex = 0;", "    void* cachedManager = g_gameDataMgr;\n    uint32_t characterIndex = 0;"),
        ]),
    "aud_control_service": (
        "src/rage/audio/rage_audio.cpp", [
            ("poll state 1 immediately", "            *reinterpret_cast<int32_t*>(self + 0x10) = 2;",
             "            *reinterpret_cast<int32_t*>(self + 0x10) = 2;\n            state = 2;"),
            ("test only low voice bit", "(voiceVtbl[18])(voice) & 0xFFu;\n            if (playing == 0)",
             "(voiceVtbl[18])(voice) & 0x1u;\n            if (playing == 0)"),
            ("retain releasing state", "                *reinterpret_cast<int32_t*>(self + 0x10) = 0;",
             "                /* state clear lost */"),
            ("release stale voice", "void*  voiceAgain = *reinterpret_cast<void**>(self + 0x04);",
             "void*  voiceAgain = voice;"),
            ("retain released voice", "                *reinterpret_cast<void**>(self + 0x04) = nullptr;",
             "                /* voice clear lost */"),
            ("drop dirty flags with zero group flags", "    uint32_t groupFlags = *reinterpret_cast<uint32_t*>(group + 0x28);",
             "    uint32_t groupFlags = *reinterpret_cast<uint32_t*>(group + 0x28);\n    if (groupFlags == 0) return;"),
            ("wrong group bit mapping", "    if (groupFlags & 0x2) {\n        mFlags |= 0x4;",
             "    if (groupFlags & 0x2) {\n        mFlags |= 0x2;"),
            ("ignore master mute", "g_audMasterMuteFlag == 0 && (groupFlags & 0x1)",
             "(groupFlags & 0x1)"),
            ("wrong update argument", "(myVtbl[7])(this, mFlags);", "(myVtbl[7])(this, 0);"),
            ("retain pending flags", "    *reinterpret_cast<uint32_t*>(self + 0x14) = 0;\n}",
             "    /* pending clear lost */\n}"),
        ]),
}


def main():
    root = Path(__file__).resolve().parents[3]
    caught = 0
    for spec_name, (source_path, mutations) in CASES.items():
        source = (root / source_path).read_text()
        for name, old, new in mutations:
            patches = [(old, new)]
            if name == "cache manager across resolver":
                patches.append(("auto* manager = static_cast<uint8_t*>(g_gameDataMgr);",
                                "auto* manager = static_cast<uint8_t*>(cachedManager);"))
            for anchor, _ in patches:
                assert source.count(anchor) >= 1, f"missing mutation anchor: {name}"
                # build_lift replaces the first occurrence: state 2 for the byte mask.
                assert source.count(anchor) == (2 if name == "test only low voice bit" else 1), name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(trials=256, seed=1, patches=tuple(patches))).run()
            first = output.getvalue().splitlines()[0]
            detected = rc == 1 and first.startswith("FAIL ")
            print(f"{spec_name}: {'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
            if not detected:
                print(output.getvalue())
                return 1
            caught += 1
    print(f"Caught {caught}/{sum(len(m) for _, m in CASES.values())} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
