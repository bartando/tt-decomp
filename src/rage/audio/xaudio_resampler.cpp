#include <cstddef>
#include <cstdint>

// Prefix of the SDK render-stream state used by XmaRenderStream_Process.
struct XAudioResampleState {
    const int16_t* input;
    uint32_t inputFrames;
    uint32_t inputOffset;
    uint8_t format;
    uint8_t channels;
    uint8_t reserved0[6];
    float* output;                    // planar, 256 samples per channel
    uint32_t outputFrames;
    uint32_t outputOffset;
    uint32_t reserved1;
    float currentGain;
    float targetGain;
    float rate;
    float phase;
    float history[2];
};

static_assert(sizeof(void*) != 4 || offsetof(XAudioResampleState, output) == 20);
static_assert(sizeof(void*) != 4 || offsetof(XAudioResampleState, currentGain) == 36);
static_assert(sizeof(void*) != 4 || offsetof(XAudioResampleState, history) == 52);

// VMX flushes both subnormal operands and results, retaining the zero sign.
static inline __attribute__((always_inline)) float resampleFlush(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7f800000u) == 0) bits &= 0x80000000u;
    __builtin_memcpy(&value, &bits, sizeof(value));
    return value;
}

static inline __attribute__((always_inline)) float resampleMultiply(float a, float b) {
    return resampleFlush(resampleFlush(a) * resampleFlush(b));
}

static inline __attribute__((always_inline)) float resampleAdd(float a, float b) {
    return resampleFlush(resampleFlush(a) + resampleFlush(b));
}

static inline __attribute__((always_inline)) float resampleFraction(int64_t phase) {
    uint32_t low = static_cast<uint32_t>(phase);
    // vsr shifts the entire splatted 128-bit register, carrying bit 0 from the
    // preceding word into bit 31. The dot uses lanes 2/3, not the first lane.
    return static_cast<float>((low >> 1) | (low << 31)) * 0x1p-31f;
}

static inline __attribute__((always_inline)) float resampleInterpolate(
    float first, float second, float fraction, float gain) {
    float positive = resampleMultiply(fraction, gain);
    float negative = resampleMultiply(fraction, resampleAdd(0.0f, -gain));
    // vmsum3fp: retain the three products and their order, rather than rewriting
    // as (first + (second-first)*fraction)*gain. The dot rounds only at the end.
    double sum = 0.0;
    sum += double(resampleFlush(second)) * double(positive);
    sum += double(resampleFlush(first)) * double(negative);
    sum += double(resampleFlush(first)) * double(resampleFlush(gain));
    return resampleFlush(static_cast<float>(sum));
}

// @ 0x82474D60
// Formerly phBound_7. Descriptive name inferred from the PCM16 loads, stereo
// planar stores and resampler dispatcher at 0x8247C080; no SDK symbol recovered.
// Valid stream state has two channels, positive finite rate and <=256 outputs.
void XAudioResampler_ProcessStereoPcm16(XAudioResampleState* state) {
    constexpr int64_t ONE = int64_t(1) << 32;
    const int16_t* input = state->input + state->inputOffset * state->channels;
    int32_t available = static_cast<int32_t>(state->inputFrames - state->inputOffset);
    int32_t remaining = static_cast<int32_t>(state->outputFrames - state->outputOffset);
    uint32_t outputIndex = state->outputOffset;
    float gain = state->currentGain;
    float difference = resampleAdd(state->targetGain, -gain);
    float reciprocal = resampleFlush(1.0f / static_cast<float>(remaining));
    float gainStep = resampleMultiply(difference, reciprocal);
    int64_t phase = static_cast<int64_t>(double(state->phase) * double(ONE));
    int64_t step = static_cast<int64_t>(double(state->rate) * double(ONE));

    // Before the new buffer starts, interpolate its first frame with history.
    while (phase < 0 && remaining > 0) {
        float fraction = resampleFraction(phase);
        phase += step;
        --remaining;
        state->output[outputIndex + 256] = resampleInterpolate(
            state->history[1], float(input[1]) * 0x1p-15f, fraction, gain);
        state->output[outputIndex] = resampleInterpolate(
            state->history[0], float(input[0]) * 0x1p-15f, fraction, gain);
        gain = resampleAdd(gain, gainStep);
        ++outputIndex;
    }

    // Initial sradi(32)-sradi(63) adds one for every negative phase, including
    // exact integers. Subsequent sradi instructions simply floor.
    int64_t index = (phase >> 32) + (phase < 0 ? 1 : 0);
    int64_t last = int64_t(available) - 1;
    while (index < last && remaining != 0) {
        float fraction = resampleFraction(phase);
        const int16_t* first = input + index * 2;
        const int16_t* second = first + 2;
        phase += step;
        --remaining;
        state->output[outputIndex + 256] = resampleInterpolate(
            float(first[1]) * 0x1p-15f, float(second[1]) * 0x1p-15f, fraction, gain);
        state->output[outputIndex] = resampleInterpolate(
            float(first[0]) * 0x1p-15f, float(second[0]) * 0x1p-15f, fraction, gain);
        gain = resampleAdd(gain, gainStep);
        ++outputIndex;
        index = phase >> 32;
    }

    if (remaining != 0) {
        if (index == last) {
            state->history[1] = float(input[last * 2 + 1]) * 0x1p-15f;
            state->history[0] = float(input[last * 2]) * 0x1p-15f;
            ++index;
        } else if (index > available) {
            phase += (index - available) * ONE;
        }
    }
    phase -= index * ONE;
    state->currentGain = gain;
    state->phase = static_cast<float>(double(phase) * 0x1p-32);
    uint32_t consumed = state->inputOffset + static_cast<uint32_t>(index);
    state->inputOffset = consumed < state->inputFrames ? consumed : state->inputFrames;
    state->outputOffset = outputIndex < state->outputFrames ? outputIndex : state->outputFrames;
}
