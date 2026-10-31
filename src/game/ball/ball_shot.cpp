/**
 * ball_shot.cpp — launching the ball off a hit
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * BallShot_Launch turns a shot entry (the per-player table at 0x8261A3D0, hit
 * data at +0x30) into a launch velocity and spin, takes the ball out of the
 * rigid-body simulation and hands the launch to the trajectory predictor,
 * which simulates the flight with ball_flight.hpp's model. The ball then plays
 * that trajectory back. The shot's Gravity reaches the simulation as the ball
 * archetype's gravity factor, set for the duration of the prediction only.
 */

#include "ball_shot_solve.hpp"

#include <stdint.h>

struct pongBallInstance;
struct gmBallNode;

namespace {

using Vec4 = BallFlightVec4;

struct ShotEntryView {             // one 416-byte entry of the table at 0x8261A3D0
    uint8_t _pad000[0x28];
    int32_t slot28;                // +0x028  indexes the input object's kinds below
    uint8_t _pad02C[0x04];
    uint8_t hit[0x20];             // +0x030  pongBallHitData starts here
    Vec4    worldTgtPos;           // +0x050  hit "WorldTgtPos"
    uint8_t _pad060[0x10];
    Vec4    spinAxis;              // +0x070  hit "SpinAxis"
    Vec4    directSpin;            // +0x080  hit +0x50; the spin as is when slot28's kind is 2
    Vec4    vec90;                 // +0x090  hit +0x60; the solver's second argument
    uint8_t _pad0A0[0x10];
    float   postHitSpeed;          // +0x0B0  hit "PostHitSpeed"
    uint8_t _pad0B4[0x10];
    float   gravity;               // +0x0C4  hit "Gravity"
    uint8_t _pad0C8[0x04];
    int32_t swingType;             // +0x0CC  hit "SwingType"
    Vec4    serveHitVel;           // +0x0D0  hit "ServeHitVel"
    Vec4    serveHitAngVel;        // +0x0E0  hit "ServeHitAngVel"
    uint8_t _pad0F0[0x06];
    uint16_t flags;                // +0x0F6  hit +0xC6; 0x1000 while serving
};

struct ArchetypeView {             // rage::phArchetypePhys
    void** vtable;
    // Slot 15 (0x822C95F0) stores +0x24, the gravity factor.
    void SetGravityFactor(float factor) { reinterpret_cast<void (*)(void*, float)>(vtable[15])(this, factor); }
};

struct BallInstView {              // pongBallInstance, a rage::phInst
    void**         vtable;
    ArchetypeView* archetype;      // +0x04
    uint16_t       levelIndex;     // +0x08
};

struct LevelView {                 // rage::phLevelNew
    uint8_t  _pad00[0x1C];
    uint8_t* objectStates;         // +0x1C  low 3 bits 0 = active
};

struct InputObjectView {           // *g_input_obj_ptr
    uint8_t _pad00[0x38];
    int32_t kind[1];               // +0x38  indexed by the shot entry's slot28
};

struct GameStateView {             // *g_game_state_ptr
    uint8_t _pad00[0x04];
    float   f04, f08, f0C;         // +0x04
    uint8_t _pad10[0x1C];
    int32_t count2C;               // +0x2C
    int32_t count30;               // +0x30
};

}  // namespace

extern pongBallInstance** g_ppBallInst;      // @ 0x8271A2F4
extern const BallFlightVec4 g_phGravity;     // @ 0x825CBCE0
extern gmBallNode* g_activeBallNode;         // @ 0x82606570
extern int32_t g_shotSolveState;             // @ 0x82606580  the solver (0x822851D0 and below) reads it
extern float g_ballTrailHitValue;            // @ 0x825C4940  0x82282508's result; fxBallTrail::AddSample reads it
extern void* g_pPhysicsLevel;                // @ 0x826065E4
extern void* g_pPhysicsSim;                  // @ 0x825F5BD0
extern void* g_input_obj_ptr;                // @ 0x825EAB28
extern void* g_game_state_ptr;               // @ 0x8271A2F8

extern void  game_2010(gmBallNode* node, int kind);                                      // @ 0x82282010
extern void  pongPlayer_5010_g(void* sub, void* output, void* parent, int flag);         // @ 0x821D5010
extern float game_2508(const Vec4* spin, const Vec4* vel);                                // @ 0x82282508
extern void  game_4B60(void* scene, uint16_t handle);                                    // @ 0x822C4B60
// r6 is never set by the caller nor read by the callee.
extern void  ballPredict_ProcessHit(void* hit, const Vec4* vel, const Vec4* spin, int unusedR6, int one, uint32_t arg, float time);  // @ 0x82287B50

extern void* pongMatch_GetCharacterForSlot(void* match, uint32_t playerSlot); // @ 0x821C9C00
extern int32_t g_currentInputSlot;                                        // @ 0x82606578
extern void* g_pCameraSharedState;                                         // @ 0x8271A32C
extern "C" const float g_kFloatConst_D108;                                       // @ 0x8202D108
extern "C" const float g_kFloatConst_D10C;                                       // @ 0x8202D10C
extern "C" const float g_kFloatConst_D110;                                       // @ 0x8202D110
extern "C" const float lbl_825C5938;                                       // @ 0x825C5938

namespace {
struct TrailCharacterView {
    uint8_t _pad00[0x28];
    struct Parameters {
        uint8_t _pad00[0x10];
        float topSpin;             // +0x10
        float backSpin;            // +0x14
        uint8_t _pad18[4];
        float sideSpin;            // +0x1C
    }* trail;
};
}

// @ 0x821D61A8
// Eight directions in the spin x/y plane, made relative to ball travel and
// camera side. Index 8 is the neutral direction (also the unordered fallback).
int pongBall_ClassifySpin(const Vec4* spin, const Vec4* velocity) {
    const float direction = velocity->z > g_kFloatConst_D110 ? g_kFloatConst_D108 : lbl_825C5938;
    const float x = spin->x * direction;
    const uint8_t cameraSide = static_cast<const uint8_t*>(g_pCameraSharedState)[5];
    const bool backwards = direction < g_kFloatConst_D110;
    const float y = cameraSide == static_cast<uint8_t>(backwards)
        ? spin->y * lbl_825C5938 : spin->y;

    if (x > g_kFloatConst_D110) {
        if (y < g_kFloatConst_D110) return 1;
        if (y > g_kFloatConst_D110) return 7;
        return 0;
    }
    if (x < g_kFloatConst_D110) {
        if (y < g_kFloatConst_D110) return 3;
        if (y > g_kFloatConst_D110) return 5;
        return 4;
    }
    if (y < g_kFloatConst_D110) return 2;
    if (y > g_kFloatConst_D110) return 6;
    return 8;
}

// @ 0x82282508
float game_2508(const Vec4* spin, const Vec4* velocity) {
    const unsigned direction = static_cast<unsigned>(pongBall_ClassifySpin(spin, velocity));
    if (direction > 7) return g_kFloatConst_D110;

    // The original repeats the lookup on diagonals and loads both parameter
    // pointers afterwards. Keep that order: the resolver can update live data.
    void* const match = g_input_obj_ptr;
    const uint32_t slot = static_cast<uint32_t>(g_currentInputSlot);
    auto* first = static_cast<TrailCharacterView*>(pongMatch_GetCharacterForSlot(match, slot));
    if ((direction & 1) == 0) {
        if (direction == 0) return first->trail->topSpin;
        if (direction == 4) return first->trail->backSpin;
        return first->trail->sideSpin;
    }
    auto* second = static_cast<TrailCharacterView*>(pongMatch_GetCharacterForSlot(match, slot));
    const float axial = (direction == 1 || direction == 7)
        ? first->trail->topSpin : first->trail->backSpin;
    const float combined = second->trail->sideSpin + axial;
    return combined * g_kFloatConst_D10C;
}

// @ 0x822827E8
int BallShot_Launch(void* entryPtr, int unusedR4, int unusedR5, uint32_t predictArg, uint32_t resetRally,
                    float time) {
    (void)unusedR4;
    (void)unusedR5;
    auto* entry = static_cast<ShotEntryView*>(entryPtr);

    int effectKind;
    switch (entry->swingType) {
    case 6: case 8:  effectKind = 1; break;
    case 9: case 11: effectKind = 2; break;
    case 10:         effectKind = 3; break;
    default:         effectKind = 0; break;
    }
    game_2010(g_activeBallNode, effectKind);

    Vec4 spin;
    Vec4 vel;
    int solved = 1;
    if ((entry->flags & 0x1000) == 0) {
        auto* ball = reinterpret_cast<BallInstView*>(*g_ppBallInst);
        ball->archetype->SetGravityFactor(entry->gravity / g_phGravity.y);
        g_shotSolveState = 0;

        auto* input = static_cast<InputObjectView*>(g_input_obj_ptr);
        if (input->kind[entry->slot28] == 2) {
            spin = entry->directSpin;
        } else {
            pongPlayer_5010_g(&entry->spinAxis, &spin, entry->hit, 1);
        }
        solved = BallShot_Solve(entry, &entry->vec90, &entry->worldTgtPos, &spin, &vel, entry->postHitSpeed);
    } else {
        vel = entry->serveHitVel;
        spin = entry->serveHitAngVel;
    }

    g_ballTrailHitValue = game_2508(&spin, &vel);

    auto* ball = reinterpret_cast<BallInstView*>(*g_ppBallInst);
    auto* level = static_cast<LevelView*>(g_pPhysicsLevel);
    if ((level->objectStates[ball->levelIndex] & 7) == 0) {
        game_4B60(g_pPhysicsSim, ball->levelIndex);
    }

    if (static_cast<uint8_t>(resetRally) != 0) {  // a bool: only the low byte counts
        auto* state = static_cast<GameStateView*>(g_game_state_ptr);
        state->f04 = 0.0f;
        state->f08 = 0.0f;
        state->f0C = 0.0f;
        state->count30 = 0;
        state->count2C = 0;
    }

    ballPredict_ProcessHit(entry->hit, &vel, &spin, 0, 1, predictArg, time);
    reinterpret_cast<BallInstView*>(*g_ppBallInst)->archetype->SetGravityFactor(1.0f);
    return solved;
}
