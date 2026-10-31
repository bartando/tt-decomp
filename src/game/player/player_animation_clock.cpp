// Advance normalized auxiliary clip time at the current live/replay rate.
#include <cstdint>

extern "C" void* g_pReplayStateData; // @ 0x8271A2EC
struct AnimationClockTimeManager {
    void* vtable;
    uint32_t reserved;
    float frameSeconds;
};
extern "C" AnimationClockTimeManager g_sysTimeManager; // @ 0x825CAEB8

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x821CCBD0 | size: 0x1A4
float util_CBD0(void* replay) {
    float rate = at<float>(replay, 0x68CEC);
    void* list = at<void*>(replay, 0x68D10);
    if (at<uint8_t>(replay, 0x68CFE) == 0 && list && at<uint16_t>(list, 4) > 0
        && at<int32_t>(replay, 0x68D14) >= 0) {
        float amplitude = at<float>(replay, 0x68D24);
        bool neutral = amplitude < 0.0f;
        if (!neutral) {
            const float scaled = amplitude * at<float>(replay, 0x68D3C);
            const float riseRate = at<float>(replay, 0x68D2C);
            const float fallRate = at<float>(replay, 0x68D30);
            const float elapsed = at<float>(replay, 0x68D28);
            const float riseSpan = scaled / riseRate;
            const float fallSpan = (scaled - amplitude) / fallRate;
            if (elapsed < riseSpan) {
                amplitude = elapsed * riseRate;
            } else if (elapsed < fallSpan + riseSpan) {
                const float decline = (elapsed - riseSpan) * fallRate;
                amplitude = __builtin_fmaf(amplitude, at<float>(replay, 0x68D3C), -decline);
            } else {
                const float hold = at<float>(replay, 0x68D34);
                if (!(elapsed < (hold + fallSpan) + riseSpan)) {
                    const float tailRate = at<float>(replay, 0x68D38);
                    const float end = ((amplitude / tailRate + hold) + fallSpan) + riseSpan;
                    if (!(elapsed < end)) {
                        neutral = true;
                    } else {
                        const float tail = ((elapsed - riseSpan) - fallSpan) - hold;
                        amplitude = -__builtin_fmaf(tail, tailRate, -amplitude);
                    }
                }
            }
            neutral = neutral || amplitude == 0.0f;
        }
        if (neutral) rate = 1.0f;
        else if (amplitude <= 0.5f) {
            const float ramp = (rate - 1.0f) * amplitude;
            rate = __builtin_fmaf(ramp, 2.0f, 1.0f);
        } else {
            const float ramp = (amplitude - 0.5f) * -rate;
            rate = __builtin_fmaf(ramp, 2.0f, rate);
        }
    }
    const float overrideRate = at<float>(replay, 0x68D04);
    if (overrideRate >= 0.0f) rate = overrideRate * rate;
    return at<float>(replay, 0x68D0C) * rate;
}

// @ 0x820C28B0 | size: 0xD0
void LocomotionStateAnim_28B0_w(void* entry) {
    float rate = 1.0f;
    if (at<int32_t>(g_pReplayStateData, 0x68CF0) == 1)
        rate = util_CBD0(g_pReplayStateData);
    const float duration = at<float>(at<void*>(entry, 0x1C), 0x0C);
    const float step = duration > 0.0f ? g_sysTimeManager.frameSeconds / duration : 0.0f;
    const float scaled = at<float>(entry, 4) * step;
    const float phase = __builtin_fmaf(scaled, rate, at<float>(entry, 0x14));
    at<float>(entry, 0x14) = phase >= 1.0f ? 0.0f : phase;
}
