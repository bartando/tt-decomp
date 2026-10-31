// Swing animation phase/pose helpers recovered from the original PPC.
#include <cstdint>

extern "C" uint8_t g_swingInFlightFlag; // @ 0x8260633C
extern void pg_E6E0(int, uint8_t, int, int); // @ 0x8225E6E0
extern void* game_BAA0(void*); // @ 0x820DBAA0
extern void pcrAnimBlender_ApplyClipWeights(void*, const char*, float, float); // @ 0x820CF420

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
uint8_t swingRecipient(uint32_t slot, uint8_t extra = 0) {
    const uint32_t shift = slot & 63u;
    return static_cast<uint8_t>((shift < 32 ? 1u << shift : 0u) | extra);
}
float markerTime(void* record, unsigned offset) {
    const float duration = at<float>(at<void*>(record, 0x10), 0x0C);
    if (!(duration > 0.0f)) return 0.0f;
    const float frame = static_cast<float>(at<int16_t>(record, offset));
    const float seconds = frame * 0.03333333507180214f;
    return seconds / duration;
}
}

// Notify entry/exit marker crossings and completion before applying the live
// clip weights. The selected clip may be absent, but events still run.
// @ 0x820DADC0 | size: 0x1C0
void game_ADC0(void* swing, void* record) {
    if (g_swingInFlightFlag) return;
    const float current = at<float>(swing, 0x1C);
    if (current >= at<float>(swing, 0x30)) {
        pg_E6E0(0x100B, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, 0);
    } else if (at<float>(record, 0x80) > 0.0f) {
        const float previous = at<float>(swing, 0x18);
        const float entry = markerTime(record, 0x130);
        const float exit = markerTime(record, 0x132);
        if (previous < entry && current >= entry)
            pg_E6E0(0x1009, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, 0);
        if (previous < exit && current >= exit)
            pg_E6E0(0x100A, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, 0);
    }
    if (void* clip = game_BAA0(record)) {
        void* owner = at<void*>(swing, 8);
        const char* name = at<const char*>(clip, 0x20);
        pcrAnimBlender_ApplyClipWeights(at<void*>(owner, 0xC0), name,
            at<float>(swing, 0x18), at<float>(swing, 0x1C));
    }
}

extern "C" void* g_pongMatchTiming; // @ 0x8271A2E8
struct sysTimeManagerImage {
    void** vtable;
    uint32_t field_04;
    float frameSeconds;
    float framesPerSecond;
};
extern "C" sysTimeManagerImage g_sysTimeManager; // @ 0x825CAEB8
extern void pcrSwingBlender_A920_wrh(void*, void*); // @ 0x820DA920
extern void pcrSwingBlender_AAA0_wrh(void*, void*); // @ 0x820DAAA0
extern "C" void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

// Advance normalized swing time. Freeze flags retain a phase just below one
// after announcing the first crossing; empty animation sets finish at one.
// @ 0x820DA6F0 | size: 0x22C
void pcrSwingBlender_UpdatePhase(void* swing, void* record) {
    at<uint8_t>(swing, 0x8D) = 0;
    if (!at<void*>(record, 0x10) && !at<void*>(record, 0x14) && !at<void*>(record, 0x18)) {
        at<float>(swing, 0x1C) = 1.0f;
        return;
    }
    if (at<float>(g_pongMatchTiming, 0x30) < at<float>(swing, 0x14)) {
        at<float>(swing, 0x1C) = 0.0f;
    } else if (at<float>(record, 0x120) >= 0.0f && !(at<uint8_t>(record, 0x138) & 4)) {
        if (at<uint8_t>(swing, 0x8C)) pcrSwingBlender_A920_wrh(swing, record);
        else pcrSwingBlender_AAA0_wrh(swing, record);
    } else {
        const float duration = at<float>(at<void*>(record, 0x10), 0x0C);
        const float frames = __builtin_fmaf(duration, 30.0f, 1.0f) - 1.0f;
        const float difference = 1.0f - frames;
        const float denominator = difference >= 0.0f ? 1.0f : frames;
        const float advance = g_sysTimeManager.frameSeconds / denominator;
        at<float>(swing, 0x1C) = __builtin_fmaf(advance, 30.0f, at<float>(swing, 0x1C));
    }
    // fsel clamps unordered values to zero and retains a negative zero.
    const float phase = at<float>(swing, 0x1C);
    const double nonnegative = phase >= 0.0f ? double(phase) : 0.0;
    const float clamped = nonnegative - 1.0 >= 0.0 ? 1.0f : static_cast<float>(nonnegative);
    at<float>(swing, 0x1C) = clamped;
    if ((at<uint8_t>(record, 0x138) & 12) && clamped == 1.0f) {
        if (clamped > at<float>(swing, 0x18)) {
            void* clip = game_BAA0(record);
            nop_8240E6D0("pcrSwingBlender::UpdatePhase--anim %s is kAnimFrozenAtEnd\n",
                        at<const char*>(clip, 0x20));
            pg_E6E0(0x1016, 0x40, 0, 0);
        }
        at<float>(swing, 0x1C) -= 9.999999747378752e-05f;
    }
}
