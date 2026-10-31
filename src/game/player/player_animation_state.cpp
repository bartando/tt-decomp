// Player-state pose assembly and locomotion crossfade, 0x820CC678.
// This is the inner state at pongCreature+0xBC, not the outer player object.
#include <cstdint>
#include <cstring>
#include <cstddef>
#include "pong_player.hpp"

extern "C" bool pongPlayer_D550_g(void*); // @ 0x820CD550
extern "C" bool pongPlayer_D598_g(void*); // @ 0x820CD598
extern "C" bool pongPlayer_D5F0_g(void*); // @ 0x820CD5F0
extern float pongPlayer_D238_g(void*); // @ 0x820DD238
extern float game_C8E0_h(void*); // @ 0x820DC8E0
extern void LocomotionStateAnim_CDB8_g(void*, bool, bool); // @ 0x820DCDB8
extern void pg_C540_g(void*); // @ 0x820DC540
extern void pcrSwingBlender_UpdatePhase(void*, void*); // @ 0x820DA6F0
extern void LocomotionStateAnim_AC40_g(void*, void*); // @ 0x820DAC40
extern void game_ADC0(void*, void*); // @ 0x820DADC0
extern void LocomotionStateAnim_1E68_g(void*, void*); // @ 0x820C1E68
// r4 is unused, r5 receives the position; r6 is not an argument.
extern uint32_t LocomotionStateAnim_B800_g(void*, void*, float*); // @ 0x820CB800
extern float ph_ClampAndSin(float); // @ 0x820CB6A0
extern float util_B6F0(float); // @ 0x820CB6F0
extern float cmSmoothRemap_B768(float); // @ 0x820CB768

using DofOperation = void (*)(void*, void*, float, uint32_t, uint32_t);
using DofFilter = uint32_t (*)(void*, uint32_t, uint32_t, void*, float*);
extern void LocomotionStateAnim_B800_g_B800_1(
    void*, const void*, void*, DofFilter, void*, float, void*, DofOperation); // @ 0x8224B800
extern void playerPose_CopyDof(void*, void*, float, uint32_t, uint32_t); // @ 0x82378450
extern void playerPose_BlendDof(void*, void*, float, uint32_t, uint32_t); // @ 0x8224BB98
extern uint32_t playerPose_FilterDof(void*, uint32_t, uint32_t, void*, float*); // @ 0x82248250

extern "C" void** g_pInputArrayTable; // @ 0x825EAB28
extern "C" const float g_identityMatrixRef[16]; // @ 0x825CB800
extern "C" uint8_t g_playerSlotPoseData[160]; // @ 0x82619990
extern "C" uint8_t g_playerPoseChannelBlend; // @ 0x82606334
extern "C" int32_t g_playerPoseEaseMode; // @ 0x82606330

namespace {

// Only fields used here are named; offsets are relative to the inner state.
struct PlayerPoseState {
    uint8_t pad00[8];
    uint32_t slotIndex;              // +08
    uint8_t pad0C[7];
    uint8_t suppressBlend;           // +13
    uint8_t pad14[12];
    uint8_t pose[16];                // +20 crAnimFrame
    uint8_t secondaryPose[16];       // +30 crAnimFrame
    uint8_t pad40[36];
    uint8_t* defaultSlot;            // +64
    uint8_t pad68[16];
    uint8_t* activeSlot;             // +78
    uint8_t* swing;                  // +7C
    uint8_t* recovery;               // +80
    uint8_t* auxiliary;              // +84
    uint8_t* phase;                  // +88
    uint8_t* special;                // +8C
    uint8_t* secondary;              // +90
    uint8_t* locomotion;             // +94
    uint8_t* blendFilter;            // +98
    uint8_t* additivePose;           // +9C
    float blendIn;                  // +A0
    float blendOut;                 // +A4
    float blendWeight;              // +A8
};

#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(offsetof(PlayerPoseState, pose) == 0x20, "pose offset");
static_assert(offsetof(PlayerPoseState, activeSlot) == 0x78, "slot offset");
static_assert(offsetof(PlayerPoseState, blendWeight) == 0xA8, "weight offset");
#endif

template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

template<class Fn> Fn virtualAt(void* object, unsigned slot) {
    return reinterpret_cast<Fn>((*static_cast<void***>(object))[slot]);
}

void exportPose(void* animation, void* frame) {
    virtualAt<void (*)(void*)>(animation, 4)(animation);
    virtualAt<void (*)(void*, void*)>(animation, 8)(animation, frame);
}

void copyPose(void* dst, const void* src) {
    LocomotionStateAnim_B800_g_B800_1(dst, src, nullptr, nullptr, nullptr,
                                    0.0f, nullptr, playerPose_CopyDof);
}

// Xenon's fsel chooses zero for NaN as well as for negative values.
float clampPoseWeight(float value) {
    const float nonnegative = value >= 0.0f ? value : 0.0f;
    return nonnegative >= 1.0f ? 1.0f : nonnegative;
}

float markerTime(uint8_t* record, unsigned marker) {
    const float duration = at<float>(at<void*>(record, 16), 12);
    if (!(duration > 0.0f)) return 0.0f;
    const float frames = static_cast<float>(at<int16_t>(record, marker));
    return (frames * 0.03333333507180214f) / duration;
}

void startLocomotion(PlayerPoseState* state, void* sourceFrame) {
    alignas(16) float transform[16];
    std::memcpy(transform, g_pInputArrayTable[state->slotIndex + 17], sizeof transform);
    // Preserve the source's w lanes and translation while replacing its basis.
    transform[0] = 1.0f; transform[1] = 0.0f; transform[2] = 0.0f;
    transform[4] = 0.0f; transform[5] = 1.0f; transform[6] = 0.0f;
    transform[8] = 0.0f; transform[9] = 0.0f; transform[10] = 1.0f;
    alignas(16) float position[4];
    LocomotionStateAnim_B800_g(sourceFrame, nullptr, position);
    for (unsigned i = 0; i < 4; ++i) transform[12 + i] += position[i];
    auto start = virtualAt<void (*)(void*, uint32_t, const float*, uint32_t)>(
        state->locomotion, 3);
    start(state->locomotion, 1, transform, 0);
    state->locomotion[340] = 1;
}

} // namespace

// Priority-select the current pose, advance its timing, then crossfade the
// locomotion frame and (during a swing's exit) the secondary animation.
// The by-address entry is retained for the existing UpdateLocomotionState alias.
// @ 0x820CC678 | size: 0xBB0 (2992 bytes)
extern "C" void pongPlayer_C678_g(pongPlayer* player) {
    auto* state = reinterpret_cast<PlayerPoseState*>(player);
    float end = state->blendOut;
    float start = state->blendIn;
    float progress = 0.0f;
    float limit = 1.0f;
    bool blend = false;
    bool secondaryOverlay = false;
    state->blendWeight = 0.0f;

    if (player->IsCreatureStateReady()) {
        if (state->locomotion) state->locomotion[340] = 0;
        exportPose(state->special, state->pose);
    } else if (pongPlayer_D598_g(state)) {
        auto* recovery = state->recovery;
        if (state->locomotion && at<float>(recovery, 172) >= state->blendIn
            && at<float>(recovery, 168) < state->blendIn)
            state->locomotion[340] = 0;
        auto* loco = state->locomotion;
        LocomotionStateAnim_CDB8_g(recovery,
            at<int32_t>(loco, 28) == 0 && at<int32_t>(loco, 36) == 3,
            at<int32_t>(loco, 32) == 1);
        float time = pongPlayer_D238_g(recovery);
        if (at<float>(recovery, 172) >= time) {
            time = pongPlayer_D238_g(recovery);
            if (at<float>(recovery, 168) < time && state->locomotion)
                startLocomotion(state, recovery + 128);
        }
        if (recovery[44]) {
            copyPose(state->pose, state->locomotion + 8);
        } else {
            copyPose(state->pose, recovery + 128);
            blend = true;
            progress = at<float>(recovery, 172);
            end = pongPlayer_D238_g(recovery);
        }
    } else if (pongPlayer_D5F0_g(state)) {
        auto* phase = state->phase;
        float current = at<float>(phase, 412) <= 0.0f ? at<float>(phase, 96) : 0.0f;
        float previous = at<float>(phase, 412) <= 0.0f ? at<float>(phase, 100) : 0.0f;
        if (state->locomotion && current >= state->blendIn && previous < state->blendIn)
            state->locomotion[340] = 0;
        pg_C540_g(phase);
        if (state->locomotion) {
            current = at<float>(phase, 412) <= 0.0f ? at<float>(phase, 96) : 0.0f;
            float time = game_C8E0_h(phase);
            if (current >= time) {
                previous = at<float>(phase, 412) <= 0.0f ? at<float>(phase, 100) : 0.0f;
                time = game_C8E0_h(phase);
                if (previous < time) startLocomotion(state, phase + 384);
            }
        }
        copyPose(state->pose, phase + 384);
        blend = state->suppressBlend == 0;
        progress = at<float>(phase, 412) <= 0.0f ? at<float>(phase, 96) : 0.0f;
        end = game_C8E0_h(phase);
    } else if (pongPlayer_D550_g(state)) {
        auto* swing = state->swing;
        if (state->locomotion && at<float>(swing, 28) >= state->blendIn
            && at<float>(swing, 24) < state->blendIn)
            state->locomotion[340] = 0;
        if (g_swingInFlightFlag) state->activeSlot = state->defaultSlot;
        auto* record = state->activeSlot + 32;
        at<float>(swing, 24) = at<float>(swing, 28);
        pcrSwingBlender_UpdatePhase(swing, record);
        LocomotionStateAnim_AC40_g(swing, record);
        game_ADC0(swing, record);
        if (state->auxiliary && !g_swingInFlightFlag) {
            at<float>(state->auxiliary, 12) = markerTime(record, 306);
            at<float>(state->auxiliary, 16) = at<float>(swing, 28);
        }
        const float time = markerTime(record, 308);
        if (at<float>(swing, 28) >= time && at<float>(swing, 24) < time
            && state->locomotion) {
            alignas(16) float transform[16];
            std::memcpy(transform, g_identityMatrixRef, sizeof transform);
            std::memcpy(transform + 12, g_playerSlotPoseData + 16 + state->slotIndex * 80, 16);
            auto activate = virtualAt<void (*)(void*, uint32_t, const float*, uint32_t)>(
                state->locomotion, 3);
            activate(state->locomotion, 1, transform, record[314]);
            state->locomotion[340] = 1;
        }
        copyPose(state->pose, swing + 96);
        blend = state->suppressBlend == 0 && !g_swingInFlightFlag;
        progress = at<float>(swing, 28);
        if (at<float>(record, 128) > 0.0f) {
            end = markerTime(record, 308);
            limit = at<float>(swing, 48);
        }
        secondaryOverlay = player->IsCreatureState2Active() && progress > end;
        if (at<float>(swing, 28) >= at<float>(swing, 48)) state->activeSlot = nullptr;
    } else if (player->IsCreatureState2Active()) {
        if (state->locomotion) state->locomotion[340] = 0;
        exportPose(state->secondary, state->pose);
        if (!pongPlayer_D550_g(state)) {
            end = 1.0f;
            progress = at<float>(state->secondary, 96);
            void* clip = at<uint16_t>(state->secondary, 88) == 1
                ? at<void*>(state->secondary, 84) : nullptr;
            const float duration = at<float>(clip, 12);
            start = duration > 0.0f ? 0.2666666805744171f / duration : 0.0f;
            blend = progress < start;
        }
    } else {
        if (state->locomotion) state->locomotion[340] = 1;
        copyPose(state->pose, state->locomotion + 8);
        state->blendWeight = 1.0f;
    }

    if (blend) {
        float weight;
        DofFilter filter = nullptr;
        void* filterData = nullptr;
        if (end < 1.0f && progress > end) {
            const float ratio = (progress - end) / (limit - end);
            const float curve = !(ratio >= 0.4f) ? 0.0f
                : clampPoseWeight((ratio - 0.4f) * 1.6666666269302368f);
            float* weights = at<float*>(state->blendFilter, 12);
            weights[2] = ratio;
            weights[0] = curve;
            weights[1] = curve;
            state->blendWeight = ratio;
            filter = playerPose_FilterDof;
            filterData = state->blendFilter;
            weight = 1.0f;
        } else if (start > 0.0f && progress < start) {
            const float ratio = progress / start;
            if (g_playerPoseChannelBlend) {
                const float curve = 1.0f - clampPoseWeight(ratio * 2.0f);
                float* weights = at<float*>(state->blendFilter, 12);
                weights[2] = curve;
                weights[0] = curve;
                weights[1] = 1.0f - ratio;
                state->blendWeight = ratio;
                filter = playerPose_FilterDof;
                filterData = state->blendFilter;
                weight = 1.0f;
            } else {
                weight = 1.0f - ratio;
                switch (g_playerPoseEaseMode) {
                case 1: weight = util_B6F0(weight); break;
                case 2: weight = ph_ClampAndSin(weight); break;
                case 3: weight = cmSmoothRemap_B768(weight); break;
                }
                state->blendWeight = weight;
                weight = clampPoseWeight(weight);
            }
        } else {
            goto overlays;
        }
        LocomotionStateAnim_B800_g_B800_1(state->pose, state->locomotion + 8,
            nullptr, filter, filterData, weight, nullptr, playerPose_BlendDof);
    }
overlays:
    if (secondaryOverlay && player->IsCreatureState2Active()) {
        exportPose(state->secondary, state->secondaryPose);
        LocomotionStateAnim_B800_g_B800_1(state->pose, state->secondaryPose,
            nullptr, nullptr, nullptr, clampPoseWeight(state->blendWeight), nullptr, playerPose_BlendDof);
    }
    if (state->auxiliary) LocomotionStateAnim_1E68_g(state->auxiliary, state->pose);
    if (state->additivePose) copyPose(state->pose, state->additivePose);
}
