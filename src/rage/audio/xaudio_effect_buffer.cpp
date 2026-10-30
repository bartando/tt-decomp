#include <cstddef>
#include <cstdint>

namespace rage {

struct XAudioEffectBuffer {
    void* interface;
    uint8_t index;
    uint8_t active;
    uint8_t format;
    uint8_t reserved;
};

struct XAudioBufferPool {
    uint8_t reserved[12];
    void* buffers[2];
};

static_assert(sizeof(void*) != 4 || offsetof(XAudioEffectBuffer, active) == 5);
static_assert(sizeof(void*) != 4 || offsetof(XAudioEffectBuffer, format) == 6);
static_assert(sizeof(void*) != 4 || offsetof(XAudioBufferPool, buffers) == 12);

extern XAudioBufferPool* g_xaudioBufferPool; // @ 0x825E788C

// @ 0x8247FE38
// Formerly ph_FE38. Selects input/output buffers for an XAudio effect interface.
int32_t xaudioEffectBuffer_Process(void*, XAudioEffectBuffer* effect, void** current) {
    if (!(effect->active & 1)) return 0;

    void* input = nullptr;
    void* output = nullptr;
    const uint8_t format = effect->format;
    if ((format & 6) == 6) {
        input = *current;
        XAudioBufferPool* pool = g_xaudioBufferPool;
        unsigned index = 0;
        if (input) {
            for (; index < 2; ++index) {
                if (input == pool->buffers[index]) break;
            }
        } else {
            index = 2;
        }
        output = pool->buffers[index < 2 ? (index ^ 1) : 0];
        *current = output;
    } else if (format & 3) {
        input = *current;
    } else if (format & 4) {
        output = *current;
    }
    // For format & 7 == 0 the original passes an uninitialized stack word
    // twice; choose deterministic null arguments for that indeterminate case.
    using Process = int32_t (*)(void*, void*, void*);
    void** vtable = *static_cast<void***>(effect->interface);
    return reinterpret_cast<Process>(vtable[6])(effect->interface, input, output);
}

}
