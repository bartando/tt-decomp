"""0x82474D60 (phBound_7): XAudio stereo PCM16 linear resampler and gain ramp.

Exact comparisons, no ignored memory or modeled DSP calls. Covers negative
history phase, fractional/whole steps, up/downsampling, zero/full output, empty
or exhausted input, final-frame history, overshoot, unequal gain endpoints,
signed PCM limits and unaligned vector-load positions. Guards and untouched
planar samples retain random bytes. Gain/history include signed zero and
subnormals. The name is descriptive, not a recovered SDK symbol.

Domain: distinct input/output/state storage, stereo input, 0..256 output frames,
0 < rate <= 16 (including steps quantized to zero), -1 <= phase <= 4, at most
1000 input frames, and valid offsets. The history path requires one readable frame, even
when inputFrames is zero. This verifies lift-check's exact-reciprocal VMX model;
hardware reciprocal estimates and dot-product rounding remain unverified.
"""

FUNCTION = "XAudioResampler_ProcessStereoPcm16"
ADDRESS = 0x82474D60
SOURCE = "src/rage/audio/xaudio_resampler.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    state = t.alloc(88, "stream", ctype="XAudioResampleState")
    pcm = t.alloc(4 * 1024 + 32, "interleavedPcm16") + rng.choice([0, 2, 4, 6, 8, 10, 12, 14])
    output = t.alloc(2 * 1024 + 32, "planarOutput") + rng.choice([0, 4, 8, 12])
    count = rng.choice([0, 1, 2, 3, 7, 31, 64, 127, 256, 511, 1000])
    offset = rng.choice([0, count, rng.randrange(count + 1)])
    output_count = rng.choice([0, 1, 2, 3, 7, 31, 64, 127, 255, 256])
    output_offset = rng.choice([0, output_count, rng.randrange(output_count + 1)])
    for i in range(2048):
        t.w16(pcm + 2 * i, rng.choice([-32768, -32767, -1, 0, 1, 32766, 32767,
                                     rng.randrange(-32768, 32768)]))
    rate = rng.choice([2**-33, 2**-16, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0,
                       3.25, 16.0, rng.uniform(0.1, 4.0)])
    phase = rng.choice([-1.0, -0.99999994, -0.75, -0.5, -2**-32, -2**-33,
                        -0.0, 0.0, 2**-32, 0.25, 0.5, 0.99999994, 1.0, 2.5,
                        rng.uniform(-1, 4)])
    gains = [-2.0, -0.0, 0.0, 0.25, 0.5, 1.0, 2.0, 2**-149, -2**-140, 2**-126]
    current = rng.choice(gains + [rng.uniform(-4, 4)])
    target = rng.choice([current, rng.choice(gains), rng.uniform(-4, 4)])
    t.w32(state, pcm)
    t.w32(state + 4, count)
    t.w32(state + 8, offset)
    t.w8(state + 12, 1)  # signed PCM16 format
    t.w8(state + 13, 2)
    t.w32(state + 20, output)
    t.w32(state + 24, output_count)
    t.w32(state + 28, output_offset)
    for off, value in [(36, current), (40, target), (44, rate), (48, phase)]:
        t.wf32(state + off, value)
    for channel in range(2):
        t.wf32(state + 52 + 4 * channel, rng.choice(gains + [rng.uniform(-1, 1)]))
    t.args(r3=state)
