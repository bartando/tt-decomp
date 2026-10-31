#pragma once
#include <cstddef>
#include <cstdint>

struct AudioFrame {
    uint8_t format, channels;
    uint16_t reserved;
    uint32_t sampleRate;
    float* samples;
};
struct AudioFormat {
    uint8_t format, channels;
    uint16_t reserved;
    uint32_t sampleRate;
};
// SDK frame owner @82465DE0: capacity format at +0xC, current frame at +0x14.
// Storage is supplied by the owning audio allocator; Resize never reallocates it.
struct AudioFrameBuffer {
    void* vtable;
    uint32_t references;
    uint8_t kind, reserved[3];
    AudioFormat capacity;
    AudioFrame frame;
    void* allocator;
};
struct XAudioLock {
    uint32_t spinLock, depth;
    uintptr_t owner;
    uint8_t savedIrql, reserved[3];
};
struct XmaLoopRegion {
    uint32_t startBits, endBits;
    uint8_t startSubframe, endSubframe, count;
};
inline uintptr_t hostAudioThreadIdentity() {
    static thread_local uint8_t identity;
    return reinterpret_cast<uintptr_t>(&identity);
}
extern XAudioLock g_xaudioSourceLock; // @ 0x825E7870
namespace rage { extern XAudioLock g_audMixerLock; } // Same image object.
constexpr int32_t HostMediaNotSupported = static_cast<int32_t>(0x80004001u);
constexpr int32_t HostMediaInvalidArgument = static_cast<int32_t>(0x80070057u);
int32_t PcmFrame_Get(void* owner, AudioFrame* frame); // @ 0x82465D80
int32_t PcmFrame_Resize(void* owner, const AudioFrame* frame, uint32_t flags); // @ 0x82465EF0
int32_t XAudioFrame_Get(void* frameInterface, AudioFrame* frame); // @ 0x82465DA8
int32_t XAudioFrame_Resize(void* frameInterface, const AudioFrame* frame, uint32_t flags); // @ 0x82466018
int32_t XmaDecoder_IsEnabled(void* decoder); // @ 0x8246AEF8
int32_t XmaDecoder_Lock(void* decoder); // @ 0x8246B708
void XmaDecoder_Wait(void* decoder); // @ 0x8246B7A0
uint32_t XmaDecoder_Available(void* decoder, uint32_t stream); // @ 0x8246B118
uint32_t XmaDecoder_Peek(void* decoder, uint32_t stream, const void** input); // @ 0x8246B360
void XmaDecoder_Consume(void* decoder, uint32_t stream, uint32_t frames, const void** input); // @ 0x8246B190
uint32_t XmaDecoder_SamplesPlayed(void* decoder, uint32_t stream); // @ 0x8246B550
int32_t XmaDecoder_Unlock(void* decoder); // @ 0x8246B9E0
int32_t XmaDecoder_HasInputSpace(void* decoder, uint32_t stream); // @ 0x8246B050
int32_t XmaDecoder_IsBufferPending(void* decoder, uint32_t stream, const void* data); // @ 0x8246AFF0
uint32_t XmaDecoder_GetStreamStatus(void* decoder, uint32_t stream); // @ 0x8246B488
int32_t XmaDecoder_IsInputEmpty(void* decoder, uint32_t stream); // @ 0x8246B0B8
int32_t XmaDecoder_SubmitData(void* decoder, uint32_t stream, const void* data, uint32_t bytes); // @ 0x8246AF18
int32_t XmaDecoder_SetReadPosition(void* decoder, uint32_t stream, uint32_t bits, uint32_t subframe); // @ 0x8246B5E0
int32_t XmaDecoder_SetLoopRegion(void* decoder, uint32_t stream, const XmaLoopRegion* region); // @ 0x8246B4D8
double XAudio_UInt64ToDouble(unsigned long long value); // @ 0x825693C0
