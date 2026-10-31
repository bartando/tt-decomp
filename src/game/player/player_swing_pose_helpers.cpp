// Swing animation phase/pose helpers recovered from the original PPC.
#include <cstdint>
#include "game/game_message.hpp"

extern "C" uint8_t g_swingInFlightFlag; // @ 0x8260633C
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
float phaseFrameSpan(float duration) {
    const float frames = __builtin_fmaf(duration, 30.0f, 1.0f) - 1.0f;
    const float difference = 1.0f - frames;
    return difference >= 0.0f ? 1.0f : frames;
}
}

// Notify entry/exit marker crossings and completion before applying the live
// clip weights. The selected clip may be absent, but events still run.
// @ 0x820DADC0 | size: 0x1C0
void game_ADC0(void* swing, void* record) {
    if (g_swingInFlightFlag) return;
    const float current = at<float>(swing, 0x1C);
    if (current >= at<float>(swing, 0x30)) {
        PostGameMessage(0x100B, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, nullptr);
    } else if (at<float>(record, 0x80) > 0.0f) {
        const float previous = at<float>(swing, 0x18);
        const float entry = markerTime(record, 0x130);
        const float exit = markerTime(record, 0x132);
        if (previous < entry && current >= entry)
            PostGameMessage(0x1009, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, nullptr);
        if (previous < exit && current >= exit)
            PostGameMessage(0x100A, swingRecipient(at<uint32_t>(swing, 0x88), 0x40), 0, nullptr);
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
        const float denominator = phaseFrameSpan(duration);
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
            PostGameMessage(0x1016, 0x40, 0, nullptr);
        }
        at<float>(swing, 0x1C) -= 9.999999747378752e-05f;
    }
}

// Select the present clip with greatest weight. Equal/unordered comparisons
// retain the earlier clip, including when its weight is NaN.
// @ 0x820DBAA0 | size: 0xA4
void* game_BAA0(void* record) {
    int selected = -1;
    for (int index = 0; index < 3; ++index) {
        if (at<void*>(record, 0x10 + unsigned(index) * 4)
            && (selected < 0 || at<float>(record, 0x1C + unsigned(index) * 4)
                > at<float>(record, 0x1C + unsigned(selected) * 4)))
            selected = index;
    }
    return selected < 0 ? nullptr : at<void*>(record, 0x10 + unsigned(selected) * 4);
}

// Map clock time onto the entry/exit markers, then continue at the clip rate.
// Each ordered clock comparison falls through when its inputs are unordered.
// @ 0x820DA920 | size: 0x17C
void pcrSwingBlender_A920_wrh(void* swing, void* record) {
    const float now = at<float>(g_pongMatchTiming, 0x30);
    const float contactClock = at<float>(swing, 0x10);
    if (now <= contactClock) {
        const float startClock = at<float>(swing, 0x14);
        const float elapsed = now - startClock;
        const float interval = contactClock - startClock;
        const float ratio = elapsed / interval;
        at<float>(swing, 0x1C) = markerTime(record, 0x130) * ratio;
    } else if (now <= at<float>(swing, 0x0C)) {
        const float elapsed = now - contactClock;
        const float interval = at<float>(swing, 0x0C) - contactClock;
        const float ratio = elapsed / interval;
        const float exit = markerTime(record, 0x132);
        const float entry = markerTime(record, 0x130);
        const float difference = exit - entry;
        at<float>(swing, 0x1C) = __builtin_fmaf(difference, ratio, entry);
    } else {
        const float duration = at<float>(at<void*>(record, 0x10), 0x0C);
        const float advance = g_sysTimeManager.frameSeconds / phaseFrameSpan(duration);
        at<float>(swing, 0x1C) = __builtin_fmaf(advance, 30.0f, at<float>(swing, 0x1C));
    }
}

// Reach the exit marker at the planned clock time, then interpolate the
// follow-through rate over the remaining normalized phase interval.
// @ 0x820DAAA0 | size: 0x1A0
void pcrSwingBlender_AAA0_wrh(void* swing, void* record) {
    const float now = at<float>(g_pongMatchTiming, 0x30);
    const float exitClock = at<float>(swing, 0x0C);
    const float startClock = at<float>(swing, 0x14);
    const float interval = exitClock - startClock;
    if (now <= exitClock) {
        const float elapsed = now - startClock;
        const float ratio = elapsed / interval;
        at<float>(swing, 0x1C) = markerTime(record, 0x132) * ratio;
        return;
    }
    const float duration = at<float>(at<void*>(record, 0x10), 0x0C);
    const float frame = static_cast<float>(at<int16_t>(record, 0x132));
    const float seconds = frame * 0.03333333507180214f;
    const float finalRate = 30.0f / phaseFrameSpan(duration);
    const float clockRate = seconds / interval;
    const float initialRate = clockRate * finalRate;
    const float marker = markerTime(record, 0x132);
    const float current = at<float>(swing, 0x1C);
    const float elapsedPhase = current - marker;
    const float remainingPhase = at<float>(swing, 0x28) - marker;
    const float ratio = elapsedPhase / remainingPhase;
    const double nonnegative = ratio >= 0.0f ? double(ratio) : 0.0;
    const float blend = nonnegative - 1.0 >= 0.0 ? 1.0f : static_cast<float>(nonnegative);
    const float difference = finalRate - initialRate;
    const float rate = __builtin_fmaf(difference, blend, initialRate);
    at<float>(swing, 0x1C) = __builtin_fmaf(rate, g_sysTimeManager.frameSeconds, current);
}
