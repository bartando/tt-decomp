#include "platform/audio.hpp"
#include <cstddef>
#include <cstdint>

namespace rage {

// The buffer interface passed to Process is at +8 in its owning object.
using AudMixerBufferDesc = AudioFrame;

struct AudMixerRoute {
    uint8_t source;
    uint8_t destination;
    uint16_t reserved;
    float currentGain;
    float targetGain;
};

struct AudChannelMixer {
    uint8_t reserved0[16];
    uint8_t routeCount;              // +16: zero selects the identity channel map
    uint8_t reserved17[3];
    AudMixerRoute* routes;           // +20
    uint8_t routeCapacity;           // +24
    uint8_t outputChannels;          // +25
    uint8_t overwrite;               // +26: exactly 1 also updates the output descriptor
};

using AudMixerLock = XAudioLock;

static_assert(sizeof(AudMixerRoute) == 12);
static_assert(sizeof(void*) != 4 || offsetof(AudMixerBufferDesc, samples) == 8);
static_assert(sizeof(void*) != 4 || offsetof(AudChannelMixer, routes) == 20);
static_assert(sizeof(void*) != 4 || offsetof(AudChannelMixer, overwrite) == 26);
static_assert(sizeof(void*) != 4 || offsetof(AudMixerLock, savedIrql) == 12);

extern AudMixerLock g_audMixerLock; // @ 0x825E7870
extern "C" uint32_t KeRaiseIrqlToDpcLevel(); // @ 0x8258653C
extern "C" void KeAcquireSpinLockAtRaisedIrql(void* lock); // @ 0x8258634C
extern "C" void KeReleaseSpinLockFromRaisedIrql(void* lock); // @ 0x8258631C
extern "C" void KfLowerIrql(uint32_t irql); // @ 0x8258654C
extern void* util_6898(void* destination, int value, uint32_t bytes); // @ 0x82566898
extern void* util_8680(void* destination, const void* source, uint32_t bytes); // @ 0x82568680

// VMX arithmetic flushes subnormal operands and results to signed zero.
static inline __attribute__((always_inline)) float mixerFlush(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
    }
    __builtin_memcpy(&value, &bits, sizeof(value));
    return value;
}

static inline __attribute__((always_inline)) float mixerAdd(float a, float b) {
    return mixerFlush(mixerFlush(a) + mixerFlush(b));
}

static inline __attribute__((always_inline)) float mixerMultiply(float a, float b) {
    return mixerFlush(mixerFlush(a) * mixerFlush(b));
}

// @ 0x82465550
// Previously ph_vt58FC_13_5550: a planar float audio mixer, not a physics method.
// The original uses 64 four-lane VMX groups, retaining four running gains rather
// than recomputing gain from the sample index. Keep the product rounded before
// each VMX add (compile without FP contraction).
int32_t audChannelMixer_Process(AudChannelMixer* mixer, void* sourceBuffer, void* destinationBuffer) {
    AudMixerBufferDesc source;
    AudMixerBufferDesc destination;
    void* sourceOwner = sourceBuffer ? static_cast<char*>(sourceBuffer) - offsetof(AudioFrameBuffer, kind) : nullptr;
    void* destinationOwner = destinationBuffer ? static_cast<char*>(destinationBuffer) - offsetof(AudioFrameBuffer, kind) : nullptr;
    int32_t status = PcmFrame_Get(sourceOwner, &source);
    if (status < 0) {
        return status;
    }
    status = PcmFrame_Get(destinationOwner, &destination);
    if (status < 0) {
        return status;
    }
    if (mixer->overwrite == 1) {
        destination.channels = mixer->outputChannels;
        status = PcmFrame_Resize(destinationOwner, &destination, 1);
    }
    if (status < 0) {
        return status;
    }

    uint32_t oldIrql = KeRaiseIrqlToDpcLevel();
    uintptr_t thread;
#if defined(__powerpc__) || defined(__ppc__)
    // Xenon's r13 identifies the current processor/TLS block for this lock.
    __asm__ volatile("mr %0, 13" : "=r"(thread));
#else
    thread = hostAudioThreadIdentity();
#endif
    AudMixerLock& lock = g_audMixerLock;
    if (lock.depth == 0 || lock.owner != thread) {
        KeAcquireSpinLockAtRaisedIrql(&lock);
        lock.owner = thread;
        lock.savedIrql = static_cast<uint8_t>(oldIrql);
    }
    ++lock.depth;

    if (mixer->routeCount != 0) {
        for (uint32_t routeIndex = 0; routeIndex < mixer->routeCount; ++routeIndex) {
            AudMixerRoute& route = mixer->routes[routeIndex];
            if (route.destination >= destination.channels) {
                continue;
            }
            float* output = destination.samples + 256 * route.destination;
            if (route.source < source.channels) {
                const float* input = source.samples + 256 * route.source;
                float target = route.targetGain;
                // These three scalar instructions retain subnormals.
                float difference = target - route.currentGain;
                float step = difference * (1.0f / 256.0f);
                float advance = step * 4.0f;
                float gains[4];
                for (uint32_t lane = 0; lane < 4; ++lane) {
                    gains[lane] = mixerAdd(mixerMultiply(step, static_cast<float>(lane)), route.currentGain);
                }
                for (uint32_t group = 0; group < 64; ++group) {
                    float result[4];
                    for (uint32_t lane = 0; lane < 4; ++lane) {
                        uint32_t sample = group * 4 + lane;
                        result[lane] = mixerMultiply(input[sample], gains[lane]);
                        if (mixer->overwrite == 0) {
                            result[lane] = mixerAdd(result[lane], output[sample]);
                        }
                        gains[lane] = mixerAdd(gains[lane], advance);
                    }
                    // Load all lanes before storing: in-place and overlapping routes
                    // must see the same 16-byte group as the original vector load.
                    for (uint32_t lane = 0; lane < 4; ++lane) {
                        output[group * 4 + lane] = result[lane];
                    }
                }
                route.currentGain = target;
            } else if (mixer->overwrite != 0) {
                util_6898(output, 0, 1024);
            }
        }
    } else if (sourceBuffer != destinationBuffer) {
        for (uint32_t channel = 0; channel < destination.channels; ++channel) {
            float* output = destination.samples + 256 * channel;
            if (channel < source.channels) {
                const float* input = source.samples + 256 * channel;
                if (mixer->overwrite == 0) {
                    for (uint32_t group = 0; group < 64; ++group) {
                        float result[4];
                        for (uint32_t lane = 0; lane < 4; ++lane) {
                            uint32_t sample = group * 4 + lane;
                            result[lane] = mixerAdd(input[sample], output[sample]);
                        }
                        for (uint32_t lane = 0; lane < 4; ++lane) {
                            output[group * 4 + lane] = result[lane];
                        }
                    }
                } else {
                    util_8680(output, input, 1024);
                }
            } else if (mixer->overwrite != 0) {
                util_6898(output, 0, 1024);
            } else {
                break;
            }
        }
    }

    if (lock.depth != 0 && lock.owner == thread) {
        if (--lock.depth == 0) {
            uint32_t savedIrql = lock.savedIrql;
            lock.savedIrql = 0;
            lock.owner = 0;
            KeReleaseSpinLockFromRaisedIrql(&lock);
            KfLowerIrql(savedIrql);
        }
    }
    return 0;
}

} // namespace rage
