#include <cstdint>

namespace rage {

// The backend interface is only known at the slots used by this update.
struct audInstance {
    void* voice;
    uint8_t state;
    uint8_t persistent;
    uint8_t spatial;
    uint8_t padding[89];
    uint8_t spatialInput[124];
    uint8_t spatialOutput[32];
    float distance;
};

extern uint8_t g_audListener[]; // @ 0x825EE258
extern const char g_audDistanceParameter[]; // @ 0x8203B4E8
extern void audCalculateSpatial(uint8_t*, uint8_t*, int, uint8_t*); // @ 0x82481920
extern void audInstance_UpdateParameters(audInstance*); // @ 0x821AF860

// Poll an active voice, handle its state transitions and update its 3D mix.
void audInstance_Update(audInstance* instance) { // @ 0x821AFD90
    void* voice = instance->voice;
    if (!voice) return;

    auto table = *reinterpret_cast<void***>(voice);
    uint32_t flags;
    reinterpret_cast<void (*)(void*, uint32_t*)>(table[2])(voice, &flags);
    if (instance->state == 14 && (flags & 4)) {
        instance->state = 15;
        return;
    }
    if (flags & 0x20) {
        voice = instance->voice;
        if (voice) {
            table = *reinterpret_cast<void***>(voice);
            reinterpret_cast<void (*)(void*)>(table[3])(voice);
            instance->voice = nullptr;
        }
        instance->state = instance->persistent ? 11 : 19;
        return;
    }
    if (!instance->spatial) return;

    audCalculateSpatial(g_audListener, instance->spatialInput, 61, instance->spatialOutput);
    voice = instance->voice;
    table = *reinterpret_cast<void***>(voice);
    uint32_t parameter = reinterpret_cast<uint32_t (*)(void*, const char*)>(table[8])(
        voice, g_audDistanceParameter);
    voice = instance->voice;
    table = *reinterpret_cast<void***>(voice);
    reinterpret_cast<void (*)(void*, uint32_t, float)>(table[9])(voice, parameter, instance->distance);
    audInstance_UpdateParameters(instance);
}

} // namespace rage
