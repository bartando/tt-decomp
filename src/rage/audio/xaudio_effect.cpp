#include <cstdint>

// The names describe observed behavior; the SDK's original type name is unknown.
struct XAudioEffectState {
    void** vtable;
    uint8_t reserved04[28];
    void* buffer;
    uint8_t reserved24[8];
    void (*callback)(void**);
    void* callbackContext;
    uint8_t reserved34[9];
    uint8_t flags;
    uint8_t reserved3e[2];
    uint16_t remaining;
};

// @ 0x8247FBA0
int32_t xaudioEffect_UpdateBuffer(XAudioEffectState* effect) {
    void* args[2] = {effect->callbackContext, effect->buffer};
    if (effect->callback)
        effect->callback(args);
    if (effect->flags & 4) {
        if (effect->remaining == 0) {
            using Stop = int32_t (*)(XAudioEffectState*, int32_t, int32_t);
            return reinterpret_cast<Stop>(effect->vtable[15])(effect, 1, 1);
        }
        --effect->remaining;
    }
    using Submit = int32_t (*)(XAudioEffectState*, void**);
    return reinterpret_cast<Submit>(effect->vtable[20])(effect, &args[1]);
}
