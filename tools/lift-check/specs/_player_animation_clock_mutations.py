"""Break the normalized clock and replay-rate curve independently."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_advance_auxiliary_animation_clock", "wrong replay mode", "0x68CF0) == 1", "0x68CF0) == 0"),
    ("player_advance_auxiliary_animation_clock", "drop duration normalization", "g_sysTimeManager.frameSeconds / duration", "g_sysTimeManager.frameSeconds"),
    ("player_advance_auxiliary_animation_clock", "unordered duration divides", "duration > 0.0f ? g_sysTimeManager.frameSeconds / duration : 0.0f", "duration <= 0.0f ? 0.0f : g_sysTimeManager.frameSeconds / duration"),
    ("player_advance_auxiliary_animation_clock", "strict reset boundary", "phase >= 1.0f", "phase > 1.0f"),
    ("player_advance_auxiliary_animation_clock", "omit replay rate", "__builtin_fmaf(scaled, rate,", "__builtin_fmaf(scaled, 1.0f,"),
    ("player_replay_animation_rate", "ignore paused curve gate", "at<uint8_t>(replay, 0x68CFE) == 0", "true"),
    ("player_replay_animation_rate", "wrong ramp split", "amplitude <= 0.5f", "amplitude <= 0.25f"),
    ("player_replay_animation_rate", "omit decline from hold span", "(hold + fallSpan) + riseSpan", "hold + riseSpan"),
    ("player_replay_animation_rate", "reverse tail sign", "amplitude = -__builtin_fmaf(tail, tailRate, -amplitude);", "amplitude = __builtin_fmaf(tail, tailRate, -amplitude);"),
    ("player_replay_animation_rate", "omit neutral rate", "if (neutral) rate = 1.0f;", "if (neutral) rate = 0.0f;"),
    ("player_replay_animation_rate", "accept negative override", "overrideRate >= 0.0f", "true"),
    ("player_replay_animation_rate", "drop final time scale", "return at<float>(replay, 0x68D0C) * rate;", "return rate;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/game/player/player_animation_clock.cpp").read_text()
    for spec, label, old, new in CASES:
        assert source.count(old) == 1, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
