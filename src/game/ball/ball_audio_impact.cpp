// Impact cue selection, repeat suppression and per-surface volume/gain.
#include "ball_audio.hpp"
#include "ball_audio_envelope.hpp"
#include "rage/indexed_registry.h"

#include <cstdint>
#include <cstdio>

#pragma clang fp contract(off)

namespace {
struct ImpactEmitter {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Play() = 0;
    virtual void Stop() = 0;
    virtual void Slot5() = 0;
    virtual void Slot6() = 0;
    virtual void Slot7() = 0;
    virtual void Slot8() = 0;
    virtual uint32_t Select(const char* cue) = 0;
    virtual void Slot10() = 0;
    virtual void Slot11() = 0;
    virtual void Slot12() = 0;
    virtual void Slot13() = 0;
    virtual void Slot14() = 0;
    virtual void Slot15() = 0;
    virtual void Slot16() = 0;
    virtual void Slot17() = 0;
    virtual void Slot18() = 0;
    virtual uint32_t IsPlaying() = 0;
};
struct ImpactEmitterFields {
    uint8_t _pad00[0x14];
    uint32_t flags;
    uint8_t _pad18[0x18];
    float volume;
};
// Pointer members have their native width/alignment. In particular, names does
// not overlap repeat on 64-bit hosts; comments identify the Xenon offsets.
struct ImpactAudio {
    uint8_t _pad000[0x2F4];
    float smashThreshold, hardThreshold, mediumThreshold;
    uint8_t _pad300[0x18];
    int32_t nameCount;                      // +0x318
    const char** names;                     // +0x31C
    uint32_t repeat;                        // +0x320
    uint8_t handled;                        // +0x324
    uint8_t _pad325[3];
    uint32_t hitCounter;                    // +0x328
    uint32_t lastStamp, netStamp, personStamp;
};
struct ImpactControls {
    uint8_t _pad00[0x90];
    float soft, medium, hard, smash, net, pong;
    uint8_t _pad0A8[0x12C];
    int32_t nearBudget, farBudget;
};
struct ImpactInput {
    uint8_t _pad00[0x14];
    int32_t networkCount;
    uint8_t _pad18[0x10];
    uint32_t prefixKey;
};
struct ImpactPrefix { uint8_t _pad00[0x28]; const char* prefix; };
struct ImpactTiming {
    uint8_t _pad00[0x28];
    uint32_t stamp;
    uint8_t _pad2C[0x28];
    float tick;
};
struct ImpactContext {
    uint8_t _pad00[0x58];
    uint8_t suppressed;
    uint8_t _pad59[0x5B];
    void* environmentResource;
    uint8_t _padB8[0x188];
    char environment[256];
};
struct ImpactTable { uint8_t _pad00[0x14]; float height; };
struct ImpactBound { uint8_t _pad00[8]; float radius; };
struct ImpactArchetype { uint8_t _pad00[0x0C]; ImpactBound* bound; };
struct ImpactInstance { void* vtable; ImpactArchetype* archetype; };
}

extern "C" uint8_t lbl_825C5EC8[];                   // @ 0x825C5EC8
extern void* g_input_obj_ptr;                          // @ 0x825EAB28
extern void* lbl_8271A310;                             // @ 0x8271A310
extern void* g_pTableDims;                             // @ 0x8271A304
extern void** g_ppBallInst;                            // @ 0x8271A2F4
extern "C" uint32_t g_hudShell_UpdateBlock[24];       // @ 0x825CAEB8
extern "C" const uint8_t* g_pongControlGroupConfig;   // @ 0x8271A398
extern "C" void* g_audCtrlMgrControlPrimary;          // @ 0x82606410
extern "C" void* g_ballAudioListener;                // @ 0x82606424
extern "C" float g_phCapsuleShapeK;                  // @ 0x825C8080
extern "C" float g_kPowerBlend;                      // @ 0x825C2EA0
extern bool BallShot_IsLocalPlay();                   // @ 0x822823E0
extern void nop_8240E6D0(const char* format, ...);      // @ 0x8240E6D0

namespace {
ImpactControls const* ImpactConfig() {
    return reinterpret_cast<const ImpactControls*>(g_pongControlGroupConfig);
}
ImpactTiming* ImpactClock() {
    return reinterpret_cast<ImpactTiming*>(g_hudShell_UpdateBlock);
}
ImpactEmitter* ImpactVoice(void* audio, uint32_t offset) {
    return reinterpret_cast<ImpactEmitter*>(static_cast<uint8_t*>(audio) + offset);
}
float ImpactTableHeight() { return static_cast<ImpactTable*>(g_pTableDims)->height; }
float ImpactRadius() {
    auto* ball = static_cast<ImpactInstance*>(*g_ppBallInst);
    return ball ? ball->archetype->bound->radius : 0.0f;
}
}

// @ 0x8228AD58
int BallAudio_PreImpact(void* audioPtr, void* /*unusedR4*/, int kind, const float* position,
                       int index, float energy) {
    auto* audio = static_cast<ImpactAudio*>(audioPtr);
    char cue[128] = {};
    float gain = 1.0f;
    float volume = 1.0f;
    const bool kick = lbl_825C5EC8[0x30] != 0 && static_cast<uint8_t>(BallShot_IsLocalPlay()) != 0;
    const bool pong = lbl_825C5EC8[8] != 0;
    const bool special = kick || pong;
    auto* input = static_cast<ImpactInput*>(g_input_obj_ptr);
    auto* record = static_cast<ImpactPrefix*>(pg_C2A0_g(lbl_8271A310, input->prefixKey));
    const char* const prefix = record->prefix;
    auto* primary = ImpactVoice(audioPtr, 0x10);
    auto* loop = ImpactVoice(audioPtr, 0x1A0);
    BallAudio_SetEmitterPosition(primary, position);
    BallAudio_SetEmitterPosition(loop, position);
    BallAudio_SetEmitterPosition(ImpactVoice(audioPtr, 0x240), position);
    const int32_t elapsed = static_cast<int32_t>(ImpactClock()->stamp - audio->lastStamp);
    if (kind == 2 || kind == 5) audio->lastStamp = ImpactClock()->stamp;
    const bool above = position[1] >= ImpactTableHeight() - 0.11999999731779099f;
    const bool budget = above
        ? static_cast<int32_t>(audio->hitCounter) > ImpactConfig()->nearBudget
        : static_cast<int32_t>(audio->repeat) >= ImpactConfig()->farBudget;
    if (budget && audio->handled == 0 &&
        static_cast<ImpactContext*>(g_audCtrlMgrControlPrimary)->suppressed == 0) {
        uint32_t chosenLoop = 0;
        if (kind == 2) {
            snprintf(cue, sizeof(cue), "%s:BALL_TABLE_BOUNCE", prefix);
            if (!special) chosenLoop = loop->Select(cue);
        } else if (kind == 5) {
            if (index < audio->nameCount) {
                snprintf(cue, sizeof(cue), "%s:%s_BOUNCE", prefix, audio->names[index]);
                if (!special) chosenLoop = loop->Select(cue);
            } else {
                nop_8240E6D0("[pongBallAudio] Sound index %d out of range!", index);
            }
        }
        if (static_cast<uint8_t>(chosenLoop) != 0) loop->Play();
        audio->handled = 1;
    }
    if (elapsed < 2 && elapsed != static_cast<int32_t>(audio->lastStamp)) {
        ++audio->repeat;
        return 0;
    }
    if (static_cast<uint8_t>(loop->IsPlaying()) != 0 && !above) loop->Stop();
    audio->repeat = 0;
    if (!above) audio->handled = 0;
    uint32_t chosen = 0;
    switch (kind) {
    case 2:
        if (audio->handled != 0) return 0;
        if (pong) {
            snprintf(cue, sizeof(cue), "%s:PONG_BALL_TABLE", prefix);
            chosen = primary->Select(cue);
            volume = ImpactConfig()->pong;
        } else if (kick) {
            snprintf(cue, sizeof(cue), "HUD:KICKBALL_TABLE");
            chosen = primary->Select(cue);
            volume = ImpactConfig()->pong;
        } else if (energy >= audio->smashThreshold * 9.999999747378752e-05f) {
            snprintf(cue, sizeof(cue), "%s:BALL_TABLE_SMASH", prefix);
            chosen = primary->Select(cue);
            volume = ImpactConfig()->smash;
        } else if (energy >= audio->hardThreshold * 9.999999747378752e-05f) {
            snprintf(cue, sizeof(cue), "%s:BALL_TABLE_HARD", prefix);
            chosen = primary->Select(cue);
            volume = ImpactConfig()->hard;
        } else if (energy >= audio->mediumThreshold * 9.999999747378752e-05f) {
            snprintf(cue, sizeof(cue), "%s:BALL_TABLE_MEDIUM", prefix);
            chosen = primary->Select(cue);
            volume = ImpactConfig()->medium;
        } else {
            snprintf(cue, sizeof(cue), "%s:BALL_TABLE_SOFT", prefix);
            chosen = primary->Select(cue);
            volume = ImpactConfig()->soft;
        }
        ++audio->hitCounter;
        break;
    case 3: {
        snprintf(cue, sizeof(cue), pong ? "%s:PONG_BALL_NET" : "%s:BALL_NET", prefix);
        volume = pong ? ImpactConfig()->pong : ImpactConfig()->net;
        chosen = primary->Select(cue);
        const uint32_t now = ImpactClock()->stamp;
        const float age = static_cast<float>(now - audio->netStamp);
        const float cooldown = 2.0f / ImpactClock()->tick;
        if (age < cooldown) chosen = 0;
        else audio->hitCounter = 0;
        audio->netStamp = age < cooldown ? now : ImpactClock()->stamp;
        if (!static_cast<uint8_t>(AudioControl_IsWithinActiveEnvelope(g_ballAudioListener)) && !pong)
            gain = 0.5f;
        break;
    }
    case 4: {
        if (special) {
            if (!pong) {
                snprintf(cue, sizeof(cue), "HUD:KICKBALL_PERSON");
                chosen = primary->Select(cue);
            }
        } else {
            snprintf(cue, sizeof(cue), "%s:BALL_HIT_PERSON", prefix);
            chosen = primary->Select(cue);
        }
        volume = 0.0f;
        const uint32_t now = ImpactClock()->stamp;
        const float cooldown = g_kPowerBlend / ImpactClock()->tick;
        if (static_cast<float>(now - audio->personStamp) < cooldown) chosen = 0;
        audio->personStamp = now;
        audio->hitCounter = 0;
        break;
    }
    case 5: {
        const char* suffix;
        if (energy >= audio->smashThreshold * 9.999999747378752e-05f) {
            suffix = "_HARD";
            volume = ImpactConfig()->hard;
        } else if (energy >= audio->hardThreshold * 9.999999747378752e-05f) {
            suffix = "_MEDIUM";
            volume = ImpactConfig()->medium;
        } else {
            suffix = "_SOFT";
            volume = ImpactConfig()->soft;
        }
        if (index == 15) {
            snprintf(cue, sizeof(cue), pong ? "%s:PONG_BALL_NET" : "%s:BALL_NET", prefix);
            volume = pong ? ImpactConfig()->pong : ImpactConfig()->net;
            gain = 0.5f;
        } else if (!special) {
            if (index == 7 && position[1] <= ImpactTableHeight() + ImpactRadius() &&
                static_cast<ImpactInput*>(g_input_obj_ptr)->networkCount > 0) gain = g_phCapsuleShapeK;
            auto* context = static_cast<ImpactContext*>(g_audCtrlMgrControlPrimary);
            const char* environment = context->environmentResource ? context->environment : nullptr;
            snprintf(cue, sizeof(cue), "%s:%s%s", environment, audio->names[index], suffix);
        } else if (kick) {
            snprintf(cue, sizeof(cue), "HUD:KICKBALL_TABLE");
            gain = 0.5f;
        }
        if (!(pong && index != 15)) chosen = primary->Select(cue);
        audio->hitCounter = 0;
        break;
    }
    default:
        nop_8240E6D0("Unhandled instance type (%d) in pongBallAudio::PreImpact", kind);
        break;
    }
    if (static_cast<uint8_t>(chosen) == 0) return 0;
    BallAudio_SetEmitterGain(primary, gain);
    auto* fields = reinterpret_cast<ImpactEmitterFields*>(primary);
    fields->volume = volume;
    fields->flags |= 8;
    primary->Play();
    return 1;
}
