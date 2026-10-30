#include <cstddef>
#include <cstdint>

namespace rage {

struct audInstanceSpatialInput {
    uint8_t reserved[28];
    float position[3];
    uint8_t remaining[84];
};

// The backend interface is only known at the slots used by this update.
struct audInstance {
    void* voice;
    uint8_t state;
    uint8_t persistent;
    uint8_t spatial;
    uint8_t reserved7;
    uint32_t controlGroup;
    uint8_t controlEnabled;
    uint8_t reserved13[15];
    float volume;
    uint8_t reserved32[64];
    audInstanceSpatialInput spatialInput;
    uint8_t spatialOutput[32];
    float distance;
};

static_assert(sizeof(audInstanceSpatialInput) == 124);
static_assert(sizeof(void*) != 4 || offsetof(audInstance, volume) == 28);
static_assert(sizeof(void*) != 4 || offsetof(audInstance, spatialInput) == 96);
static_assert(sizeof(void*) != 4 || offsetof(audInstance, distance) == 252);

extern uint8_t g_audListener[]; // @ 0x825EE258
extern const char g_audDistanceParameter[]; // @ 0x8203B4E8
extern void audCalculateSpatial(uint8_t*, uint8_t*, int, uint8_t*); // @ 0x82481920
extern void audInstance_UpdateParameters(audInstance*); // @ 0x821AF860

extern audInstance* g_audInstancePool2000[16]; // @ 0x825EE658
extern audInstance* g_audInstancePool4000[240]; // @ 0x825EE298
extern const char g_audInvalidXactCommand[]; // @ 0x8203B2B0
extern "C" void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0
extern void aud_F098(audInstance*, uint32_t, uint32_t, uint32_t, uint32_t,
                     uint32_t, uint32_t, uint32_t, uint32_t, uint8_t); // @ 0x821AF098
extern uint8_t aud_F508(audInstance*, uint32_t, uint32_t); // @ 0x821AF508
extern void aud_F5F0(audInstance*); // @ 0x821AF5F0
extern void aud_F670(audInstance*); // @ 0x821AF670
extern void aud_F6F0(audInstance*); // @ 0x821AF6F0
extern void aud_FB50(audInstance*, uint32_t); // @ 0x821AFB50
extern void aud_FC28(audInstance*, uint32_t); // @ 0x821AFC28
extern void aud_FD10(audInstance*, float); // @ 0x821AFD10

// Inferred name: the command consumer at 0x821AB4C0 passes its queued XACT
// payload here; the default diagnostic calls these "xactSound" commands.
void audXactSound_ProcessCommand(uint32_t command, const uint32_t* params) { // @ 0x821AEAE0
    uint32_t opcode = command & 0xffff;
    auto getInstance = [&]() {
        return (opcode < 0x4000 ? g_audInstancePool2000 : g_audInstancePool4000)[params[0]];
    };

    switch (opcode) {
    case 0x2003:
    case 0x200b:
    case 0x4007:
    case 0x400c:
        break;
    case 0x2002:
        aud_F508(getInstance(), params[1], params[2]);
        break;
    case 0x2005:
    case 0x4002:
        aud_F098(getInstance(), params[1], params[2], params[3], params[4],
                 params[5], params[6], params[7] != 0, params[8], params[9] != 0);
        break;
    case 0x2007:
    case 0x4003:
        aud_F6F0(getInstance());
        break;
    case 0x2008:
    case 0x4004:
        aud_F5F0(getInstance());
        break;
    case 0x2009:
    case 0x4005:
        aud_F670(getInstance());
        break;
    case 0x200a:
    case 0x4006: {
        audInstance* instance = getInstance();
        // addi wraps before extsw/fcfid converts the signed low word to float.
        instance->volume = static_cast<float>(static_cast<int32_t>(params[1] + 5000u)) * 0.0002f;
        audInstance_UpdateParameters(instance);
        break;
    }
    case 0x200d:
    case 0x400a:
        aud_FD10(getInstance(), static_cast<float>(static_cast<int32_t>(params[1])));
        break;
    case 0x200e:
    case 0x400b: {
        audInstance* instance = getInstance();
        instance->spatialInput.position[0] = static_cast<float>(static_cast<int32_t>(params[1])) * 0.001f;
        instance->spatialInput.position[1] = static_cast<float>(static_cast<int32_t>(params[2])) * 0.001f;
        instance->spatialInput.position[2] = -(static_cast<float>(static_cast<int32_t>(params[3])) * 0.001f);
        break;
    }
    case 0x200f:
    case 0x400e:
        aud_FB50(getInstance(), params[1]);
        break;
    case 0x2010:
    case 0x4010: {
        audInstance* instance = getInstance();
        if (instance->controlGroup != params[1]) {
            instance->controlGroup = params[1];
        }
        instance->controlEnabled = params[2] != 0;
        break;
    }
    case 0x2011:
    case 0x4011:
        aud_FC28(getInstance(), params[1]);
        break;
    default:
        nop_8240E6D0(g_audInvalidXactCommand, params[0], opcode);
        break;
    }
}

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

    audCalculateSpatial(g_audListener, reinterpret_cast<uint8_t*>(&instance->spatialInput),
                        61, instance->spatialOutput);
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
