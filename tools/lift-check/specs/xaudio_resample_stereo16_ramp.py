"""Stereo PCM16 fixed-point resampling with a gain ramp, 0x82470048.

Uses the real uint64-to-double callee. No ignored memory or float tolerance;
FP contraction is off to preserve the VMX kernel's separate rounding steps.
Inputs respect the caller's fast-path contract: 8-frame blocks, aligned output,
nonnegative rates/phase and a readable lookahead. Varies rate/phase, gain ramps,
PCM extrema, subnormal fade gains, initial offsets and final counter clamping.
"""
from liftcheck.spec import *

FUNCTION = "XAudioResampleStereo16_Ramp"
ADDRESS = 0x82470048
SOURCE = "src/rage/audio/xma_source.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
CALLS = {"XAudio_UInt64ToDouble": run()}


def inputs(t):
    rng = t.rng
    stream = t.alloc(88, "stream", ctype="XmaRenderStream")
    pcm = t.alloc(0x5000, "pcm16")
    output = t.alloc(0x900, "output", floats=[(0, 0x900 // 4)])
    count = rng.choice([8, 16, 24, 32, 64, 128, 256])
    initial_in = rng.choice([0, 1, 3, 7, 64])
    initial_out = rng.choice([0, 4, 8])
    rate = rng.choice([0.0, 0.125, 0.5, 1.0, 1.25, 2.0, 3.999, rng.uniform(0.001, 4)])
    phase = rng.choice([0.0, 0.25, 0.5, 0.99999, rng.random()])
    t.w32(stream, pcm)
    t.w32(stream + 4, rng.choice([0, 1, 100, 4096, 0xffffffff]))
    t.w32(stream + 8, initial_in)
    t.w8(stream + 13, 2)
    t.w32(stream + 20, output)
    t.w32(stream + 24, rng.choice([0, 1, 64, 256, 0xffffffff]))
    t.w32(stream + 28, initial_out)
    for off in (36, 40):
        t.wf32(stream + off, rng.choice([0, 1, -1, 0.5, 1e-40, -1e-40,
                                       2.0**-126, rng.uniform(-4, 4)]))
    t.wf32(stream + 44, rate)
    t.wf32(stream + 48, phase)
    # Random PCM plus frequent exact endpoints, alternating signs and zero runs.
    if rng.randrange(3) == 0:
        samples = [0, 32767, -32768, -1, 1, 16384, -16384, 12345]
        for i in range(0, 0x5000, 2):
            t.w16(pcm + i, samples[(i // 2) % len(samples)])
    t.args(r3=pcm + initial_in * 4, r4=4096, r5=output + initial_out * 4,
           r6=count, r7=stream)
