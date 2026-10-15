// ═════════════════════════════════════════════════════════════════════════════
// XAudio reverb filter kernels (filed as phInst_*_p39, not physics)
// ═════════════════════════════════════════════════════════════════════════════
//
// The symbol map puts 0x824621E0..0x82462C38 under phInst, but nothing here
// touches a physics object. These are the leaf filters of XAudio's reverb
// effect, statically linked SDK code without RTTI:
//   - their only caller is the reverb's render routine 0x824631B8, called
//     from slot 15 (0x824648F8) of the effect whose vtable is 0x820058B0;
//   - that class's scalar deleting destructor (0x82464888) frees through the
//     heap at 0x825E7888 with XALLOC attributes 0x61820000: allocator id 0x82,
//     eXALLOCAllocatorId_XAUDIO;
//   - 0x82461498 in the same block unregisters an XAudio render-driver client.
// Probably the I3DL2 reverb (.rdata holds the I3DL2_ENVIRONMENT_PRESET_*
// names). They sit in this file only because it already hosts that block's
// helpers under physics names (ph_vt57D8_*); they belong in an audio file.
//
// 0x824631B8 runs each channel through one chain of these:
//   0x82461B00 (input stage, not lifted) -> ReverbLowPass
//   -> ReverbTapDelay3<512> -> ReverbAllpass<128> -> ReverbTapDelay3<2048>
//   -> ReverbAllpass<256> -> ReverbAllpass<512> (out of place)
//   -> ReverbTapDelay2<1024>
// and later feeds ReverbTapDelay2's first output through two in-place
// ReverbAllpass<512>. The state sizes asserted below are the distances
// between the consecutive filter states inside the effect.
//
// All kernels but the low-pass hard-code a 256-sample block. Each writes its
// output one sample late: out[0] gets the last sample of the previous block
// (kept in the state) and the block's own samples go to out[1..256], so the
// buffers between stages hold 257 floats.

static const uint32_t kReverbBlockSamples = 256;

// Two one-pole low-passes in series. 0x824631B8 keeps one per channel at
// +0x200A8 and +0x200C8.
struct ReverbLowPass {
    uint8_t _unk00[0x10];  // not read by Process
    float   stage1;        // +0x10  first pole's output
    float   stage2;        // +0x14  second pole's output, the last sample written
    float   gain;          // +0x18
    float   coefficient;   // +0x1C  pole: y = c*y + (1-c)*gain*x

    void Process(const float* in, float* out, uint32_t sampleCount);
};
static_assert(sizeof(ReverbLowPass) == 0x20, "two sit back to back at +0x200A8");

// One read tap of a ReverbTapDelay. Laid out in 12-byte steps in both delay
// kinds; lastOut is the last sample this tap's output buffer got.
struct ReverbTap {
    uint32_t delay;    // samples behind the write position
    float    gain;
    float    lastOut;
};

// Delay line with three taps: outA = tap 0 + tap 1, outB = tap 2. The history
// is written a whole block at a time from writePos without wrapping. That
// holds as long as writePos starts at a multiple of 256: it only ever moves
// by 256, modulo kLength.
template <uint32_t kLength>
struct ReverbTapDelay3 {
    ReverbTap taps[3];           // +0x00  taps[1].lastOut (+0x14) is never touched
    uint32_t  writePos;          // +0x24
    uint8_t   _unk28[4];
    float     history[kLength];  // +0x2C

    void Process(const float* in, float* outA, float* outB, uint32_t sampleCount);
};
static_assert(sizeof(ReverbTapDelay3<512>) == 0x82C, "state spacing in 0x824631B8");
static_assert(sizeof(ReverbTapDelay3<2048>) == 0x202C, "state spacing in 0x824631B8");

// Delay line with two taps, one output each; history written as above.
template <uint32_t kLength>
struct ReverbTapDelay2 {
    ReverbTap taps[2];           // +0x00
    uint32_t  writePos;          // +0x18
    uint8_t   _unk1C[4];
    float     history[kLength];  // +0x20

    void Process(const float* in, float* outA, float* outB);
};
static_assert(sizeof(ReverbTapDelay2<1024>) == 0x1020, "state spacing in 0x824631B8");

// Schroeder allpass: w = x + feedback*d, y = d + feedforward*w, where d is w
// from `delay` samples ago. The history holds w.
template <uint32_t kLength>
struct ReverbAllpass {
    uint32_t delay;              // +0x00
    float    feedforward;        // +0x04
    float    feedback;           // +0x08
    float    lastOut;            // +0x0C
    uint32_t writePos;           // +0x10
    uint8_t  _unk14[4];
    float    history[kLength];   // +0x18

    void ProcessInPlace(float* samples);
    void Process(float* in, float* out);

    // One sample, inlined into every kernel
    float Step(float x, uint32_t readPos, uint32_t writeIndex) {
        const float delayed = history[readPos & (kLength - 1)];
        const float w = x + feedback * delayed;
        history[writeIndex] = w;
        return delayed + feedforward * w;
    }
};
static_assert(sizeof(ReverbAllpass<128>) == 0x218, "state spacing in 0x824631B8");
static_assert(sizeof(ReverbAllpass<256>) == 0x418, "state spacing in 0x824631B8");
static_assert(sizeof(ReverbAllpass<512>) == 0x818, "state spacing in 0x824631B8");

/**
 * ReverbLowPass::Process @ 0x824621E0 | size: 0x12C  (was phInst_21E0_p39)
 *
 * Filters sampleCount samples (256 from 0x824631B8) through two one-pole
 * low-passes in series, both scaled by gain. The second pole takes the first
 * one's output from the previous sample.
 *
 * The binary unrolls the loop by four and, for three of every four samples,
 * forms (x*gain)*(1-c) instead of x*(gain*(1-c)): equal up to rounding.
 */
void ReverbLowPass::Process(const float* in, float* out, uint32_t sampleCount) {
    float y1 = stage1;
    float y2 = stage2;
    out[0] = y2;

    const float c = coefficient;
    const float inputScale = gain * (1.0f - c);  // 1.0f from .rdata 0x82003DAC
    for (uint32_t i = 0; i < sampleCount; ++i) {
        const float previous1 = y1;
        y1 = c * y1 + inputScale * in[i];
        y2 = inputScale * previous1 + c * y2;
        out[i + 1] = y2;
    }

    stage1 = y1;
    stage2 = y2;
}

/**
 * ReverbTapDelay3<kLength>::Process
 *   <512>  @ 0x82462310 | size: 0xCC  (was phInst_2310_p39)
 *   <2048> @ 0x82462678 | size: 0xCC  (was phInst_2678_p39)
 *
 * Writes one block of input into the delay line and reads three taps behind
 * it: outA gets taps 0 and 1 mixed, outB tap 2. The taps are read before the
 * new sample is stored, so a zero delay returns the old contents.
 * The caller passes the block length (256) as a fifth argument; both copies
 * ignore it and run 256 samples.
 */
template <uint32_t kLength>
void ReverbTapDelay3<kLength>::Process(const float* in, float* outA, float* outB,
                                       uint32_t /*sampleCount*/) {
    const uint32_t mask = kLength - 1;
    const uint32_t pos = writePos;
    const float gain0 = taps[0].gain;
    const float gain1 = taps[1].gain;
    const float gain2 = taps[2].gain;

    float a = taps[0].lastOut;
    float b = taps[2].lastOut;
    outA[0] = a;
    outB[0] = b;

    for (uint32_t i = 0; i < kReverbBlockSamples; ++i) {
        const float tap1 = history[(pos + i - taps[1].delay) & mask];
        const float tap0 = history[(pos + i - taps[0].delay) & mask];
        const float tap2 = history[(pos + i - taps[2].delay) & mask];
        history[pos + i] = in[i];

        b = tap2 * gain2;
        outB[i + 1] = b;
        a = tap0 * gain0 + tap1 * gain1;
        outA[i + 1] = a;
    }

    taps[0].lastOut = a;
    taps[2].lastOut = b;
    writePos = (pos + kReverbBlockSamples) & mask;
}

template void ReverbTapDelay3<512>::Process(const float*, float*, float*, uint32_t);   // @ 0x82462310
template void ReverbTapDelay3<2048>::Process(const float*, float*, float*, uint32_t);  // @ 0x82462678

/**
 * ReverbTapDelay2<1024>::Process @ 0x82462B90 | size: 0xA8  (was phInst_2B90_p39)
 *
 * Same as ReverbTapDelay3 with two taps and no mixing: outA gets tap 0,
 * outB tap 1.
 */
template <uint32_t kLength>
void ReverbTapDelay2<kLength>::Process(const float* in, float* outA, float* outB) {
    const uint32_t mask = kLength - 1;
    const uint32_t pos = writePos;
    const float gain0 = taps[0].gain;
    const float gain1 = taps[1].gain;

    float a = taps[0].lastOut;
    float b = taps[1].lastOut;
    outA[0] = a;
    outB[0] = b;

    for (uint32_t i = 0; i < kReverbBlockSamples; ++i) {
        const float tap0 = history[(pos + i - taps[0].delay) & mask];
        const float tap1 = history[(pos + i - taps[1].delay) & mask];
        a = tap0 * gain0;
        history[pos + i] = in[i];
        b = tap1 * gain1;
        outA[i + 1] = a;
        outB[i + 1] = b;
    }

    taps[0].lastOut = a;
    taps[1].lastOut = b;
    writePos = (pos + kReverbBlockSamples) & mask;
}

template void ReverbTapDelay2<1024>::Process(const float*, float*, float*);  // @ 0x82462B90

/**
 * ReverbAllpass<kLength>::ProcessInPlace
 *   <256> @ 0x82462748 | size: 0x16C  (was phInst_2748_p39)
 *   <512> @ 0x824628B8 | size: 0x16C  (was phInst_28B8_p39)
 *
 * Runs one block through the allpass in place. samples[] holds 257 floats:
 * samples[i] is read before it is replaced by the previous output, and the
 * block's last output also lands in samples[256]. History writes don't wrap
 * (see ReverbTapDelay3); for <256> writePos never moves.
 */
template <uint32_t kLength>
void ReverbAllpass<kLength>::ProcessInPlace(float* samples) {
    const uint32_t pos = writePos;
    float y = lastOut;
    for (uint32_t i = 0; i < kReverbBlockSamples; ++i) {
        const float x = samples[i];
        samples[i] = y;
        y = Step(x, pos + i - delay, pos + i);
    }
    lastOut = y;
    samples[kReverbBlockSamples] = y;
    writePos = (pos + kReverbBlockSamples) & (kLength - 1);
}

/**
 * ReverbAllpass<128>::ProcessInPlace @ 0x824623E0 | size: 0x298  (was phInst_23E0_p39)
 *
 * The 128-sample line is half a block, so this copy runs the block as two
 * loops: the first writes the history from writePos, the second from 0 and
 * reads relative to 0, i.e. it assumes writePos was 0. writePos is left 0.
 */
template <>
void ReverbAllpass<128>::ProcessInPlace(float* samples) {
    const uint32_t half = kReverbBlockSamples / 2;
    const uint32_t pos = writePos;
    float y = lastOut;
    for (uint32_t i = 0; i < half; ++i) {
        const float x = samples[i];
        samples[i] = y;
        y = Step(x, pos + i - delay, pos + i);
    }
    for (uint32_t i = 0; i < half; ++i) {
        const float x = samples[half + i];
        samples[half + i] = y;
        y = Step(x, i - delay, i);
    }
    lastOut = y;
    samples[kReverbBlockSamples] = y;
    writePos = 0;
}

template void ReverbAllpass<256>::ProcessInPlace(float*);  // @ 0x82462748
template void ReverbAllpass<512>::ProcessInPlace(float*);  // @ 0x824628B8

/**
 * ReverbAllpass<512>::Process @ 0x82462A28 | size: 0x168  (was phInst_2A28_p39)
 *
 * ReverbAllpass::ProcessInPlace with a separate output: out[0] gets the
 * previous block's last output and out[i + 1] sample i's, except that the
 * block's last output goes to in[256], not out[256], which stays untouched.
 * The binary does exactly that; the next stage only reads out[0..255].
 */
template <uint32_t kLength>
void ReverbAllpass<kLength>::Process(float* in, float* out) {
    const uint32_t pos = writePos;
    float y = lastOut;
    for (uint32_t i = 0; i < kReverbBlockSamples; ++i) {
        const float x = in[i];
        out[i] = y;
        y = Step(x, pos + i - delay, pos + i);
    }
    lastOut = y;
    in[kReverbBlockSamples] = y;
    writePos = (pos + kReverbBlockSamples) & (kLength - 1);
}

template void ReverbAllpass<512>::Process(float*, float*);  // @ 0x82462A28
