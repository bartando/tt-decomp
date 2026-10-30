"""Run from repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_fx_crowd_anim_playback_update_mutations.py

Mutates build-cache copies only. Baselines must pass on both seeds; only a
behavioral FAIL (1) counts as caught, never BUILD/SPEC/UNSUPPORTED or a crash
of this driver. No source files are changed by running this script.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("wrong RNG multiplier", "* 0x5CDCFAA7u", "* 0x5CDCFAA9u"),
    ("drop RNG carry", "+ g_prngState[1]", "+ 0u"),
    ("wrong random mask", "uint32_t(next) & 0x7FFFFF", "uint32_t(next) & 0x3FFFFF"),
    ("fuse range product into final addition",
     "__builtin_fmaf(product, 0x1p-23f, clip->minSpeed)",
     "__builtin_fmaf(clip->maxSpeed - clip->minSpeed, "
     "float(uint32_t(next) & 0x7FFFFF) * 0x1p-23f, clip->minSpeed)"),
    ("read old queue slot", "return self->queue[self->readIndex];",
     "return self->queue[1 - self->readIndex];"),
    ("forget queue count", "--self->queued;", "/* omit decrement */"),
    ("miss special type 11", "self->current->type == 11", "self->current->type == 12"),
    ("consume queue in outro", "&& self->state != 2", "&& true"),
    ("drop deferred transition", "self->finishCurrent = 1;", "self->finishCurrent = 0;"),
    ("omit delay scale", "randomSpeed(self->next) * self->next->delayScale",
     "randomSpeed(self->next)"),
    ("blend before delay expires", "self->next && self->delay <= 0.0f", "self->next != nullptr"),
    ("exclude zero delay", "self->delay <= 0.0f", "self->delay < 0.0f"),
    ("reverse delay tick", "self->delay -= lbl_825CAEB8[2]", "self->delay += lbl_825CAEB8[2]"),
    ("ignore clip duration", "duration * self->currentPhase", "self->currentPhase"),
    ("evaluate next into current frame",
     "self->nextFrame, 0, 1, nextDuration", "self->currentFrame, 0, 1, nextDuration"),
    ("advance next as current", "&self->nextPhase, self->next, 0",
     "&self->nextPhase, self->next, 1"),
    ("omit wrapped-phase substitution", "self->nextPhase == 0.0f ? 1.0f : self->nextPhase",
     "self->nextPhase"),
    ("ignore fade-out reflection", "phase = 1.0f - phase;", "phase = phase;"),
    ("wrong fade ratio", "weight = phase / fade;", "weight = phase * fade;"),
    ("fail to clamp unordered blend", "weight >= 0.0f ? weight : 0.0f",
     "weight < 0.0f ? 0.0f : weight"),
    ("promote at half weight", "self->blendWeight >= 1.0f", "self->blendWeight >= 0.5f"),
    ("advance again after promotion", "advanceCurrent = false;", "advanceCurrent = true;"),
    ("skip outro phase", "self->state = 2;", "self->state = 0;"),
    ("retain completed current", "self->current = nullptr;", "/* retain current */"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/graphics/fx_crowd.cpp").read_text()
    spec = Path(__file__).with_name("fx_crowd_anim_playback_update.py")
    for seed in (1, 7):
        if Checker(spec, Options(seed=seed)).run() != 0:
            return 1
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        lines = output.getvalue().splitlines()
        first = lines[0] if lines else "no checker output"
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
