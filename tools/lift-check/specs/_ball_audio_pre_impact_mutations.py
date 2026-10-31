"""Behavioral mutation proof for impact selection, repeat/cooldown state and
all callback-sensitive cue/volume/gain boundaries. Only behavioral FAIL counts.
Run with PYTHONPATH=tools/lift-check and the real lift-check virtual environment.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("empty impact", "    auto* audio =", "    return 0;\n    auto* audio ="),
    ("omit third position", "    BallAudio_SetEmitterPosition(ImpactVoice(audioPtr, 0x240), position);", "    (void)position;"),
    ("disable kick cues", "lbl_825C5EC8[0x30] != 0 &&", "false &&"),
    ("disable pong cues", "const bool pong = lbl_825C5EC8[8] != 0;", "const bool pong = false;"),
    ("unordered above-table test", "position[1] >= ImpactTableHeight() - 0.11999999731779099f", "!(position[1] < ImpactTableHeight() - 0.11999999731779099f)"),
    ("include near-budget equality", "audio->hitCounter) > ImpactConfig()->nearBudget", "audio->hitCounter) >= ImpactConfig()->nearBudget"),
    ("exclude far-budget equality", "audio->repeat) >= ImpactConfig()->farBudget", "audio->repeat) > ImpactConfig()->farBudget"),
    ("unsigned hit budget", "static_cast<int32_t>(audio->hitCounter) >", "audio->hitCounter >"),
    ("ignore handled gate", "budget && audio->handled == 0", "budget && true"),
    ("ignore controller suppression", "static_cast<ImpactContext*>(g_audCtrlMgrControlPrimary)->suppressed == 0", "true"),
    ("omit discarded special-mode format", 'snprintf(cue, sizeof(cue), "%s:BALL_TABLE_BOUNCE", prefix);', 'if (!special) snprintf(cue, sizeof(cue), "%s:BALL_TABLE_BOUNCE", prefix);'),
    ("test all loop-select bits", "static_cast<uint8_t>(chosenLoop) != 0", "chosenLoop != 0"),
    ("omit handled mark", "audio->handled = 1;", "audio->handled = 0;"),
    ("extend repeat window", "elapsed < 2 &&", "elapsed <= 2 &&"),
    ("lose stamp-equality exception", "elapsed < 2 && elapsed != static_cast<int32_t>(audio->lastStamp)", "elapsed < 2"),
    ("omit repeat increment", "++audio->repeat;", "(void)audio->repeat;"),
    ("test all loop-playing bits", "static_cast<uint8_t>(loop->IsPlaying()) != 0", "loop->IsPlaying() != 0"),
    ("omit handled clear below table", "if (!above) audio->handled = 0;", "if (false) audio->handled = 0;"),
    ("ignore table suppression", "if (audio->handled != 0) return 0;", "if (false) return 0;"),
    ("unordered smash threshold", "energy >= audio->smashThreshold * 9.999999747378752e-05f", "!(energy < audio->smashThreshold * 9.999999747378752e-05f)"),
    ("wrong table-smash cue", "%s:BALL_TABLE_SMASH", "%s:BALL_TABLE_HARD"),
    ("cache config before callbacks", "    auto* audio =", "    auto const* cachedConfig = ImpactConfig();\n    auto* audio ="),
    ("cache hit counter before Select", "    auto* audio =", "    auto* audio ="),
    ("cache names before callbacks", "    auto* audio =", "    auto* audio ="),
    ("signed net cooldown age", "static_cast<float>(now - audio->netStamp)", "static_cast<float>(static_cast<int32_t>(now - audio->netStamp))"),
    ("ordered net cooldown gate", "if (age < cooldown) chosen = 0;", "if (!(age >= cooldown)) chosen = 0;"),
    ("omit net stamp", "audio->netStamp = age < cooldown ? now : ImpactClock()->stamp;", "(void)now;"),
    ("attenuate pong net too", "(g_ballAudioListener)) && !pong)", "(g_ballAudioListener)))"),
    ("wrong person volume", "volume = 0.0f;", "volume = 1.0f;"),
    ("ordered person cooldown gate", "if (static_cast<float>(now - audio->personStamp) < cooldown) chosen = 0;", "if (!(static_cast<float>(now - audio->personStamp) >= cooldown)) chosen = 0;"),
    ("constant person cooldown", "g_kPowerBlend / ImpactClock()->tick", "3.0f / ImpactClock()->tick"),
    ("omit person stamp", "audio->personStamp = now;", "(void)now;"),
    ("wrong net surface index", "if (index == 15)", "if (index == 14)"),
    ("include zero network count", "networkCount > 0", "networkCount >= 0"),
    ("constant quarter gain", "gain = g_phCapsuleShapeK;", "gain = 0.25f;"),
    ("play suppressed pong surface", "if (!(pong && index != 15)) chosen = primary->Select(cue);", "chosen = primary->Select(cue);"),
    ("test all primary-select bits", "static_cast<uint8_t>(chosen) == 0", "chosen == 0"),
    ("omit gain update", "BallAudio_SetEmitterGain(primary, gain);", "(void)gain;"),
    ("omit volume update", "fields->volume = volume;", "(void)volume;"),
    ("replace flags instead of OR", "fields->flags |= 8;", "fields->flags = 8;"),
    ("omit primary Play", "primary->Play();", "(void)primary;"),
    ("lose successful return", "    return 1;", "    return 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_audio_impact.cpp").read_text()
    start = source.index("int BallAudio_PreImpact(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    for label, old, new in MUTATIONS:
        assert old in body, f"missing mutation anchor: {label}"
        changed = body.replace(old, new)
        if label == "cache config before callbacks": changed = changed.replace("ImpactConfig()->", "cachedConfig->")
        if label == "cache hit counter before Select":
            changed = changed.replace("char cue[128] = {};", "const uint32_t cachedHits = audio->hitCounter;\n    char cue[128] = {};")
            changed = changed.replace("++audio->hitCounter;", "audio->hitCounter = cachedHits + 1;")
        if label == "cache names before callbacks":
            changed = changed.replace("char cue[128] = {};", "const char** cachedNames = audio->names;\n    char cue[128] = {};")
            changed = changed.replace("audio->names[index]", "cachedNames[index]")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_audio_pre_impact.py"), Options(
                trials=512, seed=1, patches=((body, changed),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
