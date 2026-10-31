#include "platform/audio.hpp"
#include <cstring>

static_assert(sizeof(void*) != 4 || offsetof(AudioFrameBuffer, frame) == 0x14, "SDK frame layout");
static_assert(sizeof(void*) != 4 || offsetof(AudioFrameBuffer, kind) == 8, "SDK interface layout");

// @ 0x82465D80
int32_t PcmFrame_Get(void* owner, AudioFrame* frame) {
    if (!owner || !frame) return HostMediaInvalidArgument;
    *frame = static_cast<AudioFrameBuffer*>(owner)->frame;
    return 0;
}
// @ 0x82465DA8
int32_t XAudioFrame_Get(void* frameInterface, AudioFrame* frame) {
    void* owner = frameInterface ? static_cast<uint8_t*>(frameInterface) - offsetof(AudioFrameBuffer, kind) : nullptr;
    return PcmFrame_Get(owner, frame);
}
// @ 0x82465EF0
int32_t PcmFrame_Resize(void* owner, const AudioFrame* requested, uint32_t flags) {
    if (!owner) return HostMediaInvalidArgument;
    auto* buffer = static_cast<AudioFrameBuffer*>(owner);
    const AudioFormat request = requested ? AudioFormat{requested->format, requested->channels, requested->reserved, requested->sampleRate}
                                         : buffer->capacity;
    auto frames = [](uint32_t rate) -> uint32_t {
        return rate && rate <= 48000 ? uint16_t(256u / (48000u / rate)) : 0;
    };
    uint32_t desiredFrames = frames(request.sampleRate);
    uint32_t capacityFrames = frames(buffer->capacity.sampleRate);
    uint32_t oldFrames = frames(buffer->frame.sampleRate);
    if (!desiredFrames || !capacityFrames || !oldFrames) return HostMediaInvalidArgument;
    uint32_t desired = desiredFrames * request.channels;
    uint32_t capacity = capacityFrames * buffer->capacity.channels;
    uint32_t previous = oldFrames * buffer->frame.channels;
    if (desired > capacity) return static_cast<int32_t>(0x8007000Eu);
    if (!(flags & 1) && previous > desired) return static_cast<int32_t>(0x8000FFFFu);
    if (flags & 2) {
        if (flags & 1) previous = 0;
        if (desired > previous && !buffer->frame.samples) return HostMediaInvalidArgument;
        if (desired > previous) std::memset(buffer->frame.samples + previous, 0, (desired - previous) * sizeof(float));
    }
    buffer->frame.channels = request.channels;
    return 0;
}
// @ 0x82466018
int32_t XAudioFrame_Resize(void* frameInterface, const AudioFrame* frame, uint32_t flags) {
    void* owner = frameInterface ? static_cast<uint8_t*>(frameInterface) - offsetof(AudioFrameBuffer, kind) : nullptr;
    return PcmFrame_Resize(owner, frame, flags);
}

// The retail conversion truncates discarded significand bits, rather than
// rounding as an ordinary C++ unsigned-integer conversion would.
// @ 0x825693C0 | size: 0x28
double XAudio_UInt64ToDouble(unsigned long long value) {
    if (value == 0) return 0.0;
    const unsigned leading = __builtin_clzll(value);
    const uint64_t fraction = ((value << leading) >> 11) & 0x000fffffffffffffULL;
    const uint64_t bits = (uint64_t(1086 - leading) << 52) | fraction;
    double result;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}
