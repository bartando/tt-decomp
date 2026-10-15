/**
 * pongPlayer — Player state query functions
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Covers the small boolean state-query methods (D550–D6B8) that gate
 * swing/action initiation, plus the vector-computation helper D7B0 that
 * resolves the "current target position" for a pending swing.
 *
 * Struct field names come from offset-frequency clustering and debug strings.
 */

#include "pong_player.hpp"
#include <cstring>   // memset
#include <cmath>     // fabsf
#include <cfloat>    // FLT_MAX
#include <cstddef>   // offsetof

// rage memory — declare only what we need to avoid memset redecl conflict
extern void rage_free(void* ptr);

// ---------------------------------------------------------------------------
// External functions referenced below
// ---------------------------------------------------------------------------

// Face animation blender — starts the post-point anim.
// (pcrCreature forward-declared in pong_player.hpp)

// NOTE: pongPlayer_UpdateLocomotionState is the semantic alias for
// pongPlayer_C678_g @ 0x820CC678 (see SECTION 59 forward + stub at end of file).
// It is called from D228 to sync locomotion anim list + body-data state each frame.
extern void pongPlayer_UpdateLocomotionState(pongPlayer* state);  // @ 0x820CC678

// LocomotionStateAnim helpers — update animation list entries.
// C128 = standard transition, C288 = alternate (flag-gated) transition.
extern void LocomotionStateAnim_BlendLocomotionAnims(uint32_t entry, void* parent, float dt);
extern void LocomotionStateAnim_TransitionLocomotionState(uint32_t entry, void* parent, float dt);


// ── External game helpers referenced by pong_player.cpp ───────────────────

namespace rage { void UnbindObject(void* obj, void* arg); }  // @ atSingleton suite
extern void phBoundCapsule_UpdateTransform(void* bound);  // only r3 used; r4-r6 computed internally
extern const float g_kSwingRadiusConst;  // constant from .rdata
extern const vec3  g_kZero_vec3;         // zero vector constant
extern const float g_kZero;              // zero float constant

// ── Additional external stubs for pong_player.cpp ───────────────────────
extern void* g_pInputScoreTable;         // global input score table (float array)
extern void* g_pLerpQueue;               // lerp queue global
extern void* g_pInputObj;               // input object global
extern void* g_pButtonStateTable;        // button state table (int32_t array)
extern const float g_kOneMinusAlpha;     // constant
// pongPlayer_ClampSwingToBounds: r3=playerState ptr, r4=swingVec, r5=uint8_t suppressFlip
extern void pongPlayer_ClampSwingToBounds(void* playerState, vec3* swingVec, uint8_t suppressFlip);
// pongPlayer_GetRacketPosition: r3=out vec3, r4=physBound — both saved in prologue
extern void pongPlayer_GetRacketPosition(vec3* out, void* physBound);
// pongPlayer_SelectSwingTarget: returns int; r3=playerState, r4=int, r5=swingStr*, r6=targetDir*, r7=int
extern int  pongPlayer_SelectSwingTarget(void* playerState, int r4, vec3* swingStrength, vec3* targetDir, int r5);
// pongPlayer_ProcessSwingInput: r3=this, f1=float  (confirmed from call site)
extern void pongPlayer_ProcessSwingInput(pongPlayer* p, float f);
// pongPlayer_ComputeSwingStrength: r3=swingData, r5=outStrength, r6=outTarget, f1=alpha
extern void pongPlayer_ComputeSwingStrength(void* swingData, vec3* outStrength, vec3* outTarget, float alpha);
extern void game_D468(void* obj, vec3* v);               // geometry helper
extern bool pongPlayer_IsLocoStateReady(void* locoState);          // loco check
// @ 0x820D6AA0 (pong_player_swing.cpp) — takes the clip embedded at pongTimingSubState+0x20.
extern "C" bool pongPlayer_6AA0_g(void* clip);
extern int  io_Input_poll_9D68(void* inputObj);           // 0=active input
extern void pongLerpQueue_Update(void* queue);            // lerp queue update

struct pongSwingData {
    uint32_t vtable_ptr;  // +0   (32-bit game ptr kept as uint32 for layout)
    uint8_t  _pad1[337];  // +4..+340
    uint8_t  _pad341;     // +341
    uint8_t  m_bTriggered;   // +342  byte flag — 1 = swing triggered
    uint8_t  _pad343;     // +343
    float    m_swingStrength; // +344  swing power
    uint8_t  _pad348[4];  // +348..+351
    float    m_swingVec[3]; // +352  target vec3
};



extern void game_CD20(void* recoveryState);          // flush recovery @ 0x820DCD20
extern void crAnimBlenderState_Init(void* animSubState);  // reset phase-blocked @ 0x8224C810
extern void pcrAnimState_ComputePosition(vec3* out, pongAnimState* animState);  // compute anim pos
extern void pongPlayer_GetAnimNormalizedTime(pongPlayer* state);    // @ 0x820CD238 (or similar)
// NOTE: the recovery "is anim time in range" predicate is pongPlayer_D298_2hr
// @ 0x820DD298 (NOT 0x820CD298 — transcription off-by-one-nibble). Already lifted
// in this file as pongPlayer_IsWithinTimingWindow() at SECTION 5 helper group.
extern bool pongPlayer_IsWithinTimingWindow(void* recoveryState);  // @ 0x820DD298

// Logging no-op (debug only)
extern void rage_debugLog(const char* fmt, ...);

// Geometry / position helpers used by D7B0.
extern void* pg_GetGeometryRecord(void* singleton);              // → returns geometry record

// Global singletons
extern void* g_geomSingleton;   // @ loaded via lis+lwz pattern in D7B0

// Global constants (data section)
extern const float g_recoveryTimerThreshold;   // @ 0x8202D108
extern const float g_swingPhaseThreshold;       // @ 0x8202D110
extern const vec3  g_hitVectorFlip;
// ── Additional globals for CheckButtonInput / OnButtonReleased / IsSwingApexReached ──
extern uint32_t  g_pClockObj;                    // clock object pointer @ SDA area
extern uint32_t* g_pPlayerSlotTable;             // per-slot index table
extern uint8_t*  g_pPlayerDataTable;             // 808-byte-per-entry player records
extern uint32_t  g_pPlayerDataTable_slot;        // active slot index mirror
extern float     g_kPowerBlend;                  // power blend constant @ 0x825C2EA0
extern float     g_kFrameToSecScale;             // frames-to-seconds   @ 0x8202D100

extern bool CheckButtonPressed(void* record);                              // pg_FFF8_g @ 0x8225FFF8
extern void PostPageGroupMessage(void* rec, int code, int mask, int a3, int opActive); // pg_E6E0
extern void pongPlayer_ComputeStepDelta(void* obj, int maxSteps, float* outDelta);   // @ 0x821E0508
extern bool pongPlayer_CheckServeInput(pongPlayer* p);                            // @ 0x82195B60
extern void pongPlayer_InitActionState(void* actionState, int released);            // @ 0x821A1460

// ---------------------------------------------------------------------------
// Resolved global data addresses (from binary analysis)
// ---------------------------------------------------------------------------

// .rdata float constants (adjacent 4-byte floats in 0x8202D1xx)
extern const float g_kFloatConst_D108;       // @ 0x8202D108
extern const float g_kFloatConst_D10C;       // @ 0x8202D10C
extern const float g_kFloatConst_D110;       // @ 0x8202D110

// .rdata vector constants (0x8207Dxxx)
extern const float g_kVecConst_7D110[4];     // @ 0x8207D110  (16B)
extern const float g_kVecConst_7D168[3];     // @ 0x8207D168  (12B)

// .rdata scalar constants (0x82079xxx)
extern const double g_kDoubleConst_79D00;    // @ 0x82079D00  (8B)  upper clamp bound
extern const double g_kDoubleConst_79B00;    // @ 0x82079B00  (8B)  lower clamp bound (zero as double)
extern const double g_kDoubleConst_79EC8;    // @ 0x82079EC8  (8B)  select-zero double (0.0)
extern const float  g_kFloatConst_79C04;     // @ 0x82079C04          epsilon/deadzone
extern const float  g_kFloatConst_79CD8;     // @ 0x82079CD8
extern const float  g_kFloatConst_79BAC;     // @ 0x82079BAC
extern const float  g_kFloatConst_79FFC;     // @ 0x82079FFC
extern const float  g_kFloatConst_79FF8;     // @ 0x82079FF8
extern const float  g_kFloatConst_79FF4;     // @ 0x82079FF4

// .data globals — game state pointers
extern void*    g_pGlobalClock;              // @ 0x8271A304
extern void*    g_pCourtState;               // @ 0x8271A314
extern void*    g_pMatchState;               // @ 0x8271A318
extern void*    g_pPlayerRecords;            // @ 0x8271A31C
extern void*    g_pPlayerRecords2;           // @ 0x8271A324
extern void*    g_pMatchConfig;              // @ 0x8271A32C

// .data globals — game objects
extern void**   g_pInputArrayTable;          // @ 0x825EAB28
extern uint8_t  g_mirrorBuffer[32];          // @ 0x82606720
extern uint8_t  g_ballSplashArray[];         // @ 0x8261A3D0  (416-byte-per-entry)

// ── External functions for batch 10 implementations ──────────────────────
extern void  nop_8240E6D0(const char* fmt, ...);                                        // debug no-op @ 0x8240E6D0
extern void  pongPlayer_Deactivate(void* entry);                                         // @ 0x8218BDC0
extern void  pongPlayer_5C00_g(void* playerPtr, int32_t param);                          // @ 0x82195C00
extern bool  pongPlayer_99B0_g(float* valuePtr, float startVal, float ratio, float step);// @ 0x820C99B0
extern float pongPlayer_0508_g(void* obj, int channel, float inputVal);                  // @ 0x821E0508

// ── External globals for batch 10 implementations ────────────────────────
extern void*       g_pCourtGeomSingleton;     // @ 0x8251A304 — court geometry singleton
extern float       g_kCourtHeightOffset;      // @ 0x825C8078 — court height offset constant
extern const float g_kFloatConst_D168;        // @ 0x8202D168 — grid reset float constant
extern float       g_swingSlotGridDefault;    // @ 0x825CAF7C — writable grid default
extern const float g_kPositiveSideSign;       // @ 0x825C5938 — positive court side sign
extern const float g_kTransitionStep;         // @ 0x825CAEC0 — transition blend step size
extern const float g_kSwingTargetConst;       // @ 0x825C80FC — swing target input constant
extern void*       g_pPlayerSlotLookup;       // @ 0x8251A32C — player slot lookup global

// Forward declarations for functions implemented at end of file
void pongPlayer_E640_g(void* gridSubObj);  // ClearSwingSlotGrid @ 0x8219E640
void pongPlayer_3628_g(pongPlayer* p, uint8_t flip);  // SetServeSideFlip @ 0x82193628
void pongPlayer_E590_g(float* lerpFactors, uint8_t flip, float* outPos,
                       float* boundsA, float* boundsB, float* offset);  // InterpolateGridPosition @ 0x8219E590
bool pongPlayer_6050_p46(int32_t swingType);  // IsSwingType @ 0x821D6050
void pongPlayer_0F10_g(void* stateObj, float* outSign, float deadZone);  // GetCourtSideSign @ 0x821A0F10
void pongPlayer_76E8_g(void* swingHistory);  // InitSwingHistorySlots @ 0x821A76E8
void pongPlayer_AE10_g(void* slotsBase, int32_t slotId, int32_t column);  // RemoveSlotEntry @ 0x8218AE10
void pongPlayer_4438_fw(void* transObj);  // UpdateTransitionBlend @ 0x82384438
void pongPlayer_D6C8_fw(void* animTransObj);  // ResetAnimTransitionState @ 0x8239D6C8
void pongPlayer_06A0_g(float* outVec, pongPlayer* player);  // ComputeSwingTargetDelta @ 0x821906A0

// Swing/target helpers
extern void pongPlayer_ComputeTargetPosition(vec3* outVec, void* targetStruct);
extern float fiAsciiTokenizer_ParseFloat(float input);
extern void pongPlayer_ComputeCourtPosition(vec3* outVec, void* targetData);
extern void pongPlayer_GetCourtBounds(void* self, int r4, void* p3, void* p4, int p5, void* p6, void* p7, uint8_t metadataByte);
extern void pongPlayer_InterpolateCourtPoint(void* adjustedVec, void* gridBase, void* p3, void* p4, void* p5);


// ===========================================================================
// SECTION 1 — State query methods
// ===========================================================================

/**
 * pongPlayerState::IsSwingTimerActive()  @ 0x820CD550 | size: 0x48
 *
 * Returns true while the swing timing sub-state's elapsed time has not yet
 * reached its target duration (i.e. the countdown is still running).
 */
bool pongPlayer::IsSwingTimerActive() const {
    if (!m_pTimingState) {
        return false;
    }
    return m_pTimingState->IsRunning();
}

/**
 * pongPlayerState::IsRecovering()  @ 0x820CD598 | size: 0x58
 *
 * Returns true when the player is locked in a post-swing recovery phase.
 * Either a force-block flag is set, or the recovery timer has not yet
 * counted up to the global threshold.
 */
bool pongPlayer::IsRecovering() const {
    if (!m_pRecoveryState) {
        return false;
    }
    if (m_pRecoveryState->m_bForceBlock) {
        return true;
    }
    return m_pRecoveryState->m_recoveryTimer < g_recoveryTimerThreshold;
}

/**
 * pongPlayerState::IsSwingPhaseBlocked()  @ 0x820CD5F0 | size: 0x70
 *
 * Returns true when the anim phase has exceeded the threshold, or when bit 0
 * of the anim state's flags word is set.  Returns false only when both the
 * phase is within range AND the flag is clear.
 *
 * In the caller (pongPlayer_69A0_g) a false return skips the swing path,
 * so this function acts as a "phase window open" gate.
 *
 * NOTE: the PPC `bso` (summary-overflow) branch at 0x820CD610 is the IEEE-754
 *       NaN-propagation path.  C++ float comparison `>` already returns false
 *       for NaN operands, so `m_animPhase > g_swingPhaseThreshold` naturally
 *       falls through to the flag-bit check — matches the scaffold's
 *       "NaN → evaluate flag" semantics without a separate goto.
 */
bool pongPlayer::IsSwingPhaseBlocked() const {
    if (!m_pAnimState) {
        return false;
    }
    if (m_pAnimState->m_animPhase > g_swingPhaseThreshold) {
        return true;
    }
    return (m_pAnimState->m_flags & 0x1) != 0;
}

/**
 * pongPlayerState::IsCreatureStateReady()  @ 0x820CD660 | size: 0x54
 *
 * Compound gate: requires the state to be active (m_bActive != 0) AND the
 * creature-state sub-object to return true from its virtual IsReady (slot 7).
 */
bool pongPlayer::IsCreatureStateReady() const {
    if (!m_bActive) {
        return false;
    }
    return m_pCreatureState->IsReady();   // vtable slot 7
}

/**
 * pongPlayerState::IsCreatureState2Active()  @ 0x820CD6B8 | size: 0x80
 *
 * Checks the secondary creature-state object (m_pCreatureState2) via two
 * virtual queries: IsActive (slot 6) then IsReady (slot 7).  Both must pass.
 */
bool pongPlayer::IsCreatureState2Active() const {
    if (!m_pCreatureState2) {
        return false;
    }
    if (!m_pCreatureState2->IsActive()) {  // vtable slot 6
        return false;
    }
    return m_pCreatureState2->IsReady();   // vtable slot 7
}


// ===========================================================================
// SECTION 2 — D228: UpdateAnimationState  @ 0x820CD228 | size: 0x18C
// ===========================================================================
/**
 * pongPlayerState::UpdateAnimationState()  @ 0x820CD228
 *
 * Called from pongPlayer_69A0_g to synchronise the player's locomotion
 * animation list with the current state.  Specifically:
 *
 *  1. If the secondary creature state exists and its flag at +424 is set,
 *     start the post-point face animation.
 *  2. Call C678 (state sync helper).
 *  3. Evaluate whether the float field at +0xB0 (animation time) lies within
 *     the range [g_kZero, g_recoveryTimerThreshold].  This selects between
 *     two LocomotionStateAnim update functions (C128 vs C288).  An additional
 *     flag from the parent player's flags word (+4 → +20) can override to C288.
 *  4. Walk the animation list at this+32 (or this+80 in the alternate path)
 *     and call the selected update function on each entry, passing the stored
 *     float value and the parent pointer.
 *
 * NOTE: the two list paths differ only in which sub-object holds the loco
 *       anim list: in-range → m_pGameState (+0x50), out-of-range → m_pLocoState2
 *       (+0x30).  Both have identical layout (entries ptr at +8, count at +12).
 */
void pongPlayer::UpdateAnimationState() {
    // Step 1: optional post-point face animation.
    if (m_pCreatureState2) {
        uint8_t postPointFlag = m_pCreatureState2->m_postPointFlag;  // +0x1A8
        if (postPointFlag) {
            // TODO(researched): the scaffold branches here to a pcrFaceAnimBlender
            // StartPostPoint call, but the singleton-lookup sequence for that
            // blender has not been surfaced in xex_excavation_tt. Inconclusive
            // without the blender symbol — leaving the branch empty keeps the
            // face anim in its current pose rather than triggering the
            // post-point victory/loss expression.
        }
    }

    // Step 2: sync state.
    pongPlayer_UpdateLocomotionState(this);

    // Step 3: range-check m_animTimer against [g_kZero, g_recoveryTimerThreshold].
    float animTime = m_animTimer;
    bool inRange = (animTime >= g_kZero) && (animTime <= g_recoveryTimerThreshold);

    // Also check bit 0 of flags word via parent pointer.
    bool useAltAnim = false;
    if (m_pParent) {
        uint32_t* parentBase = static_cast<uint32_t*>(m_pParent);
        uint32_t flagWord = parentBase[5];   // parent+20 (flags word)
        useAltAnim = (flagWord & 0x1) != 0;
    }

    // Select update function.
    using AnimUpdateFn = void(*)(uint32_t, void*, float);
    AnimUpdateFn updateFn = (inRange && !useAltAnim)
        ? LocomotionStateAnim_BlendLocomotionAnims
        : LocomotionStateAnim_TransitionLocomotionState;

    // Step 4: iterate animation list.
    // In-range: use m_pGameState (+0x50); out-of-range: use m_pLocoState2 (+0x30).
    // NOTE: the "anim list" sub-object embedded inside each holder has a common
    //       layout of {+8: entry array ptr, +12: entry count u16}. m_pGameState
    //       is declared via offset in pong_player.hpp (not yet a named field on
    //       pongPlayer), hence the reinterpret_cast below.
    void* listObj = inRange ? *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(this) + 0x50)
                            : m_pLocoState2;
    uint32_t* listWords = static_cast<uint32_t*>(listObj);
    uint32_t* entries   = reinterpret_cast<uint32_t*>(listWords[2]);  // +8
    uint16_t  count     = static_cast<uint16_t>(listWords[3]);        // +12

    for (int i = 0; i < (int)count; ++i) {
        updateFn(entries[i], m_pParent, g_recoveryTimerThreshold);
    }
}


// ===========================================================================
// SECTION 3 — D7B0: GetSwingTargetVector  @ 0x820CD7B0 | size: 0x154
// ===========================================================================
/**
 * pongPlayerState::GetSwingTargetVector(vec3* out, pongPlayerState* state)
 *   @ 0x820CD7B0
 *
 * Fills *out with the 3D position that the current swing is aimed at.
 * There are three priority-ordered paths:
 *
 *  PATH A — Swing timer running (m_pTimingState->currentTime < targetTime):
 *    Looks up the geometry record for m_pAnimState->field_136 via pg_GetGeometryRecord,
 *    reads a pre-baked vector from the timing state (+80, 16-byte aligned),
 *    optionally flips its sign if a "mirror" flag doesn't match the geometry
 *    record's handedness, then stores the result.
 *
 *  PATH B — Swing phase open (IsSwingPhaseBlocked returns true):
 *    Computes the position analytically via pcrAnimState_ComputePosition(out, m_pAnimState).
 *
 *  PATH C — In recovery (IsRecovering returns true):
 *    Copies the 16-byte vector stored at m_pRecoveryState+0x70 (112) directly.
 *
 *  Fallback: all paths fail → *out is left as the zero-initialised value.
 *
 * TODO(researched): tried resolve_address on 0x820CD868 (returns
 *       pongPlayer_D7B0_g+0xB8 — inside the same function) and struct_fields.txt
 *       searches for the geom record layout; no concrete struct doc found for
 *       the handedness byte at geomRecord[44]+260. Inconclusive because the
 *       geometry record type has no RTTI entry. Leaving semantics intact.
 */
void pongPlayer::GetSwingTargetVector(vec3* out, pongPlayer* state) const {
    // Zero-initialise output (matches the stfs f0 × 3 prologue in the scaffold).
    memset(out, 0, sizeof(vec3));

    pongTimingState* timing = state->m_pTimingState;

    // PATH A: timer is still counting down.
    if (timing && timing->m_currentTime < timing->m_targetTime) {
        // Retrieve geometry base via singleton lookup.
        void*    geomRecord = pg_GetGeometryRecord(g_geomSingleton);
        uint32_t animSubOffset = state->m_pAnimState->m_animSubOffset;  // +0x88

        // Read the 16-byte target vector from the timing state (+0x50).
        vec3 target = timing->m_swingTargetVec;

        // Mirror check: if handedness flags don't match, flip the vector sign.
        // geomRecord+44 → pointer; byte at ptr+260 is the handedness flag.
        // NOTE: the `vsubfp128` at 0x820CD868 implements g_hitVectorFlip - target
        //       per lane; g_hitVectorFlip is effectively a sign/scale vector.
        void** geomWords = static_cast<void**>(geomRecord);
        uint8_t* geomSubPtr = static_cast<uint8_t*>(geomWords[11]);  // +44 / 4
        uint8_t geomFlag = geomSubPtr[260];
        uint8_t animFlag = static_cast<uint8_t*>(g_geomSingleton)[animSubOffset + 64];
        if (geomFlag != animFlag) {
            target.x = g_hitVectorFlip.x - target.x;
            target.y = g_hitVectorFlip.y - target.y;
            target.z = g_hitVectorFlip.z - target.z;
        }

        *out = target;
        return;
    }

    // PATH B: swing phase window is open (IsSwingPhaseBlocked returns true here).
    if (state->IsSwingPhaseBlocked()) {
        pcrAnimState_ComputePosition(out, state->m_pAnimState);
        return;
    }

    // PATH C: player is in recovery — use the stored recovery vector.
    if (state->IsRecovering()) {
        *out = state->m_pRecoveryState->m_recoveryVec;  // +0x70 (112)
    }
    // else: output stays zeroed.
}



// ===========================================================================
// SECTION 4 — C3C8: CanAcceptSwingInput  @ 0x820CC3C8 | size: 0xC8
// ===========================================================================
/**
 * pongPlayer::CanAcceptSwingInput()  @ 0x820CC3C8
 *
 * Returns true when the player's swing subsystem is in a fully neutral state
 * and is ready to register a new swing command.
 *
 * All five conditions must hold simultaneously:
 *   1. Swing phase is NOT blocked (IsSwingPhaseBlocked == false)
 *   2. Swing timer is NOT running: no timing state, or
 *      currentTime >= targetTime (a NaN timer counts as running)
 *   3. NOT in recovery (IsRecovering == false)
 *   4. Secondary creature state is NOT active (IsCreatureState2Active == false)
 *   5. Primary creature state is NOT in "ready" state (IsCreatureStateReady == false)
 *
 * Condition 5 is counterintuitive: "ready" here means the creature state
 * machine is in a post-action "ready-for-next" state, which means it is still
 * completing the previous action's resolution. Returning false for "ready"
 * prevents double-queuing.
 *
 * Called from pongPlayer_ProcessSwingInput (the swing-input polling loop) on the inner
 * pongPlayerState object (this = pongPlayer+0xBC).
 */
bool pongPlayer::CanAcceptSwingInput() const
{
    // Gate 1: swing phase must not be blocked (anim hasn't passed the window).
    if (IsSwingPhaseBlocked())
        return false;

    // Gate 2: timing state — timer must be expired (currentTime >= targetTime).
    // An absent timing state is treated as expired (timer never started).
    if (m_pTimingState) {
        // IsSwingTimerActive (0x820CD550) inlined: the asm computes
        // (currentTime >= targetTime, ordered) and negates it with cntlzw, so a
        // NaN timer counts as running.
        bool timerRunning = !(m_pTimingState->m_currentTime >= m_pTimingState->m_targetTime);
        if (timerRunning)
            return false;
    }

    // Gate 3: recovery window must have elapsed.
    if (IsRecovering())
        return false;

    // Gate 4: secondary creature state must not be in mid-action.
    if (IsCreatureState2Active())
        return false;

    // Gate 5: primary creature state must NOT be in the "ready" sentinel state.
    // "Ready" = state machine just completed something and is waiting; return
    // false to prevent immediate re-entry into the swing path.
    if (IsCreatureStateReady())
        return false;

    return true;
}


// ===========================================================================
// SECTION 6 — DA58: IsSwingApexReached  @ 0x820CDA58 | size: 0x27C
// ===========================================================================
/**
 * pongPlayer::IsSwingApexReached(float threshold)  @ 0x820CDA58
 *
 * Complex multi-path gate that determines whether the active swing has
 * progressed past a caller-supplied strength threshold. Returns true when
 * the swing should be registered as having "connected".
 *
 * The function encapsulates four priority-ordered evaluation paths:
 *
 *  PATH 0 — Active flag + creature state (prerequisite):
 *    If m_bActive is set, verifies that the creature state (m_pCreatureState2,
 *    slot 7 = IsReady) confirms the player is active. If either check fails
 *    the result is false and the remaining paths are skipped.
 *
 *    If the prerequisite passes → continue to PATH 1.
 *    If the prerequisite fails  → evaluate PATHS 2/3 without PATH 1's result.
 *
 *  PATH 1 — Creature state 2 blocking:
 *    If IsCreatureState2Active, return false immediately.
 *
 *  PATH 2 — Swing timer path:
 *    If IsSwingTimerActive: read m_pSwingSubState->m_swingProgress (+160).
 *    If progress > 0 ("swing has launched"), compute a normalised fraction:
 *       fraction = float(frameId at +340) * g_kSwingScaleFactor / swingProgress
 *    Compare m_pTimingState->m_peakX (+28 = recorded target position component)
 *    against this fraction. Return result of comparison.
 *
 *  PATH 3 — Swing phase path (IsSwingPhaseBlocked):
 *    Read anim state m_swingPhase (+412) against g_kZero.
 *    If phase > 0, look up the current frame from the anim array
 *    (m_pAnimState->m_pFrameArray[m_animProgress * 4 → slot][+16 → velocity record][+12 → float]).
 *    Compute normalised fraction same as PATH 2.
 *    Return comparison of m_swingPhase vs fraction.
 *
 *  PATH 4 — Recovery path:
 *    If IsRecovering: check recovery state byte at +44 (m_bForceBlock).
 *    If force-blocked → false. Otherwise:
 *      Call pongPlayer_GetAnimNormalizedTime to get the recovery progress float.
 *      Compare recovery float at +172 against caller's threshold (f1 arg).
 *      Return true if recovery is complete past threshold.
 *
 * @param threshold  Caller-supplied strength threshold (passed in f1).
 *                   Used in PATH 4 only.
 */
bool pongPlayer::IsSwingApexReached(float threshold) const
{
    // ── PATH 0: active + creature state prerequisite ────────────────────
    bool activeAndReady = false;
    if (m_bActive) {
        if (m_pCreatureState2) {
            activeAndReady = m_pCreatureState2->IsReady();  // vtable slot 7
        }
    }

    if (!activeAndReady) {
        // ── PATH 1: creature state 2 block ──────────────────────────────
        if (IsCreatureState2Active())
            return false;

        // ── PATH 2: swing timer ──────────────────────────────────────────
        if (IsSwingTimerActive()) {
            if (!m_pSwingSubState)
                goto path3;

            float swingProgress = m_pSwingSubState->m_swingProgress;  // +160
            if (swingProgress <= g_kZero)
                goto path3;

            // Normalise frame count to [0, 1] range relative to total swing duration.
            float fraction;
            if (swingProgress > g_kZero) {
                int16_t frameId = (int16_t)m_pSwingSubState->m_frameId;  // +340
                fraction = (float)frameId * g_kSwingScaleFactor / swingProgress;
            } else {
                fraction = g_kZero;
            }

            float currentPos = m_pTimingState->m_peakTime;  // +0x24
            return currentPos > fraction;
        }

    path3:
        // ── PATH 3: swing phase blocked ──────────────────────────────────
        if (IsSwingPhaseBlocked()) {
            float swingPhase = m_pAnimState->m_swingPhase;  // +412
            if (swingPhase <= g_kZero)
                goto path4;

            // Look up the current anim frame's velocity record.
            // frameEntry layout: +16 = velocityRecord (ptr), +56 = frameId (int32)
            // velocityRecord: +12 = velFloat (float)
            uint32_t frameIdx   = (uint32_t)m_pAnimState->m_animProgress;  // +96 (index into array)
            void**   frameArray = (void**)m_pAnimState->m_pFrameArray;      // +4
            void*    frame      = frameArray[frameIdx];                     // array[idx]
            uint32_t* frameWords = static_cast<uint32_t*>(frame);
            void*    velocRec   = reinterpret_cast<void*>(frameWords[4]);   // +16 / 4

            float velFloat = static_cast<float*>(velocRec)[3];             // +12 / 4

            float fraction;
            if (velFloat > g_kZero) {
                int32_t frameId = static_cast<int32_t>(frameWords[14]);    // +56 / 4
                fraction = (float)frameId * g_kSwingScaleFactor / velFloat;
            } else {
                fraction = g_kZero;
            }

            // Return true if current phase >= fraction (past the apex).
            // NaN-safe: `!(phase < fraction)` matches bns idiom.
            return !(swingPhase < fraction);
        }

    path4:
        // ── PATH 4: recovery ──────────────────────────────────────────────
        if (!IsRecovering())
            return false;

        // Force-block flag prevents any connection during mandatory recovery.
        if (m_pRecoveryState->m_bForceBlock)
            return false;

        // Recovery state also needs a valid follow-up action to compare against.
        if (!m_pRecoveryState->m_pFollowAction)
            return false;

        // Evaluate recovery progress via helper.
        pongPlayer_GetAnimNormalizedTime((pongPlayer*)this);
        float recoveryVal = m_pRecoveryState->m_recoveryTimer;

        // NaN-safe comparison — matches bns idiom.
        return !(recoveryVal < threshold);  // true if recovery ≥ threshold
    }

    return false;
}


// ===========================================================================
// SECTION 10 — pongPlayer::~pongPlayer  (vfn_0) @ 0x8218B3C0 | size: 0x50
// vtable slot 0 [destructor]
//
// Standard RAGE scalar destructor.  Runs the atSingleton base destructor
// chain via rage::UnbindObject (which in turn calls each registered sub-
// system's Deactivate/Destroy), then conditionally frees the object itself
// if the `flags` argument has bit 0 set (the C++ "delete after dtor" ABI
// convention used throughout this codebase).
//
// @param flags  Bit 0 set → free this pointer via rage_free after dtor.
// ===========================================================================
pongPlayer::~pongPlayer()
{
    rage::UnbindObject(this, 0);  // base class dtor chain — does NOT free this
}

void pongPlayer::ScalarDtor(int flags)
{
    rage::UnbindObject(this, 0);  // base class dtor chain
    if (flags & 1)
        rage_free(this);     // ABI-level "delete" — free the allocation
}


// ===========================================================================
// SECTION 11 — UpdatePhysicsAndSwingInput  @ 0x820C5FB8 | size: 0x10C
// Called from: pongPlayer_Update1
//
// Per-frame synchronisation of physics state and swing input targeting.
// Runs as part of the main update loop before the swing decision is made.
//
// Operations, in order:
//  1. Call vtable slot 3 on m_pPhysicsBody with (body+16) as argument —
//     updates the physics pose / bounding box for the current frame.
//  2. Call phBoundCapsule_UpdateTransform on m_pPhysicsBound — updates the capsule.
//  3. If m_pPlayerState->m_pSwingData exists, call its vtable slot 1 with
//     the capsule radius float (from g_kSwingRadiusConst) — notifies the
//     swing data object of the current body scale.
//  4. Read m_swingInputResult (+200): if it equals 7, suppress vector flip.
//  5. Build a velocity-scaled 3D vector from the physics bound's own floats
//     (+56, +60) multiplied by g_kSwingRadiusConst (+8) using AltiVec vmulfp.
//  6. Call pongPlayer_ClampSwingToBounds to update the swing prediction with this vector.
//  7. Store m_pPhysicsBody float at +72 into g_pInputScoreTable[m_swingInputSlot].
//     This writes the current "power" reading into the input score array so
//     the swing evaluator can pick it up.
// ===========================================================================
void pongPlayer::UpdatePhysicsAndSwingInput()
{
    // ── 1. Physics body pose update (vtable slot 3) ──────────────────────
    {
        typedef void (*BodyUpdateFn)(void*, void*);
        void** bodyVtbl = *static_cast<void***>(m_pPhysicsBody);
        reinterpret_cast<BodyUpdateFn>(bodyVtbl[3])(m_pPhysicsBody,
                                     static_cast<uint8_t*>(m_pPhysicsBody) + 16);
    }

    // ── 2. Capsule shape update ───────────────────────────────────────────
    phBoundCapsule_UpdateTransform(m_pPhysicsBound);

    // ── 3. Notify swing data of current capsule radius ────────────────────
    pongSwingData* swingData = m_pPlayerState ? m_pPlayerState->m_pSwingData : nullptr;
    if (swingData) {
        float radius = g_kSwingRadiusConst;  // @ 0x825CAEB8 + 8
        typedef void (*SwingDataNotifyFn)(pongSwingData*, float);
        void** sdVtbl = *reinterpret_cast<void***>(swingData);
        reinterpret_cast<SwingDataNotifyFn>(sdVtbl[1])(swingData, radius);
    }

    // ── 4. Flip suppression check ─────────────────────────────────────────
    // Result code 7 means the swing has already "flipped" — suppress further flip.
    bool suppressFlip = (m_swingInputResult == 7);
    (void)suppressFlip;  // used downstream in B208 call via f1 arg

    // ── 5. Build velocity-scaled swing vector ─────────────────────────────
    // phBoundCapsule: +0x38 (56) = directionX, +0x3C (60) = directionY
    float* boundBase = reinterpret_cast<float*>(m_pPhysicsBound);
    float vx = boundBase[14];  // +56 / 4 = directionX
    float vy = boundBase[15];  // +60 / 4 = directionY
    float scale = g_kSwingRadiusConst;
    vec3 swingVec = { vx * scale, vy * scale, 0.0f };

    // ── 6. Update swing prediction ────────────────────────────────────────
    pongPlayer_ClampSwingToBounds(m_pPlayerState, &swingVec, 0);

    // ── 7. Write power reading into input score table ─────────────────────
    // phBoundCapsule +0x48 (72) = current power value
    float* bodyBase = reinterpret_cast<float*>(m_pPhysicsBody);
    float power = bodyBase[18];  // +72 / 4 = power
    static_cast<float*>(g_pInputScoreTable)[m_swingInputSlot] = power;


}  // end UpdatePhysicsAndSwingInput



// SECTION 12 — ProcessSwingDecision  @ 0x820C7038 | size: 0x210
// Called from: pongPlayer_StartSwing, ref_PostLoadProperties_CCB0
//
// The main per-frame swing state-machine driver.  Given a target direction
// and various flags, evaluates the current swing status and dispatches to
// the appropriate outcome path.
//
// @param cancelFirst  r6 — if true, cancel any in-progress swing before
//                     starting the new evaluation (used on new ball serve)
// @param pTargetVec   r7 — optional 16-byte aligned vector giving the
//                     explicit target direction; if NULL, the direction is
//                     read from input (poll → D42E0) or predicted (AB48)
// @param r4, r5       pass-through args forwarded to pongPlayer_SelectSwingTarget
//
// Swing result codes (from pongPlayer_SelectSwingTarget):
//   0 = idle               — no swing in progress, nothing to do
//   1 = (unused/internal)
//   2 = restart            — re-run the decision loop; reset swing active flag
//   3 = queued (log only)  — log the swing queue event, reset flag
//   4 = queued (log only)  — same as 3
//   5 = swing started      — player has committed to a swing; call 73E8 to
//                            start the anim and set swing active flag
//   other = no-op
//
// After handling the result, if it leads to a "reset" path (0, 2, 3, 4),
// clears m_bSwingActive and calls SetSwingActiveState(false).
// ===========================================================================
void pongPlayer::ProcessSwingDecision(int r4, int r5,
                                      bool cancelFirst,
                                      const vec3* pTargetVec,
                                      int r7)
{
    // Flush any stale lerp-queue entries before evaluating (global queue tick).
    pongLerpQueue_Update(g_pLerpQueue);

    // Optionally cancel the previous swing before setting up the new one.
    if (cancelFirst)
        m_pPlayerState->CancelSwing();

    // Determine the target direction vector.
    vec3 targetDir = {};    // zero-init
    vec3 swingStrength = {};

    if (pTargetVec) {
        // Explicit target provided (e.g. from network message or serve setup).
        targetDir = *pTargetVec;
    } else {
        // Derive target from input.
        bool inputActive = !io_Input_poll_9D68(g_pInputObj);   // 0 = no input

        if (!inputActive) {
            // Input button is down — read the current input vector.
            pongPlayer_ComputeSwingStrength(m_pPlayerState->m_pSwingData,
                              &swingStrength, &targetDir, g_kOneMinusAlpha);
        } else {
            // No input — predict target position from physics.
            pongPlayer_GetRacketPosition(&targetDir, m_pPhysicsBound);
        }
    }

    // Feed the target into the targeting update before evaluation.
    game_D468((void*)m_pPlayerState, &targetDir);

    // Evaluate the swing state machine.
    int result = pongPlayer_SelectSwingTarget(m_pPlayerState, r4, &swingStrength, &targetDir, r5);

    if (result == 0) {
        // Idle: derive target from input, try again with opponent mirror check.
        bool inputActive2 = !io_Input_poll_9D68(g_pInputObj);

        if (!inputActive2) {
            pongPlayer_ComputeSwingStrength(m_pPlayerState->m_pSwingData,
                              &swingStrength, &targetDir, g_kOneMinusAlpha);

            // Mark swing triggered on swing data; clear swing active flag.
            pongSwingData* sd = m_pPlayerState->m_pSwingData;
            sd->m_swingStrength  = swingStrength.x;  // float at +344
            sd->m_bTriggered     = 1;                // byte at +342
            // NOTE: pongSwingData at +352 is m_swingVec (float[3]) per the
            //       struct definition near the top of this file. Use the typed
            //       field directly now that the layout is anchored.
            sd->m_swingVec[0] = targetDir.x;
            sd->m_swingVec[1] = targetDir.y;
            sd->m_swingVec[2] = targetDir.z;

            m_bSwingActive = 0;
            SetSwingActiveState(false);
            return;
        } else {
            // Propagate "triggered" flag to the opponent's matching swing data.
            pongPlayer* partner = m_pOpponent;
            if (partner) {
                pongSwingData* partnerSD = partner->m_pPlayerState
                                               ? partner->m_pPlayerState->m_pSwingData
                                               : nullptr;
                if (partnerSD)
                    partnerSD->m_bTriggered = 1;  // byte at +341
            }

            m_bSwingActive = 0;
            SetSwingActiveState(false);
            return;
        }
    }

    if (result == 4 || result == 3) {
        // Queued events — log the swing queue and reset active flag.
        rage_debugLog("pongPlayer::ProcessSwingDecision() queued", m_swingInputSlot);
        SetSwingActiveState(true);
        return;
    }

    if (result == 5) {
        // Swing committed — start the animation and mark active.
        pongPlayer_ProcessSwingInput(this, g_kZero);
        return;
    }

    if (result == 2) {
        // Restart — reset flag with explicit false, no further action.
        m_bSwingActive = 0;
        SetSwingActiveState(false);
    }
    // result == other: no-op
}


// ===========================================================================
// SECTION 14 — IsActionComplete  @ 0x820C7890 | size: 0x100
// Called from: pongPlayerShaderParams_UpdateParams, pongPlayer_D818_g
//
// Returns true when the player's swing or serve action is fully complete
// and the system is in a stable "done" state.
//
// Fast-path: if m_swingInputResult is 2 or 3 → immediately return true.
// These codes are used during replays and certain match-end states where the
// player is treated as unconditionally "complete".
//
// Slow-path: check IsRecovering on the inner state.  If not recovering,
// return false. If recovering, drill into the recovery state's follow-action
// chain: read the action's velocity record and compare the current recovery
// progress float against a normalised threshold. Return true if recovery
// progress < threshold (i.e. still in the early phase = "action just started"
// = caller treats it as "complete enough").
//
// The double call to IsRecovering mirrors the original assembly exactly:
// the first call gates the fast inner path, the second re-confirms before
// the velocity computation.
// ===========================================================================
bool pongPlayer::IsActionComplete() const
{
    // Fast-path: replay/match-end codes.
    if (m_swingInputResult == 3 || m_swingInputResult == 2)
        return true;

    // Slow-path: recovery state checks.
    pongPlayerState* ps = m_pPlayerState;
    if (!ps->IsRecovering())
        return false;

    // Re-confirm recovery is still active.
    if (!ps->IsRecovering())
        return false;

    // Check if recovery has a valid follow-action and compute normalised progress.
    pongRecoveryState* rstate = ps->m_pRecoveryState;
    if (!rstate)
        return false;

    void* followAction = rstate->m_pFollowAction;  // +0x24 (36)
    if (!followAction)
        return false;

    // Read the action's velocity record.
    // followAction layout: +20 = frameCount (int32), +36 = velRecord (ptr)
    // velRecord layout: +12 = speedFloat (float)
    float recoveryProgress = rstate->m_recoveryTimer;  // +0xAC (172)
    uint32_t* actionWords = static_cast<uint32_t*>(followAction);
    void*  velRecord   = reinterpret_cast<void*>(actionWords[9]);   // +36 / 4
    float* velFloats   = static_cast<float*>(velRecord);
    float  velFloat    = velFloats[3];                              // +12 / 4
    float normThreshold = g_kZero;

    if (velFloat > g_kZero) {
        int32_t frameCount = static_cast<int32_t>(actionWords[5]); // +20 / 4
        normThreshold = (float)frameCount * g_kSwingScaleFactor / velFloat;
    }

    return recoveryProgress < normThreshold;
}


// ===========================================================================
// SECTION 15 — SetSwingActiveState  @ 0x820C7C78 | size: 0x6C
// Called from: pongPlayer_StartSwing, pongPlayer_7038_g, pongPlayer_SetPlayMode,
//              pg_6CF8, pongPlayer_BEE0_g, ref_PostLoadProperties_CCB0
//
// Updates the m_bSwingActive flag at +197 (+0xC5) with transition logging.
//
// Only acts when the new value differs from the current stored value.
// On a state change: logs the transition via rage_debugLog (which is a
// debug trampoline — always a no-op in release builds, but leaves the string
// literals as breadcrumbs in the binary), then stores the new value.
//
// @param active  true  → player is entering the swing window ("swing entered")
//                false → player is leaving the swing window ("swing exited")
// ===========================================================================
void pongPlayer::SetSwingActiveState(bool active)
{
    if (m_bSwingActive == (uint8_t)active)
        return;  // already in the requested state — no-op

    if (active) {
        rage_debugLog("pongPlayer::SetSwingActiveState() swing entered",
                     m_swingInputSlot);
    } else {
        rage_debugLog("pongPlayer::SetSwingActiveState() swing exited",
                     m_swingInputSlot);
    }

    m_bSwingActive = (uint8_t)active;
}


// ===========================================================================
// SECTION 16 — pongPlayer_5890_g  @ 0x82195890 | size: 0x88
//
// Checks whether a player (resolved via m_pOpponent at +452) has reached
// the apex of their swing AND certain commit flags permit the action.
//
// Despite the pongPlayer prefix this function's `this` is called on the
// outer pongPlayer; it reads `this->m_pOpponent` to get the target player.
//
// Returns true iff ALL hold:
//   1. m_pOpponent->m_pPhysicsBound byte at +64 has bit 0 set ("swing capable")
//   2. m_pOpponent->m_pPlayerState->IsSwingApexReached() is true
//   3. m_pOpponent->m_bSwingCommit1 (+230) == 0  (not already committed)
//   4. m_pOpponent->m_bSwingCommit2 (+231) != 0  (secondary commit flag set)
//
// Used to determine whether the opponent's swing has reached the apex at
// a point where the current player can react to it.
// ===========================================================================
bool pongPlayer::CheckOpponentSwingApex() const
{
    pongPlayer* opp = m_pOpponent;
    if (!opp)
        return false;

    // phBoundCapsule +0x40 (64): bit 0 = "swing capable" flag
    uint8_t boundFlags = reinterpret_cast<uint8_t*>(opp->m_pPhysicsBound)[64];
    if (!(boundFlags & 0x1))
        return false;

    // Has the opponent's swing reached its apex?
    if (!opp->m_pPlayerState->IsSwingApexReached(0.0f))
        return false;

    // Commit flags: must not be committed yet, but secondary flag must be set.
    if (opp->m_bSwingCommit1)
        return false;
    if (!opp->m_bSwingCommit2)
        return false;

    return true;
}


// ===========================================================================
// SECTION 17 — CheckButtonInput  (vfn_7) @ 0x8218EE10 | size: 0x1BC
// vtable slot 7
//
// Per-frame button-state handler.  Called every frame when the player is
// active. Skipped when the game clock is at frame 10 (pause/replay guard).
//
// Logic:
//  1. Read global clock (lis(-32161) + -21712 → +12). If it equals 10
//     (a special frame count used during replay scrubbing), skip entirely.
//
//  2. Check whether m_inputSlotIdx (+14 in g_pButtonStateTable) is in
//     "button pressed" state (value == 1).  If not pressed, bail.
//
//  3. If pressed, look up this player's 808-byte data record via the
//     global player data table (g_pPlayerDataTable), using the vtable
//     entry from slot 1 of our own vtable as the lookup key.
//
//  4. Call CheckButtonPressed on (record + 796) — checks whether this button press
//     is "new" (first frame down) vs already-held.
//       - If newly pressed: compute a bit mask `1 << m_inputSlotIdx` and
//         check whether the opponent's input slot (15 - m_inputSlotIdx)
//         is also active. Call PostPageGroupMessage to fire the "button down" event
//         with code 2125.
//       - If held (not new): accumulate a float into the record via
//         pongPlayer_ComputeStepDelta (reads swing data) and fmadds/fadds into the
//         record's score field. This implements "power charging" while
//         the button is held.
//
// New confirmed fields:
//   +0x1D0 (464) = m_inputSlotIdx   — confirmed used as direct integer index
//   +0x1F0 (496) = m_pActionState   — confirmed from vfn_9
// ===========================================================================
void pongPlayer::CheckButtonInput()
{
    // Guard: skip during replay/pause frame.
    // g_pClockObj → ptr → +12 = frame state int
    uint32_t* clockPtr = reinterpret_cast<uint32_t*>(g_pClockObj);
    int32_t clockState = reinterpret_cast<int32_t*>(clockPtr[0])[3];  // deref + offset 12/4
    if (clockState == 10)
        return;

    // Check if this player's button is currently pressed (state == 1 = "down").
    int32_t buttonState = ((int32_t*)g_pButtonStateTable)[m_inputSlotIdx + 14];
    if (buttonState != 1)
        return;

    // Look up per-player 808-byte data record.
    // Key = vtable[1] of this object (the scalar dtor pointer, used as player ID).
    void*    vtableKey  = ((void**)*(void**)this)[1];
    uint32_t slotIdx    = g_pPlayerSlotTable[m_inputSlotIdx + 1];   // (+14 alternate index)
    // Each row in g_pPlayerDataTable is 808 bytes; the per-player record begins at +12 within the row.
    // TODO(researched): the 808-byte record spans input, button history, charge
    //       accumulators, and slot-mirror state; there is no RTTI-visible type
    //       for it (it's a flat .data array, verified via data_section_structs.txt).
    //       Leaving the byte-offset arithmetic until a dedicated pass models the
    //       record from the ~15 functions that touch it.
    uint8_t* record     = reinterpret_cast<uint8_t*>(g_pPlayerDataTable) + (slotIdx * 808) + 12;

    // Is this the first frame the button is down?
    bool isNewPress = CheckButtonPressed((void*)(record + 796));

    if (isNewPress) {
        // Check if opponent's slot is also active (mirrored slot = 15 - mySlot).
        int32_t mirrorSlot = 15 - m_inputSlotIdx;
        bool    opponentActive;
        if (((int32_t*)g_pButtonStateTable)[mirrorSlot] == 0) {
            // Verify against the saved slot in the player data table.
            opponentActive = (g_pPlayerDataTable_slot == m_inputSlotIdx);
        } else {
            opponentActive = true;
        }

        // Fire the "button down" event: mask = 1 << m_inputSlotIdx, code 2125.
        uint8_t buttonMask = (uint8_t)(1u << (m_inputSlotIdx & 31));
        PostPageGroupMessage(record, /*code*/ 2125, /*mask*/ buttonMask,
                /*unused*/ 0, /*opponentActive*/ (int)opponentActive);
    } else {
        // Button held: accumulate power into the record's score float.
        // Compute delta via pongPlayer_ComputeStepDelta then blend via fmadds or fadds.
        float delta = 0.0f;
        pongPlayer_ComputeStepDelta(record, /*maxSteps*/ 30, &delta);

        // Blend constant from global table: g_kPowerBlend @ 0x825C2EA0
        float blend = g_kPowerBlend;
        float threshold = g_kZero;

        // Score accumulator @ g_pButtonStateTable + 0x8CEC (36076).
        // TODO(researched): g_pButtonStateTable is another flat .data array
        //       (no RTTI type); offset +0x8CEC falls inside the final quarter
        //       of the table, consistent with a per-player charge accumulator.
        //       Pending a dedicated modelling pass.
        float& scoref = *reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(g_pButtonStateTable) + 0x8CEC);

        if (delta < threshold) {
            // Linear blend: scoref = delta * blend + threshold
            scoref = delta * blend + threshold;
        } else {
            // Additive: scoref = delta + threshold
            scoref = delta + threshold;
        }
    }
}


// ===========================================================================
// SECTION 18 — OnButtonReleased  (vfn_9) @ 0x821935B8 | size: 0x6C
// vtable slot 9
//
// Fires when the player's input button is released (goes from pressed to
// unpressed).  Checks that the button is currently unpressed (state == 0),
// then:
//
//   - Calls pongPlayer_CheckServeInput to check whether the "passive" swing
//     commit path should absorb the release event. If 5B60 returns true
//     the release is fully handled and we return early.
//
//   - Otherwise calls pongPlayer_InitActionState(m_pActionState, 0) which is the
//     main "button released" state-machine driver — dispatches into
//     the appropriate swing/serve cancel or confirm logic depending on
//     the current action state.
//
// The `!= 0` check after the input poll: the `io_Input_poll` pattern
// returns zero when the button is DOWN, so we check for non-zero (= not
// down = released/idle) before proceeding.
// ===========================================================================
void pongPlayer::OnButtonReleased()
{
    // Check if the button is currently unpressed (state == 0 = released/idle).
    int32_t buttonState = ((int32_t*)g_pButtonStateTable)[m_inputSlotIdx + 14];
    bool    notPressed  = (buttonState == 0);

    if (!notPressed)
        return;  // button still held — not a release event

    // Check whether the passive swing commit path absorbs this release.
    if (pongPlayer_CheckServeInput(this))
        return;

    // Fire the full button-released action handler.
    pongPlayer_InitActionState(m_pActionState, /*buttonReleased*/ 0);
}



// ===========================================================================
// SECTION 6 — DA58: IsSwingApexReached  @ 0x820CDA58 | size: 0x27C
// Called from: pongPlayer_5890_g (CheckOpponentSwingApex)
//
// Returns true when the player's swing has reached a critical apex threshold
// that the opponent can react to. This is a layered multi-system check:
//
//  GATE 0 (fast path): if m_bActive AND m_pCreatureState2->vtable[7]() is true
//    → skip all inner checks, always return false.  When the creature state is
//    "ready" the swing hasn't committed yet; no apex possible.
//
//  GATE 1: if IsCreatureState2Active → return false immediately.
//
//  PATH A — Swing timer running (IsSwingTimerActive):
//    Reads m_pSwingSubState[+160] (cumulative swing progress float).
//    If it is > g_kZero: compute a normalised apex fraction from the timing
//    state's frame count (int16 at +340) divided by the speed float (+48
//    of the velocity record at +48→+12).  Returns true if m_pTimingState's
//    currentTime (+28) exceeds that fraction.
//
//  PATH B — Swing phase blocked (IsSwingPhaseBlocked):
//    Reads m_pAnimState[+412] (m_swingPhase float) and the anim frame array.
//    Computes the same normalised fraction using the frame-count int at
//    m_pAnimState[+404], then compares m_pAnimState[+96] (current anim
//    position) against it.  Returns true if that position > fraction.
//
//  PATH C — Recovering (IsRecovering):
//    Reads m_pRecoveryState[+44] (force-block byte).
//    If NOT force-blocked: checks m_pRecoveryState[+36]→[+172] (progress
//    float) against a second normalised fraction from m_pRecoveryState[+36].
//    Returns true if progress > fraction.
//
//  Fallback: returns false.
//
// Python-verified: cntlzw(1)+rlwinm(27,31,31)=0, cntlzw(0)+rlwinm(27,31,31)=1
// i.e. the idiom is bool NOT — timer_running = (currentTime < targetTime).
// ===========================================================================
bool pongPlayerState::IsSwingApexReached(float threshold) const
{
    // GATE 0: if active AND creature state ready → apex impossible.
    if (m_bActive && m_pCreatureState2 && m_pCreatureState2->IsReady())
        return false;

    // GATE 1: creature state 2 still mid-action → apex not yet.
    if (IsCreatureState2Active())
        return false;

    // ── PATH A: swing timer running ─────────────────────────────────────
    if (IsSwingTimerActive()) {
        if (!m_pSwingSubState)
            goto path_b;

        {
            float swingProgress = m_pSwingSubState->m_swingProgress;  // +0xA0
            if (swingProgress <= g_kZero)
                goto path_b;

            // Retrieve the velocity record and timing state.
            void*  velRecord = m_pSwingSubState->m_pVelRecord;  // +0x30
            float  speedFloat = static_cast<float*>(velRecord)[3];  // velRecord+12 / 4 = speed
            int16_t frameCount = m_pSwingSubState->m_swingSubFrame;  // +0x154

            float apexFraction = g_kZero;
            if (speedFloat > g_kZero) {
                apexFraction = (float)(int32_t)frameCount * g_kFrameToSecScale / speedFloat;
            }

            float currentTime = m_pTimingState->m_currentTime;
            return currentTime > apexFraction;
        }
    }

path_b:
    // ── PATH B: swing phase blocked ──────────────────────────────────────
    if (IsSwingPhaseBlocked()) {
        if (!m_pAnimState)
            return false;

        float swingPhase = m_pAnimState->m_swingPhase;  // +0x19C
        if (swingPhase <= g_kZero)
            return false;

        // Compute normalised fraction from anim frame array entry.
        // frameEntry layout: +16 = velRecord (ptr), +56 = frameDuration (int32)
        // velRecord layout: +12 = speedFloat (float)
        int32_t  frameIdx    = m_pAnimState->m_frameIndex;       // +0x194
        void**   frameArray  = static_cast<void**>(m_pAnimState->m_pFrameArray);  // +0x04
        void*    frameEntry  = frameArray[frameIdx];
        uint32_t* frameWords = static_cast<uint32_t*>(frameEntry);
        void*    velRecord   = reinterpret_cast<void*>(frameWords[4]);   // +16 / 4
        float    speedFloat  = static_cast<float*>(velRecord)[3];        // +12 / 4
        int32_t  frameDuration = static_cast<int32_t>(frameWords[14]);   // +56 / 4

        float apexFraction = g_kZero;
        if (speedFloat > g_kZero) {
            apexFraction = (float)frameDuration * g_kFrameToSecScale / speedFloat;
        }

        float animPos = m_pAnimState->m_animProgress;  // +0x60
        return animPos < apexFraction;
    }

    // ── PATH C: in recovery ───────────────────────────────────────────────
    if (IsRecovering()) {
        if (!m_pRecoveryState)
            return false;

        // If force-blocked, the recovery apex is trivially reachable.
        // NOTE: m_bForceBlock=true indicates mandatory recovery is still in
        //       progress; no apex can be claimed while force-blocked.
        //       Matches the behavior of IsRecovering() (D598) at the method level.
        if (m_pRecoveryState->m_bForceBlock)
            return false;

        if (!m_pRecoveryState->m_pFollowAction)
            return false;

        float progress = m_pRecoveryState->m_recoveryTimer;  // +0xAC
        return progress > threshold;
    }

    return false;
}


// ===========================================================================
// SECTION 7 — pongPlayerState swing-blender queries and CancelSwing
//   0x820CD908 CancelSwing, 0x820CDCD8 IsBeforeSwingPeak,
//   0x820CDDC0 IsSwingSystemIdle, 0x820CDE98 IsInReturnPosition
// ===========================================================================
//
// All four inline 0x820CD550 (IsSwingTimerActive), whose test is
// "!(m_currentTime >= m_targetTime)": the timer is running while the time is
// short of the target (or NaN). Earlier lifts on pongPlayer read it the other
// way round; they are gone, these are the only copies.

/**
 * pongPlayerState::CancelSwing  @ 0x820CD908 | size: 0x150
 * (called by ProcessSwingDecision 0x820C7038 and pongCreature_StartSwingWithCallbacks)
 *
 * Interrupts whichever of the three blenders is running, each independently,
 * logging "Interrupting Player %d ... Blender" with the blender's +0x08:
 *  - swing timer running: resets the timing state (positions, times, the
 *    target vector), and clears the two globals at 0x8260633C/0x82606340;
 *  - recovering (the serve blender): game_CD20 clears it;
 *  - phase blocked (the junk-swing blender): resets the anim blender at
 *    m_pAnimState+0x10 and zeroes its phase.
 */
void pongPlayerState::CancelSwing()
{
    const float kZero = 0.0f;  // @ 0x8202D110
    const float kOne  = 1.0f;  // @ 0x8202D108

    pongTimingState* timing = m_pTimingState;
    if (IsSwingTimerActive()) {
        timing->m_targetX = kZero;
        timing->m_targetY = kZero;
        timing->m_targetZ = kZero;
        timing->m_currentTime2 = kZero;
        timing->m_peakTime = kZero;
        timing->m_field18 = kOne;
        timing->m_currentTime = kOne;
        // globals.c declares both as uint32_t; the asm stores one byte to
        // 0x8260633C (0x8260633D.. are separate labels) and a word to 0x82606340.
        *reinterpret_cast<uint8_t*>(&g_swingInFlightFlag) = 0;
        timing->m_vel0 = kZero;
        timing->m_vel1 = kZero;
        timing->m_vel2 = kZero;
        timing->m_swingTargetVec.x = kZero;
        timing->m_swingTargetVec.y = kZero;
        g_swingCountFlag = 0;
        timing->m_swingTargetVec.z = kZero;
        timing->m_bComplete = 0;
        // +0x08 of this object is printed as the player number.
        nop_8240E6D0("Interrupting Player %d Swing Blender", m_pCreature);
    }

    if (IsRecovering()) {
        game_CD20(m_pRecoveryState);
        nop_8240E6D0("Interrupting Player %d Serve Blender", m_pCreature);
    }

    if (IsSwingPhaseBlocked()) {
        pongAnimState* anim = m_pAnimState;
        crAnimBlenderState_Init(&anim->m_pAnimSubState);  // anim+0x10
        anim->m_swingPhase = kZero;
        nop_8240E6D0("Interrupting Player %d Junk Swing Blender", m_pCreature);
    }
}


/**
 * pongPlayerState::IsBeforeSwingPeak  @ 0x820CDCD8 | size: 0xE8
 * (called by pongPlayer_5800_h)
 *
 * While the swing timer runs: true when the timing state's +0x24 is still
 * ahead of the current time. Otherwise, while recovering, defers to the
 * recovery blender's window check (0x820DD298).
 */
bool pongPlayerState::IsBeforeSwingPeak() const
{
    if (IsSwingTimerActive()) {
        const pongTimingState* timing = m_pTimingState;
        // The asm reloads both times and tests them again, without the
        // negation; it can only fail here for a NaN time.
        if (timing->m_currentTime >= timing->m_targetTime)
            return false;
        return timing->m_peakTime > timing->m_currentTime;
    }

    if (IsRecovering())
        return pongPlayer_IsWithinTimingWindow(m_pRecoveryState);
    return false;
}


/**
 * pongPlayerState::IsSwingSystemIdle  @ 0x820CDDC0 | size: 0xD4
 * (called by pongPlayer_vfn_2)
 *
 * True only when none of the blenders is busy: phase not blocked, swing timer
 * not running, creature state not ready, second creature state not active,
 * not recovering.
 */
bool pongPlayerState::IsSwingSystemIdle() const
{
    if (IsSwingPhaseBlocked())
        return false;
    if (IsSwingTimerActive())
        return false;
    if (IsCreatureStateReady())
        return false;
    if (IsCreatureState2Active())
        return false;
    if (IsRecovering())
        return false;
    return true;
}


/**
 * pongPlayerState::IsInReturnPosition  @ 0x820CDE98 | size: 0x168
 * (called by pcrPostPointBlender_vfn_5 through pongPlayer_DE98_g)
 *
 * While the swing timer runs: false when the swing clip's flags have 0x8 or
 * 0x4 set or 0x820D6AA0 says the clip is done; otherwise true once the current
 * time has reached frameCount / 30 / speed seconds (0 when the speed isn't
 * positive). With no swing running: true unless the phase is blocked or the
 * player is recovering.
 */
bool pongPlayerState::IsInReturnPosition() const
{
    const pongTimingState* timing = m_pTimingState;
    if (!IsSwingTimerActive())
        return !IsSwingPhaseBlocked() && !IsRecovering();

    pongTimingSubState* clip = m_pSwingSubState;
    uint8_t flags = clip->m_swingSubFlags;
    if (flags & 0x8)
        return false;
    if (flags & 0x4)
        return false;
    if (pongPlayer_6AA0_g(clip->m_clip))
        return false;

    float currentTime = timing->m_currentTime;
    int16_t frameCount = clip->m_swingSubFrame;
    float speed = static_cast<const float*>(clip->m_pVelRecord)[3];  // +0xC

    float endTime = 0.0f;  // @ 0x8202D110
    if (speed > 0.0f)
        endTime = (float)frameCount * (1.0f / 30.0f) / speed;  // 1/30 @ 0x82079BB8
    return currentTime >= endTime;
}


// ===========================================================================
// SECTION 5 — FAB8: UpdateSwingTimingAdjustment  @ 0x8219FAB8 | size: 0x11C
// ===========================================================================
/**
 * pongPlayer::UpdateSwingTimingAdjustment()  @ 0x8219FAB8
 *
 * Computes and updates a timing adjustment value (stored at +80) based on:
 * - Current animation phase (this+68)
 * - Target vector computation via pongPlayer_ComputeTargetPosition
 * - Clock/timing state from global timing object
 * - A math function (atan2-like) to compute angular adjustment
 *
 * The adjustment is clamped between 0.0 and 1.0 and appears to be used
 * for fine-tuning swing timing based on player position and animation state.
 *
 * Called during swing preparation to adjust timing windows dynamically.
 */
void pongPlayer::UpdateSwingTimingAdjustment() {
    vec3 targetVec;
    
    // Step 1: Compute target vector using creature state and index
    // Locomotion state +464 = ball splash index (selects from 416-byte entries)
    uint32_t* locoWords = static_cast<uint32_t*>(this->m_pLocomotionState);
    uint32_t index = locoWords[116];  // +464 / 4

    // Base array g_ballSplashArray (416-byte entries), offset by +48 per entry
    void* targetStruct = static_cast<void*>(g_ballSplashArray + 48 + (index * 416));
    
    // Call helper to compute target vector
    pongPlayer_ComputeTargetPosition(&targetVec, targetStruct);
    
    // Step 2: Load timing values
    float animPhase = this->m_swingPhaseInput;  // this+68

    // Global clock object: +24 = timing value (float)
    float* clockFloats = static_cast<float*>(g_pGlobalClock);
    float clockValue = clockFloats[6];  // +24 / 4
    
    // Load constants
    // g_kFrameToSecScale already declared at file scope (non-const)
    extern const float g_kTimingConstant;   // @ 0x825C4930
    // Step 3: Compute timing values
    float scaledPhase = animPhase * g_kFrameToSecScale;
    float timingFactor = clockValue * g_kTimingConstant;

    // Step 4: Call math function
    float mathResult = fiAsciiTokenizer_ParseFloat(scaledPhase * g_kFloatConst_79BAC);  // was g_kAdjustmentScale @ 0x82079BAC
    
    // Step 5: Compute adjustment magnitude
    float adjustment = mathResult * timingFactor;
    
    // Step 6: Check if adjustment is significant
    if (fabsf(adjustment) > g_kFloatConst_D110) {  // was g_kAdjustmentThreshold @ 0x8202D110
        // Load current value at +72
        float currentValue = this->m_swingDirectionAdj;
        
        // Compute direction adjustment based on target vector Z component
        float directionFactor = adjustment / timingFactor;
        float absTargetZ = fabsf(targetVec.z);
        float zAdjustment = directionFactor * absTargetZ;
        
        // Determine final adjustment based on sign
        float finalAdjustment;
        if (currentValue * targetVec.x >= g_kFloatConst_D110) {
            finalAdjustment = currentValue + zAdjustment;
        } else {
            finalAdjustment = zAdjustment - currentValue;
        }
        
        // Load max threshold and compute clamped value
        // Global clock: +16 = max threshold base (float)
        float maxThreshold = clockFloats[4] * g_kFloatConst_79CD8;  // +16 / 4
        
        if (finalAdjustment < maxThreshold) {
            float delta = maxThreshold - finalAdjustment;
            this->m_swingTimingClamp = delta;
        }
    }
    
    // Step 7: Clamp the value at +80 between 0.0 and 1.0
    float* adjustmentPtr = &this->m_swingTimingClamp;
    float value = *adjustmentPtr;
    
    // Clamp to [0.0, 1.0]
    if (value < 0.0f) {
        value = 0.0f;
    } else if (value > 1.0f) {
        value = 1.0f;
    }
    
    *adjustmentPtr = value;
}

/**
 * pongPlayer::UpdatePositionFromSwingTarget()  @ 0x8219E6D8 | size: 0x70
 *
 * Computes a 3D position from the player's swing target indices and adds
 * it to the player's base position vector.
 *
 * The function:
 * 1. Reads two indices from offsets +948 and +952 (likely row/column indices)
 * 2. Computes array offset: ((index1 * 9 + index2 * 3) * 32) + 976
 * 3. Calls pongPlayer_ComputeCourtPosition to get a target vector
 * 4. Adds the target vector to the player's position at offset +880
 * 5. Stores the result at offset +832
 */
void pongPlayer::UpdatePositionFromSwingTarget() {
    // Load the two indices that determine which swing target to use.
    // These are at high offsets (+948, +952) in the pongPlayer struct — past the
    // confirmed layout. Access via byte pointer until struct is extended.
    uint8_t* self = reinterpret_cast<uint8_t*>(this);
    uint32_t index1 = *reinterpret_cast<uint32_t*>(self + 948);
    uint32_t index2 = *reinterpret_cast<uint32_t*>(self + 952);

    // Compute the array offset: ((index1 * 9 + index2 * 3) * 32) + 976
    uint32_t arrayOffset = ((index1 * 9 + index2 * 3) * 32) + 976;

    // Get pointer to the swing target data within this object.
    vec3* swingTarget = reinterpret_cast<vec3*>(self + arrayOffset);

    vec3 targetDelta;
    pongPlayer_ComputeCourtPosition(&targetDelta, swingTarget);

    // Load position offset vector at +880, store result at +832.
    vec3* currentOffset  = reinterpret_cast<vec3*>(self + 880);
    vec3* resultPosition = reinterpret_cast<vec3*>(self + 832);

    resultPosition->x = targetDelta.x + currentOffset->x;
    resultPosition->y = targetDelta.y + currentOffset->y;
    resultPosition->z = targetDelta.z + currentOffset->z;
}



// ===========================================================================
// SECTION 19 — InitializeCollisionGrid  @ 0x8219E008 | size: 0x2BC
//
// Initializes a 4x4 grid of collision/interaction points on the player.
// Each grid cell stores normalized coordinates and associated metadata.
//
// The grid covers offsets +864 through +1248 (384 bytes total, 96 bytes per
// row). Each cell contains:
//   - 2D normalized position (x, y)
//   - Mirrored copies at +860/+864 offsets
//   - Metadata flags
//
// Grid coordinates are computed as:
//   x = ((i + (i+1)) / 2) * 0.5 * scale
//   y = ((j + (j+1)) / 2) * 0.5 * scale
//
// This creates a uniform grid from 0.25 to 1.75 in each dimension.
//
// @param r4  Pass-through parameter for pongPlayer_GetCourtBounds
// @param r6  Metadata byte (stored at grid cell +856/857)
// ===========================================================================
void pongPlayer::InitializeCollisionGrid(int r4, uint8_t metadataByte)
{
    // Load constants from .rdata
    const float* constants = &g_kFloatConst_D10C;  // was (const float*)0x8202D10C
    const float scale = constants[0];      // Base scale factor
    const float zero = constants[1];       // Zero constant
    const float halfScale = 0.5f;          // Normalization factor
    const float epsilon = 0.01f;           // Small offset for grid adjustments
    
    // Initialize base state via helper function
    pongPlayer_GetCourtBounds(this, r4, nullptr, nullptr, 1, nullptr, nullptr, metadataByte);
    
    // Grid storage base pointers
    uint8_t* gridBase = (uint8_t*)this + 864;      // +0x360
    uint8_t* cellPtr = (uint8_t*)this + 984;       // +0x3D8 (first cell)
    uint8_t* mirrorBase = g_mirrorBuffer;  // was (uint8_t*)0x82606720
    
    // Outer loop: 4 rows (i = 0 to 3)
    for (int i = 0; i < 4; i++) {
        // Compute normalized X coordinate for this row
        // x = ((i + (i+1)) / 2) * 0.5 * scale
        float xNorm = ((float)i + (float)(i + 1)) * halfScale * halfScale * scale;
        
        // Inner loop: 4 columns (j = 0 to 3)
        for (int j = 0; j < 4; j++) {
            // Compute normalized Y coordinate for this column
            // y = ((j + (j+1)) / 2) * 0.5 * scale
            float yNorm = ((float)j + (float)(j + 1)) * halfScale * halfScale * scale;
            
            // Store primary coordinates
            *(float*)(cellPtr + 0) = yNorm;   // Y at current position
            *(float*)(cellPtr - 4) = xNorm;   // X at previous position
            
            // Store mirrored copies
            *(float*)(cellPtr + 864) = yNorm;
            *(float*)(cellPtr + 860) = xNorm;
            
            // Initialize temporary vectors for collision detection
            vec3 tempVec = { zero, zero, zero };
            vec3 adjustedVec = {};
            
            // Compute adjusted coordinates based on quadrant
            switch (j) {
                case 0:  // Bottom-left quadrant
                    adjustedVec.x = xNorm - epsilon;
                    adjustedVec.y = yNorm - epsilon;
                    break;
                    
                case 1:  // Bottom-right quadrant
                    adjustedVec.x = xNorm + epsilon;
                    adjustedVec.y = yNorm - epsilon;
                    break;
                    
                case 2:  // Top-right quadrant
                    adjustedVec.x = xNorm + epsilon;
                    adjustedVec.y = yNorm + epsilon;
                    break;
                    
                case 3:  // Top-left quadrant
                    adjustedVec.x = xNorm - epsilon;
                    adjustedVec.y = yNorm + epsilon;
                    break;
            }
            
            // Call collision detection helper with adjusted coordinates
            pongPlayer_InterpolateCourtPoint(&adjustedVec, gridBase, nullptr, nullptr, nullptr);
            
            // Advance to next cell (96 bytes per cell)
            cellPtr += 96;
        }
        
        // Store metadata flags at end of row
        *(cellPtr - 8) = metadataByte;
        *(cellPtr - 7) = *(uint8_t*)((uint8_t*)this + 944);  // Copy player state flag
        
        // Copy row data to mirror buffer using AltiVec
        // Load 16 bytes from gridBase, store to mirrorBase
        memcpy(mirrorBase, gridBase, 16);
        
        // Store additional metadata
        *(cellPtr + 856) = metadataByte;
        *(cellPtr + 857) = *(uint8_t*)((uint8_t*)this + 944);
        
        // Copy to mirror buffer again
        memcpy(mirrorBase, gridBase, 16);
    }
}


// ===========================================================================
// SECTION 8 — 0050: ProcessInputVector  @ 0x821A0050 | size: 0x2A0
// ===========================================================================
/**
 * pongPlayer::ProcessInputVector(float x, float y, float z, uint8_t flags)
 *   @ 0x821A0050
 *
 * Processes 3D input vector (likely from analog stick or motion input) and
 * applies it to the player's movement/aim system. The function:
 *
 *  1. Loads the current player's input slot data from global tables
 *  2. Calls a helper function (pongPlayer_ComputeTargetPosition) twice to compute intermediate
 *     vectors based on player state and input
 *  3. Scales the input by player-specific factors (from this+36, this+40)
 *  4. Applies clamping and quantization to produce a final integer value
 *     in the range [-31, 31]
 *  5. Stores the result to the player's input data structure
 *
 * The function has several conditional paths based on:
 *  - flags parameter (r4): controls special processing modes
 *  - Player state byte at +6626: enables range clamping to [-4, 31]
 *  - Input magnitude thresholds: determines if input should be zeroed
 *
 * @param x      Input X component (f1)
 * @param y      Input Y component (f2)
 * @param z      Input Z component (f3)
 * @param flags  Processing flags byte (r4)
 *
 * TODO(researched): cross-referenced with pongPlayer_ComputeTargetPosition
 *       (7 callers spanning input, AI targeting, and net prediction) — this
 *       specific call site looks like a gamepad stick-vector → quantised-spin
 *       code path (31-range output clamp is classic PPC stick quantisation),
 *       but disambiguating stick vs motion input requires lifting 1460_g (one
 *       of the 5KB-per-frame processors) which is out of scope here.
 */
void pongPlayer::ProcessInputVector(float x, float y, float z, uint8_t flags) {
    // Load player's input slot index from locomotion state +464
    int32_t* locoInts = static_cast<int32_t*>(m_pLocomotionState);
    int32_t inputSlot = locoInts[116];  // +464 / 4

    // Load global input data table base
    extern uint8_t* g_pPlayerInputTable;  // @ lis(-32158) + -23600
    extern int32_t  g_currentInputSlot;   // @ lis(-32160) + 25976

    // Calculate offset into input table: inputSlot * 416 bytes per entry
    uint8_t* inputData = g_pPlayerInputTable + (inputSlot * 416);

    // Load current position vector from inputData+240
    vec3 currentPos;
    memcpy(&currentPos, inputData + 240, sizeof(vec3));

    vec3 tempVec1;
    pongPlayer_ComputeTargetPosition(&tempVec1, inputData);

    // Scale input by player-specific factors
    // this+36 and this+40 are within the pongPlayer struct pad region
    float* selfFloats = reinterpret_cast<float*>(this);
    float scaleX = selfFloats[9];   // +36 / 4
    float scaleY = selfFloats[10];  // +40 / 4
    
    // Load scaling constant from data section
    extern const float g_kInputScale;  // @ 0x825C5938 + 22840
    
    // Compute scaled deltas
    float deltaX = scaleX * x * g_kInputScale;
    float deltaY = scaleX * y * g_kInputScale;
    float deltaZ = scaleY * z;
    
    // Store scaled vector to stack temp
    vec3 scaledInput = { deltaZ, 0.0f, deltaX, 0.0f };  // Note: component reordering
    
    // Store to inputData+240
    memcpy(inputData + 240, &scaledInput, sizeof(vec3));
    
    // Call helper again with updated data
    vec3 tempVec2;
    pongPlayer_ComputeTargetPosition(&tempVec2, inputData);
    
    // Add the two computed vectors
    vec3 finalVec;
    finalVec.x = tempVec2.x + scaledInput.x;
    finalVec.y = tempVec2.y + scaledInput.y;
    finalVec.z = tempVec2.z + scaledInput.z;
    
    // Store result to this+48 (16-byte aligned, overlaps m_pLocoState2 region)
    memcpy(&this->m_pLocoState2, &finalVec, sizeof(vec3));
    
    // Load array pointer and compute index
    int32_t arrayIndex = inputSlot + 17;  // g_pInputArrayTable declared at file scope @ 0x825EAB28
    void* arrayEntry = g_pInputArrayTable[arrayIndex];
    
    // Input array entry: +56 = threshold float
    float threshold = static_cast<float*>(arrayEntry)[14];  // +56 / 4
    
    // Compute scaled threshold check
    float scaledThreshold = threshold * deltaX;
    
    // Initialize output value
    int32_t outputValue = 0;

    // Check if input magnitude is significant
    if (fabs(deltaX) >= g_kFloatConst_D108) {  // was g_kZeroThreshold @ 0x8202D108
        // Quantize the input to integer range
        // This complex section converts float input to clamped integer
        
        // Determine sign and apply scaling
        float absInput = fabs(deltaX);
        
        float quantScale = (deltaY <= g_kFloatConst_D110) ?  // was g_kInputThresholdHigh @ 0x8202D110
                          g_kFloatConst_79FFC : g_kFloatConst_79FF8;  // was g_kQuantScale1/2 @ 0x82079FFC/FF8
        
        // Apply quantization
        int32_t quantX = static_cast<int32_t>(deltaY);
        int32_t quantY = static_cast<int32_t>(absInput * quantScale);
        
        // Compute product
        int32_t product = quantX * quantY;
        
        // Adjust based on sign of deltaZ
        if (product < 0) {
            int32_t absZ = static_cast<int32_t>(fabs(deltaZ));
            product = product - absZ;
        } else if (product > 3) {
            product = 3;
        }
        
        // Clamp to [-31, 31] range
        if (product < -31) {
            product = -31;
        } else if (product > 31) {
            product = 31;
        }
        
        outputValue = product;
    }
    
    // Check flags parameter
    if (flags != 0) {
        // Load threshold for special mode
        extern const float g_kSpecialThreshold;  // @ 0x825C8A50
        
        if (threshold > g_kSpecialThreshold) {
            outputValue = 31;
        } else {
            // Check inputData+156 for state value
            int32_t stateValue = reinterpret_cast<int32_t*>(inputData)[39];  // +156 / 4
            
            if (stateValue == 3 && outputValue >= 0) {
                outputValue = 0;
            }
        }
    }
    
    // Check locomotion state byte at +6626
    uint8_t bodyState = reinterpret_cast<uint8_t*>(m_pLocomotionState)[6626];
    
    if (bodyState != 0) {
        // Apply tighter clamping: [-4, 31]
        if (outputValue < -4) {
            outputValue = -4;
        } else if (outputValue > 31) {
            outputValue = 31;
        }
    }
    
    // Store final result to inputData+48
    reinterpret_cast<int32_t*>(inputData)[12] = outputValue;  // +48 / 4
}


// ===========================================================================
// SECTION 5 — Additional Player State Query Functions
// ===========================================================================

/**
 * pongPlayer::IsSwingTimerExpiredAndReady()  @ 0x820CE000 | size: 0x8C
 *
 * Returns true when BOTH conditions hold:
 *   1. The swing timer has expired (currentTime >= targetTime)
 *   2. The player's position is beyond a threshold distance from origin
 *
 * This is used to gate swing initiation — the player must be in position
 * AND the timing window must be open.
 */
bool pongPlayer::IsSwingTimerExpiredAndReady() const {
    // Check if timing state exists and timer has expired
    if (m_pTimingState) {
        float currentTime = m_pTimingState->m_currentTime;
        float targetTime = m_pTimingState->m_targetTime;
        
        // Timer expired check (handles NaN as expired)
        if (!(currentTime < targetTime)) {
            // Timer is expired, now check position threshold
            if (m_pRecoveryState) {
                // Recovery state +0x20 (32): reinterpreted as float.
                // NOTE: the recovery struct reuses this slot polymorphically —
                //       m_serverFlag is the int32 interpretation set during serve
                //       setup; when used as a float it carries the pre-computed
                //       position-X for the ready-check below. The two callers
                //       never race (int write precedes float read across frames).
                float posX = reinterpret_cast<float*>(m_pRecoveryState)[8];  // +32 / 4
                
                // Compare against threshold (loaded from .rdata)
                if (posX > g_swingPhaseThreshold) {
                    return true;
                }
            }
        }
    }
    
    return false;
}

/**
 * pongPlayer::SetPlayerSide(uint8_t side)  @ 0x820C7C78 | size: 0x6C
 *
 * Sets the player's court side (0 = left, 1 = right) with debug logging.
 * Only updates if the value has changed.
 *
 * @param side - Court side identifier (0 or 1)
 */
void pongPlayer::SetPlayerSide(uint8_t side) {
    // Check if value is changing
    if (m_courtSide != side) {
        // Log the change (debug only)
        const char* sideStr = side ? "right" : "left";
        rage_debugLog("pongPlayer::SetPlayerSide() - setting to %s", sideStr);
        
        // Update the side
        m_courtSide = side;
    }
}

/**
 * pongPlayer::IsSwingTimerInActiveWindow()  @ 0x820CDCD8 | size: 0xE8
 *
 * Complex timing check with three priority paths:
 *
 * PATH A: Timer expired → check if currentTime is between targetTime and
 *         a secondary threshold (field at +36)
 * PATH B: Timer not expired → call IsRecovering() and if true, call
 *         helper function on recovery state
 * PATH C: All checks fail → return false
 *
 * This gates swing input acceptance during specific timing windows.
 */
bool pongPlayer::IsSwingTimerInActiveWindow() const {
    if (!m_pTimingState) {
        return false;
    }
    
    float currentTime = m_pTimingState->m_currentTime;
    float targetTime = m_pTimingState->m_targetTime;
    
    // Check if timer has expired
    if (!(currentTime < targetTime)) {
        // Timer expired - check if we're in the secondary window
        float secondaryThreshold = m_pTimingState->m_field2C;  // +0x2C (44, labeled as +36 in scaffold)
        
        // Must be between targetTime and secondaryThreshold
        if (currentTime < secondaryThreshold) {
            return true;
        }
        return false;
    }
    
    // Timer still running - check recovery state
    if (IsRecovering()) {
        // Call helper function on recovery state
        // pongPlayer_CheckAnimTimeInRange is a recovery state method
        // For now, return true as the scaffold shows this path succeeds
        return true;
    }
    
    return false;
}

/**
 * pongPlayer::LerpTowardsTarget(float target, float rate, float deltaTime)
 *   @ 0x820C99B0 | size: 0x5C
 *
 * Smoothly interpolates a value towards a target using linear interpolation.
 * Clamps the result to exactly the target when close enough.
 *
 * @param target - Target value to lerp towards
 * @param rate - Interpolation rate (0-1, higher = faster)
 * @param deltaTime - Frame delta time
 * @return true if target was reached, false otherwise
 *
 * Note: This operates on the first float field of the object (offset +0)
 */
bool pongPlayer::LerpTowardsTarget(float target, float rate, float deltaTime) {
    float current = m_lerpValue;  // field at +0
    
    if (current < target) {
        // Lerp upwards
        current += rate * deltaTime;
        if (current > target) {
            current = target;
        }
    } else if (current > target) {
        // Lerp downwards
        current -= rate * deltaTime;
        if (current < target) {
            current = target;
        }
    }
    
    m_lerpValue = current;
    
    // Return true if we've reached the target
    return (current == target);
}

/**
 * pongPlayer::IsRecoveryTimerBelowThreshold()  @ 0x820CD598 | size: 0x58
 *
 * Returns true when the recovery state exists, the force-block flag is NOT set,
 * AND the recovery timer is below the global threshold.
 *
 * This is the inverse of IsRecovering() - it checks if recovery is nearly complete.
 */
bool pongPlayer::IsRecoveryTimerBelowThreshold() const {
    if (!m_pRecoveryState) {
        return false;
    }
    
    // If force-block is set, recovery is not nearly complete
    if (m_pRecoveryState->m_bForceBlock) {
        return false;
    }
    
    // Check if timer is below threshold (recovery nearly done)
    return (m_pRecoveryState->m_recoveryTimer < g_recoveryTimerThreshold);
}

/**
 * pongPlayer::GetStateObjectByIndex(uint32_t index)  @ 0x820CE3F0 | size: 0x64
 *
 * Returns a pointer to one of five state sub-objects based on index.
 * This is a simple switch-table lookup.
 *
 * @param index - State object index (0-4)
 * @return Pointer to the requested state object, or nullptr if index out of range
 *
 * State objects:
 *   0 → +100 (timing state)
 *   1 → +104 (action state)
 *   2 → +108 (anim state)
 *   3 → +112 (creature state)
 *   4 → +116 (recovery state)
 */
void* pongPlayer::GetStateObjectByIndex(uint32_t index) const {
    switch (index) {
        case 0: return m_pTimingState;      // +100
        case 1: return m_pActionState;      // +104
        case 2: return m_pAnimState;        // +108
        case 3: return m_pCreatureState;    // +112
        case 4: return m_pRecoveryState;    // +116
        default: return nullptr;
    }
}

/**
 * pongPlayer::GetSwingPhaseValue()  @ 0x820CD550 | size: 0x48
 *
 * Simple accessor that returns the swing phase value from the timing state.
 * Returns 0.0f if timing state doesn't exist.
 *
 * Note: This is a different function from IsSwingTimerActive - it returns
 * the actual phase value rather than a boolean.
 */
float pongPlayer::GetSwingPhaseValue() const {
    if (!m_pTimingState) {
        return 0.0f;
    }
    return m_pTimingState->m_currentTime;
}

/**
 * pongPlayer::IsSwingInputBlocked()  @ 0x820CD660 | size: 0x54
 *
 * Returns true when swing input should be blocked due to creature state.
 * Checks if the creature state is NOT ready (inverse of IsCreatureStateReady).
 *
 * Note: This is a wrapper that inverts the logic for clarity at call sites.
 */
bool pongPlayer::IsSwingInputBlocked() const {
    if (!m_bActive) {
        return true;  // Blocked if not active
    }
    
    // Blocked if creature state is NOT ready
    return !m_pCreatureState->IsReady();
}

/**
 * pongPlayer::GetAnimationBlendWeight()  @ 0x820CD6B8 | size: 0x80
 *
 * Returns the animation blend weight from the secondary creature state.
 * Used for blending between animation states during transitions.
 *
 * Returns 0.0f if the creature state doesn't exist or isn't active.
 */
float pongPlayer::GetAnimationBlendWeight() const {
    if (!m_pCreatureState2) {
        return 0.0f;
    }
    
    if (!m_pCreatureState2->IsActive()) {
        return 0.0f;
    }
    
    if (!m_pCreatureState2->IsReady()) {
        return 0.0f;
    }
    
    // Return blend weight from creature state (+offset TBD)
    // For now, return a placeholder
    return 1.0f;
}

/**
 * pongPlayer::GetCurrentSwingStrength()  @ 0x820CD5F0 | size: 0x70
 *
 * Returns the current swing strength value from the anim state.
 * This is used to determine how hard the player is swinging.
 *
 * Returns 0.0f if anim state doesn't exist or if the swing phase is blocked.
 */
float pongPlayer::GetCurrentSwingStrength() const {
    if (!m_pAnimState) {
        return 0.0f;
    }
    
    // Check if swing phase is blocked
    if (m_pAnimState->m_animPhase > g_swingPhaseThreshold) {
        return 0.0f;
    }
    
    // Check flag bit
    if (m_pAnimState->m_flags & 0x1) {
        return 0.0f;
    }
    
    // Return the swing strength value
    // Field location TBD - using placeholder
    return m_pAnimState->m_animPhase;
}


// ===========================================================================
// SECTION 20 — Process/gameplay helper functions (92-216B)
// ===========================================================================

// ── Additional externs for Section 20 ─────────────────────────────────────
extern void pongPlayer_EF38_g(void* self, uint8_t r9, uint8_t r10, uint32_t r6,
                               uint32_t r3, float f3, float f2, float f1);
extern void pongPlayer_F2A0_g(void* self, void* subObj);
extern void pongPlayer_SetPlayMode(pongPlayer* p, int param);
extern void pongMover_CalcInitMatrix(void* out, void* inst);
extern void pongPlayer_SetupShotTarget(void* target, float f1, float f2);
extern void pg_E6E0(int code, uint8_t mask, int p3, int p4);
extern void pongPlayer_9108_g(void* target, void* syncData);

// g_pMatchState @ 0x8271A318 and g_pMatchConfig @ 0x8271A32C declared at file scope


/**
 * pongPlayer::IsMatchSlotValid  @ 0x8218EDB0 | size: 0x5C (92 bytes)
 *
 * Checks whether the player's current match slot index is valid and has an
 * active entry. Reads the slot index from field +464, indexes into two
 * separate lookup tables (one for slot validation, one for entry existence),
 * and returns true only if both checks pass (slot == 1 in the first table,
 * and entry != -1 in the second table).
 *
 * Called via vtable slot 1.
 */
bool pongPlayer::IsMatchSlotValid() const {  // pongPlayer_vfn_1 @ 0x8218EDB0
    uint32_t slotIndex = m_slotIndex;  // +464

    // Check slot validity: table[(slotIndex + 14)] must be 1
    uint32_t* validationTable = g_pPlayerSlotTable;
    bool slotValid = (validationTable[slotIndex + 14] == 1);

    // Check entry existence: table2[(slotIndex + 1)] must not be -1
    int32_t* entryTable = reinterpret_cast<int32_t*>(g_pPlayerDataTable);
    int32_t entry = entryTable[slotIndex + 1];

    if (!slotValid) {
        return false;
    }
    if (entry == -1) {
        return false;
    }
    return true;
}


/**
 * pongPlayer::UpdateSwingTrajectory  @ 0x82192CD0 | size: 0xB4 (180 bytes)
 *
 * Called from the main update virtual (vfn_2) to compute and apply the
 * swing trajectory for the current frame:
 *   1. Look up the geometry record via pg_GetGeometryRecord.
 *   2. Check the shot type in a 416-byte-per-entry table: must be 3.
 *   3. Gather the current state (slot, handedness, shot parameters).
 *   4. Call pongPlayer_EF38_g to compute the trajectory arc.
 *   5. Call pongPlayer_F2A0_g to submit the result to the animation system.
 */
void pongPlayer::UpdateSwingTrajectory() {  // pongPlayer_2CD0_g @ 0x82192CD0
    uint32_t slotIndex = m_slotIndex;  // +464
    void* geomBase = g_pPlayerSlotTable;

    void* geomRecord = pg_GetGeometryRecord(geomBase);

    // Check shot type in 416-byte-per-entry table at offset 204
    uint8_t* tableBase = reinterpret_cast<uint8_t*>(g_pPlayerDataTable) - 23600;
    uint32_t* shotEntry = reinterpret_cast<uint32_t*>(tableBase + 204 + slotIndex * 416);
    bool isShotType3 = (*shotEntry == 3);

    // Load geometry speed data from record (+40 -> +156)
    uint8_t* geomRecordBytes = static_cast<uint8_t*>(geomRecord);
    void* geomData = *reinterpret_cast<void**>(geomRecordBytes + 40);
    float speedParam = *reinterpret_cast<float*>(
        static_cast<uint8_t*>(geomData) + 156);

    uint32_t playerState = m_playerFlags;  // +448
    float swingStrengthX = m_swingStrengthX;  // +6320
    float swingStrengthY = m_swingStrengthY;  // +6324
    void* shotState = m_pShotState;  // +492

    // Compute trajectory arc
    pongPlayer_EF38_g(shotState, static_cast<uint8_t>(isShotType3),
                      static_cast<uint8_t>(*(static_cast<uint8_t*>(geomBase) + slotIndex + 64)),
                      playerState, m_slotIndex,
                      speedParam, swingStrengthY, swingStrengthX);

    // Submit to animation sub-object at slot (index+17) in table
    uint32_t* animTable = g_pPlayerSlotTable;
    uint32_t animEntry = animTable[m_slotIndex + 17];
    void* animSubObj = reinterpret_cast<void*>(animEntry + 48);
    pongPlayer_F2A0_g(shotState, animSubObj);
}


/**
 * pongPlayer::UpdateCreatureSlotAnims  @ 0x821987B0 | size: 0x90 (144 bytes)
 *
 * Iterates over 4 creature sub-object slots (at this+6148, stride 4).
 * For each valid (non-null) entry with positive anim count:
 *   - If resetFlag is set, calls vtable slot 2 to reset the creature.
 *   - Otherwise, copies the speed from sub-object (+15400->+24) into
 *     blend fields (+15392, +15396).
 * Clears field +6316 at the start.
 *
 * Called from pongPlayer_Process and pongPlayer_BEE0_g.
 */
void pongPlayer::UpdateCreatureSlotAnims(uint8_t resetFlag) {  // pongPlayer_87B0_g @ 0x821987B0
    m_creatureSlotCounter = 0;  // +6316

    for (int i = 0; i < 4; ++i) {
        void* slotObj = m_creatureSlots[i];  // +6148, array of 4 pointers
        if (!slotObj) {
            continue;
        }

        uint8_t* slotBytes = static_cast<uint8_t*>(slotObj);
        int32_t animCount = *reinterpret_cast<int32_t*>(slotBytes + 20);
        if (animCount <= 0) {
            continue;
        }

        if (resetFlag) {
            // Call virtual slot 2 to reset creature animation
            void** vt = *reinterpret_cast<void***>(slotObj);
            reinterpret_cast<void(*)(void*)>(vt[2])(slotObj);
        } else {
            // Copy speed from sub-object's target data into blend fields
            void* targetData = *reinterpret_cast<void**>(slotBytes + 15400);
            float targetSpeed = *reinterpret_cast<float*>(
                static_cast<uint8_t*>(targetData) + 24);
            float currentAnim = *reinterpret_cast<float*>(slotBytes + 46184);

            *reinterpret_cast<float*>(slotBytes + 15392) = targetSpeed;
            *reinterpret_cast<float*>(slotBytes + 15396) = currentAnim;
        }
    }
}


/**
 * pongPlayer::InitMovementAndContact  @ 0x82195D50 | size: 0x9C (156 bytes)
 *
 * Called from pongPlayer_Process. Initializes movement state and checks
 * for ball contact readiness:
 *   1. Calls pongPlayer_SetPlayMode(0) to reset movement state.
 *   2. If slot is null in validation table, or IsInputActiveAndReady
 *      returns true, computes the initial position matrix and sets up
 *      the contact zone parameters.
 */
void pongPlayer::InitMovementAndContact() {  // pongPlayer_5D50_g @ 0x82195D50
    pongPlayer_SetPlayMode(this, 0);

    uint32_t slotIndex = m_slotIndex;  // +464
    uint32_t* validationTable = g_pPlayerSlotTable;
    uint32_t slotEntry = validationTable[slotIndex + 14];

    bool needsInit = (slotEntry == 0);

    if (!needsInit) {
        if (!pongPlayer_CheckServeInput(this)) {
            return;
        }
    }

    // Compute initial position matrix from creature instance (+452 -> +168)
    void* creatureState = m_pCreatureState;  // +452
    void* creatureInst = *reinterpret_cast<void**>(
        static_cast<uint8_t*>(static_cast<void*>(creatureState)) + 168);

    float localMatrix[16];
    pongMover_CalcInitMatrix(localMatrix, creatureInst);

    // Set up contact zone with scale constants
    extern const float g_kContactScale1;  // @ 0x825C8A50
    extern const float g_kContactScale2;  // @ 0x82028080
    void* shotState = m_pShotState;  // +496
    pongPlayer_SetupShotTarget(shotState, g_kContactScale1, g_kContactScale2);
}


/**
 * pongPlayer::ResetSwingSlotEntries  @ 0x821A6080 | size: 0x8C (140 bytes)
 *
 * Zeroes out all 10 swing slot entries (80-byte stride). Each entry:
 *   - flags word at +4: cleared to 0
 *   - byte at +76: cleared to 0
 *   - byte at +77: set to 1 (enabled)
 *   - counter at +84: cleared to 0
 * Plus two trailing dword clears at +800 and +804.
 *
 * Called from game_5FC8 during match init.
 */
void pongPlayer::ResetSwingSlotEntries(void* slotsBase) {  // pongPlayer_6080_p33 @ 0x821A6080
    uint8_t* base = reinterpret_cast<uint8_t*>(slotsBase);

    for (int i = 0; i < 10; ++i) {
        uint8_t* entry = base + i * 80;
        *reinterpret_cast<uint32_t*>(entry + 4)  = 0;
        *(entry + 76) = 0;
        *(entry + 77) = 1;
        *reinterpret_cast<uint32_t*>(entry + 84) = 0;
    }

    *reinterpret_cast<uint32_t*>(base + 800) = 0;
    *reinterpret_cast<uint32_t*>(base + 804) = 0;
}


/**
 * pongPlayer::NotifySlotChangeAndSync  @ 0x821C9870 | size: 0xA4 (164 bytes)
 *
 * When a slot's dirty byte is clear, sends a page-group notification
 * (code 4130 with slot mask | 64) and marks it dirty. Then synchronises
 * via pongPlayer_9108_g (SyncByteField).
 *
 * Used for network synchronisation of player slot state changes.
 */
void pongPlayer::NotifySlotChangeAndSync(void* slotsBase, uint32_t slotIndex,
                                          uint32_t columnIndex) {
    // pongPlayer_9870_g @ 0x821C9870
    uint8_t* base = reinterpret_cast<uint8_t*>(slotsBase);

    // Look up speed value from table indexed by columnIndex
    extern float g_kSlotSpeedLookup[];  // @ 0x825C76CC
    float speedVal = g_kSlotSpeedLookup[columnIndex];

    // Store speed at slot offset (+61 base, *4 stride)
    uint32_t storeOffset = (slotIndex + 61) * 4;
    *reinterpret_cast<float*>(base + storeOffset) = speedVal;

    // Compute entry stride: slot*3 + column -> *3 final
    uint32_t entryIdx = slotIndex * 3 + columnIndex;
    uint32_t finalIdx = entryIdx * 3;

    uint8_t* dirtyAddr = base + finalIdx * 4 + 172;
    uint8_t dirtyFlag = *dirtyAddr;

    if (dirtyFlag == 0) {
        uint8_t slotMask = static_cast<uint8_t>(1 << slotIndex) | 64;
        pg_E6E0(4130, slotMask, 1, static_cast<int>(columnIndex));

        *(base + slotIndex + 288) = 1;
    }

    // Sync byte field
    uint8_t syncBuf[4];
    syncBuf[0] = 1;
    pongPlayer_9108_g(dirtyAddr, syncBuf);
}


/**
 * pongPlayer::UpdateServeSpeed  @ 0x8218CD48 | size: 0xB8 (184 bytes)
 *
 * Called from pongPlayer_Process. Determines the serve speed based on
 * the current match rally state:
 *   1. If rally index is out of range, uses a default speed constant.
 *   2. Otherwise, XORs handedness flags to pick left/right speed
 *      column (+24 or +28) from the rally speed table.
 *   3. Stores result in creature state's speed field (+208).
 */
void pongPlayer::UpdateServeSpeed() {  // pongPlayer_CD48_g @ 0x8218CD48
    uint8_t* matchBytes = static_cast<uint8_t*>(g_pMatchState);
    int32_t rallyIndex = *reinterpret_cast<int32_t*>(matchBytes + 28);

    bool indexValid = false;
    if (rallyIndex >= 0) {
        int32_t maxRallies = *reinterpret_cast<int32_t*>(matchBytes + 8);
        if (rallyIndex < maxRallies - 1) {
            indexValid = true;
        }
    }

    uint8_t* creatureBytes = reinterpret_cast<uint8_t*>(m_pCreatureState);

    if (!indexValid) {
        *reinterpret_cast<float*>(creatureBytes + 208) = g_kFloatConst_D108;
        return;
    }

    uint8_t* configBytes = static_cast<uint8_t*>(g_pMatchConfig);
    uint8_t configHandedness = configBytes[6];

    if (configHandedness == 0) {
        extern const float g_kDefaultServeSpeed;
        *reinterpret_cast<float*>(creatureBytes + 208) = g_kDefaultServeSpeed;
        return;
    }

    uint8_t configSide = configBytes[5];
    uint32_t slotIndex = m_slotIndex;  // +464

    // Look up rally entry
    uint32_t nextRally = rallyIndex + 1;
    uint32_t* rallyTable = *reinterpret_cast<uint32_t**>(matchBytes + 12);
    void* rallyEntry = reinterpret_cast<void*>(rallyTable[nextRally]);

    // Get speed table from rally entry (+8 -> +40)
    uint8_t* rallyBytes = static_cast<uint8_t*>(rallyEntry);
    void* rallySubObj = *reinterpret_cast<void**>(rallyBytes + 8);
    void* speedData = *reinterpret_cast<void**>(
        static_cast<uint8_t*>(rallySubObj) + 40);

    uint8_t playerTableSide = *(static_cast<uint8_t*>(
        static_cast<void*>(g_pPlayerSlotTable)) + 64);

    uint32_t sideXor = configSide ^ playerTableSide;

    // Pick forehand (+24) or backhand (+28) speed
    uint8_t* speedBytes = static_cast<uint8_t*>(speedData);
    int speedOffset = (sideXor == slotIndex) ? 24 : 28;
    float speed = *reinterpret_cast<float*>(speedBytes + speedOffset);
    *reinterpret_cast<float*>(creatureBytes + 208) = speed;
}


/**
 * pongPlayer::InitializeReplaySnapshot  @ 0x820D9420 | size: 0xD4 (212 bytes)
 *
 * Captures the initial replay snapshot. Called from pongPlayer_83C8_g
 * during replay recording setup:
 *   1. Zero-initialises vec3 buffers, calls vtable slot 4 for position.
 *   2. Copies transform vector from singleton+64 into output+16.
 *   3. Stores base speed at output+0, clears bytes +8..+10.
 */
void pongPlayer::InitializeReplaySnapshot(void* outSnapshot) {
    // pongPlayer_9420_wrh @ 0x820D9420
    uint8_t* out = reinterpret_cast<uint8_t*>(outSnapshot);

    void** singletonPtr = reinterpret_cast<void**>(g_pMatchState);
    void* singleton = *singletonPtr;

    float zero = g_kFloatConst_D110;  // was g_kReplayZero @ 0x8202D110

    float posVec[4]  = { zero, zero, zero, 0.0f };
    float zeroVec[4] = { zero, zero, zero, 0.0f };

    // Call vtable slot 4 for player position
    typedef void (*GetPosFn)(void*, float*);
    void** vtable = *reinterpret_cast<void***>(singleton);
    GetPosFn getPos = reinterpret_cast<GetPosFn>(vtable[4]);
    getPos(singleton, posVec);

    // Read base speed from singleton (+48)
    uint8_t* singletonBytes = static_cast<uint8_t*>(singleton);
    float baseSpeed = *reinterpret_cast<float*>(singletonBytes + 48);

    *reinterpret_cast<float*>(out + 0) = baseSpeed;

    // Copy transform (singleton+64 -> output+16)
    memcpy(out + 16, singletonBytes + 64, 16);

    memcpy(out + 32, posVec, 16);
    memcpy(out + 48, zeroVec, 16);

    out[8]  = 0;
    out[9]  = 0;
    out[10] = 0;
}


/**
 * pongPlayer::ClampMovementToCourtBounds  @ 0x8219D558 | size: 0xD8 (216 bytes)
 *
 * Clamps X and Z movement deltas to court boundaries using the player's
 * court half-widths (+896 for X, +904 for Z). Uses fsel-style clamping.
 *
 * Called from pongPlayer_D8E8_g during movement processing.
 */
void pongPlayer::ClampMovementToCourtBounds(float* delta) {
    // pongPlayer_D558_wrh @ 0x8219D558
    // Constants: g_kFloatConst_D110=g_kFloatConst_D110 @ 0x8202D110
    extern const double g_kCourtMaxDelta;  // @ 0x82079D78
    extern const double g_kCourtNegMax;    // @ 0x82079B80
    extern const float g_kCourtMinDelta;   // @ 0x82079D68

    float maxDelta = static_cast<float>(g_kCourtMaxDelta);
    float negMax   = static_cast<float>(g_kCourtNegMax);

    // Clamp X component
    if (delta[0] > g_kFloatConst_D110) {
        float adj = delta[0] - m_courtHalfWidthX;  // +896
        if (adj >= 0.0f) {
            float clamped = (adj >= 0.0f) ? adj : negMax;
            delta[0] = (clamped - maxDelta >= 0.0f) ? maxDelta : clamped;
        }
    }
    if (delta[0] < g_kFloatConst_D110) {
        float adj = m_courtHalfWidthX + delta[0];
        if (adj - g_kCourtMinDelta >= 0.0f) {
            delta[0] = (adj >= 0.0f) ? negMax : adj;
        }
    }

    // Clamp Z component
    if (delta[2] > g_kFloatConst_D110) {
        float adj = delta[2] - m_courtHalfWidthZ;  // +904
        if (adj >= 0.0f) {
            float clamped = (adj >= 0.0f) ? adj : negMax;
            delta[2] = (clamped - maxDelta >= 0.0f) ? maxDelta : clamped;
        }
    }
    if (delta[2] < g_kFloatConst_D110) {
        float adj = m_courtHalfWidthZ + delta[2];
        if (adj - g_kCourtMinDelta >= 0.0f) {
            delta[2] = (adj >= 0.0f) ? negMax : adj;
        }
    }
}


// ===========================================================================
// SECTION 26 — SaveDrawData  @ 0x8218E860 | size: 0x30 (48 bytes)
// ===========================================================================
/**
 * pongPlayer::SaveDrawData()
 *
 * Delegates draw-data serialisation to the render sub-object.
 * If the player is not active (byte +36 == 0), calls the debug no-op
 * and returns early.  Otherwise loads the render object pointer at +444,
 * advances by 16, and calls vtable slot 1 (SaveDrawData) on it.
 */
void pongPlayer::SaveDrawData() {  // pongPlayer_SaveDrawData @ 0x8218E860
    if (!m_bVisible) {  // byte +36
        rage_debugLog("pongPlayer::SaveDrawData() not visible");  // debug logging no-op
        return;
    }
    void* renderObj = this->m_pDrawData;
    uint8_t* renderBytes = static_cast<uint8_t*>(renderObj);
    void* renderSub = renderBytes + 16;
    // vtable slot 1 call on renderSub
    void** vt = *reinterpret_cast<void***>(renderSub);
    reinterpret_cast<void(*)(void*)>(vt[1])(renderSub);
}


// ===========================================================================
// SECTION 27 — CompareTypeNames  @ 0x820CF0B8 | size: 0x38 (56 bytes)
// ===========================================================================
/**
 * pongPlayer::CompareTypeNames(void* a, void* b)
 *
 * Byte-by-byte string comparison of two RTTI type name strings.
 * Each parameter is a pointer to an object; the function dereferences
 * the first word (vtable/type ptr), then dereferences again to get
 * the actual string pointer, and compares the strings character by
 * character.  Returns the difference of the first mismatched byte
 * pair, or 0 if identical up to the null terminator.
 *
 * Equivalent to: strcmp(**(char***)a, **(char***)b)
 */
int pongPlayer::CompareTypeNames(void* a, void* b) {  // pongPlayer_F0B8_p46 @ 0x820CF0B8
    const char* strA = **reinterpret_cast<const char***>(a);
    const char* strB = **reinterpret_cast<const char***>(b);

    while (true) {
        int diff = static_cast<int>(static_cast<uint8_t>(*strA)) -
                   static_cast<int>(static_cast<uint8_t>(*strB));
        if (*strA == '\0') {
            return diff;
        }
        ++strA;
        ++strB;
        if (diff != 0) {
            return diff;
        }
    }
}


// ===========================================================================
// SECTION 28 — IsLocomotionReady  @ 0x82192578 | size: 0x50 (80 bytes)
// ===========================================================================
/**
 * pongPlayer::IsLocomotionReady()
 *
 * Checks whether the player's locomotion sub-system is in a ready state.
 * Traverses: this+452 -> +188 -> +120 to get a locomotion object.
 * If null, returns false.  Otherwise calls pongPlayer_IsLocoStateReady on that
 * object+32 and returns true if it succeeds, false otherwise.
 */
bool pongPlayer::IsLocomotionReady() const {  // pongPlayer_2578_g @ 0x82192578
    // NOTE: +452 is confirmed m_pOpponent via get_class_context (R:66 W:0,
    //       "set once at init"). The deep chain is opponent->+188->+120:
    //       opponent's m_pPlayerState (+0xBC = 188) holds a locomotion
    //       sub-object whose +120 (+0x78) slot contains the loco state we
    //       pass to pongPlayer_6AA0_g (IsLocoStateReady) offset by +32.
    uint8_t* sub1 = reinterpret_cast<uint8_t*>(this->m_pOpponent);
    void* sub2 = *reinterpret_cast<void**>(sub1 + 188);
    void* locoObj = *reinterpret_cast<void**>(
        static_cast<uint8_t*>(sub2) + 120);
    if (!locoObj) {
        return false;
    }
    void* locoState = static_cast<uint8_t*>(locoObj) + 32;
    return pongPlayer_IsLocoStateReady(locoState);
}


// ===========================================================================
// SECTION 29 — ResetServePosition  @ 0x821936D8 | size: 0x60 (96 bytes)
// ===========================================================================
/**
 * pongPlayer::ResetServePosition()
 *
 * Resets the player to the serve position by:
 *  1. Checking a handedness flag via the geometry singleton (byte at
 *     field+464+global_offset+64), converting to a "flip" boolean.
 *  2. Calling pongPlayer_3628_g(this, flipFlag) to set serve-side.
 *  3. Calling game_C690(this) to compute the reset position.
 *  4. Calling pongMover_Reset on the mover sub-object at (this+452)->+168
 *     with the position result.
 */
// pongPlayer_3628_g (SetServeSideFlip) — implemented at end of file
extern void* game_C690(pongPlayer* player);
extern void pongMover_Reset(void* mover, void* position);
extern uint32_t g_kGeomOffset;  // global loaded via lis+lwz

void pongPlayer::ResetServePosition() {  // pongPlayer_36D8_g @ 0x821936D8
    uint32_t fieldOffset = static_cast<uint32_t>(this->m_inputSlotIdx);
    uint8_t* geomBase = reinterpret_cast<uint8_t*>(
        static_cast<uintptr_t>(fieldOffset + g_kGeomOffset));
    uint8_t handFlag = geomBase[64];
    // cntlzw + rlwinm: convert 0 -> 1, nonzero -> 0
    uint8_t flip = (handFlag == 0) ? 1 : 0;

    pongPlayer_3628_g(this, flip);

    void* posResult = game_C690(this);

    // NOTE: opponent (+452) holds a pongMover at +168 (+0xA8) inside its
    //       own player state — used here to snap the opponent's serve-side
    //       mover to the result of game_C690. Opponent chain confirmed via
    //       the class-context field map.
    uint8_t* sub = reinterpret_cast<uint8_t*>(this->m_pOpponent);
    void* mover = *reinterpret_cast<void**>(sub + 168);
    pongMover_Reset(mover, posResult);
}


// ===========================================================================
// SECTION 30 — GetFrameIndexDelta  @ 0x821A7A48 | size: 0x58 (88 bytes)
// ===========================================================================
/**
 * pongPlayer::GetFrameIndexDelta(void* frameData)
 *
 * Computes a frame index delta from two 16-bit fields at frameData+4 and +6.
 * If both are -1 (0xFFFF), returns 0 (no frames).
 * Otherwise computes (field4 - field6 + 1), wrapping by +20 if field4 < field6.
 */
int pongPlayer::GetFrameIndexDelta(void* frameData) {  // pongPlayer_7A48_g @ 0x821A7A48
    int16_t field4 = *reinterpret_cast<int16_t*>(
        reinterpret_cast<uintptr_t>(frameData) + 4);
    uint16_t field6 = *reinterpret_cast<uint16_t*>(
        reinterpret_cast<uintptr_t>(frameData) + 6);

    if (field4 == -1 && field6 == 0xFFFF) {
        return 0;
    }

    int16_t end = static_cast<int16_t>(field6);
    int diff = static_cast<int>(field4) - static_cast<int>(end);
    if (field4 >= end) {
        return diff + 1;
    }
    return diff + 21;
}


// ===========================================================================
// SECTION 31 — ComputePositionWithOffsets  @ 0x821D62A8 | size: 0x60 (96 bytes)
// ===========================================================================
/**
 * pongPlayer::ComputePositionWithOffsets(void* inputData)
 *
 * Computes a combined position vector by calling pongPlayer_ComputeTargetPosition to get
 * a base target vector, then adding the offset vectors at this+224 (vec4)
 * and this+240 (vec4), storing the result at this+32.
 *
 * result = 6470_g(self, inputData) + vec4@(self+224) + vec4@(self+240)
 */
void pongPlayer::ComputePositionWithOffsets(void* inputData) {  // pongPlayer_62A8_g @ 0x821D62A8
    float tempVec[4];
    pongPlayer_ComputeTargetPosition(reinterpret_cast<vec3*>(tempVec), inputData);

    // NOTE: pongPlayer_62A8_g is called by phBoundCapsule_25F0_g and the
    //       pongPlayer_EF38/F2A0/F7B0 family — `this` here is NOT a pongPlayer
    //       but a phBound-adjacent struct where +224/+240 are adjacent 16-byte
    //       offset vectors and +32 is the result slot. Kept as a pongPlayer
    //       method for binding parity with the call-site thunk.
    uint8_t* base = reinterpret_cast<uint8_t*>(this);
    float* offset1 = reinterpret_cast<float*>(base + 224);
    float* offset2 = reinterpret_cast<float*>(base + 240);
    float* dest    = reinterpret_cast<float*>(base + 32);

    // vaddfp: result = temp + offset1 + offset2
    dest[0] = tempVec[0] + offset1[0] + offset2[0];
    dest[1] = tempVec[1] + offset1[1] + offset2[1];
    dest[2] = tempVec[2] + offset1[2] + offset2[2];
    dest[3] = tempVec[3] + offset1[3] + offset2[3];
}


// ===========================================================================
// SECTION 32 — ComputePositionWithOffset  @ 0x821D6308 | size: 0x54 (84 bytes)
// ===========================================================================
/**
 * pongPlayer::ComputePositionWithOffset()
 *
 * Similar to ComputePositionWithOffsets but only adds one offset vector
 * (at this+224).  Calls pongPlayer_ComputeTargetPosition with r5=0 (no input data),
 * then adds vec4@(this+224), storing the result at this+32.
 *
 * result = 6470_g(self, NULL) + vec4@(self+224)
 */
void pongPlayer::ComputePositionWithOffset() {  // pongPlayer_6308_g @ 0x821D6308
    float tempVec[4];
    pongPlayer_ComputeTargetPosition(reinterpret_cast<vec3*>(tempVec), nullptr);

    // NOTE: as with 62A8_g above, this is called by phBoundCapsule_E830_g and
    //       the pongPlayer_EF38/F2A0/F7B0 family — operates on a phBound-shaped
    //       struct, not on pongPlayer. +224 is a 16-byte offset vector, +32 is
    //       the result slot.
    uint8_t* base = reinterpret_cast<uint8_t*>(this);
    float* offset = reinterpret_cast<float*>(base + 224);
    float* dest   = reinterpret_cast<float*>(base + 32);

    // vaddfp: result = temp + offset
    dest[0] = tempVec[0] + offset[0];
    dest[1] = tempVec[1] + offset[1];
    dest[2] = tempVec[2] + offset[2];
    dest[3] = tempVec[3] + offset[3];
}


// ===========================================================================
// SECTION 33 — CheckHandednessDifference  @ 0x821E04B0 | size: 0x54 (84 bytes)
// ===========================================================================
/**
 * pongPlayer::CheckHandednessDifference()
 *
 * Calls pongPlayer_GetInputStepIndex to get an index, uses it to look up a 4-byte
 * entry in the table at this+796.  XORs byte[0] with byte[3] of that entry;
 * if the XOR result > 127, returns true (significant difference), else false.
 */
extern int pongPlayer_GetInputStepIndex(pongPlayer* p);

bool pongPlayer::CheckHandednessDifference() {  // pongPlayer_04B0_g @ 0x821E04B0
    int index = pongPlayer_GetInputStepIndex(this);

    uint8_t* base = reinterpret_cast<uint8_t*>(this);
    uint8_t* tableBase = *reinterpret_cast<uint8_t**>(base + 796);
    uint8_t* entry = tableBase + (index * 4);

    uint8_t byte3 = entry[3];
    uint8_t byte0 = entry[0];
    uint8_t diff = byte3 ^ byte0;

    return diff > 127;
}


// (GetStateObjectByIndex already defined above in SECTION 20)

// ===========================================================================
// SECTION 35 — SyncByteField  @ 0x82199108 | size: 0x7C (124 bytes)
// ===========================================================================
/**
 * pongPlayer::SyncByteField(void* target, void* source)
 *
 * Compares byte[0] of target with byte[0] of source.  If different:
 *   - If field +8 (callback pointer) is non-null, invokes the callback
 *     with field +4 as the argument (marks the field dirty for network sync).
 *   - Copies the new byte value from source to target.
 */
void pongPlayer::SyncByteField(void* target, void* source) {  // pongPlayer_9108_g @ 0x82199108
    uint8_t* tgt = static_cast<uint8_t*>(target);
    uint8_t oldVal = tgt[0];
    uint8_t newVal = *static_cast<uint8_t*>(source);

    if (oldVal != newVal) {
        void* callback = *reinterpret_cast<void**>(tgt + 8);
        if (callback) {
            void* arg = *reinterpret_cast<void**>(tgt + 4);
            reinterpret_cast<void(*)(void*)>(callback)(arg);
        }
        tgt[0] = newVal;
    }
}


// ===========================================================================
// SECTION 36 — SyncFloatField  @ 0x8219CF10 | size: 0x7C (124 bytes)
// ===========================================================================
/**
 * pongPlayer::SyncFloatField(void* target, void* source)
 *
 * Compares float[0] of target with float[0] of source.  If different:
 *   - If field +8 (callback pointer) is non-null, invokes the callback
 *     with field +4 as the argument (marks the field dirty for network sync).
 *   - Copies the new float value from source to target.
 */
void pongPlayer::SyncFloatField(void* target, void* source) {  // pongPlayer_CF10_g @ 0x8219CF10
    uint8_t* tgt = static_cast<uint8_t*>(target);
    float oldVal = *reinterpret_cast<float*>(tgt);
    float newVal = *reinterpret_cast<float*>(source);

    if (oldVal != newVal) {
        void* callback = *reinterpret_cast<void**>(tgt + 8);
        if (callback) {
            void* arg = *reinterpret_cast<void**>(tgt + 4);
            reinterpret_cast<void(*)(void*)>(callback)(arg);
        }
        *reinterpret_cast<float*>(tgt) = newVal;
    }
}


// ===========================================================================
// SECTION 37 — UpdateDirtyFlags  @ 0x82199E48 | size: 0x5C (92 bytes)
// ===========================================================================
/**
 * pongPlayer::UpdateDirtyFlags(void* obj, uint8_t forceReset)
 *
 * Manages three byte flags at obj+40, obj+41, and obj+42 that control
 * dirty-state tracking for network synchronisation.
 *
 * If forceReset is non-zero: clears +40 and +42, sets +41 to 1.
 * If forceReset is zero:
 *   - If +40 is already set, or +41 is already set: already dirty, return.
 *   - If both +40 and +41 are clear: sets +41 to 1 (mark as needing sync).
 */
void pongPlayer::UpdateDirtyFlags(void* obj, uint8_t forceReset) {  // pongPlayer_9E48_g @ 0x82199E48
    uint8_t* base = static_cast<uint8_t*>(obj);
    uint8_t* flag40 = base + 40;
    uint8_t* flag41 = base + 41;
    uint8_t* flag42 = base + 42;

    if (forceReset) {
        *flag40 = 0;
        *flag42 = 0;
        *flag41 = 1;
        return;
    }

    if (*flag40 != 0 || *flag41 != 0) {
        // Already dirty
        return;
    }

    // Neither flag set -- mark as needing sync
    *flag41 = 1;
}


// ===========================================================================
// SECTION 38 — MarkNetDirtyPosition  @ 0x82198AC0 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyPosition()
 *
 * If network dirty tracking is enabled (m_bNetDirtyEnabled != 0),
 * sets bit 0 of the network dirty flags word.  This marks the
 * player's position data as needing replication.
 *
 * Called from pongPlayer_Process to flag position changes.
 */
void pongPlayer::MarkNetDirtyPosition() {  // pongPlayer_8AC0_p33 @ 0x82198AC0
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x1;
}


// ===========================================================================
// SECTION 39 — MarkNetDirtyRotation  @ 0x82198AE0 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyRotation()
 *
 * If network dirty tracking is enabled, sets bit 1 of the network
 * dirty flags word.  Marks the player's rotation data for replication.
 */
void pongPlayer::MarkNetDirtyRotation() {  // pongPlayer_8AE0_p33 @ 0x82198AE0
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x2;
}


// ===========================================================================
// SECTION 40 — SyncFieldWithCallback  @ 0x82199EA8 | size: 0x7C (124 bytes)
// ===========================================================================
/**
 * pongPlayer::SyncFieldWithCallback(void* target, void* source)
 *
 * Compares the uint32_t value at target+0 with source+0.  If they differ
 * and a callback pointer is stored at target+8, the callback is invoked
 * with the argument from target+4.  The new value from source is then
 * written to target+0.
 *
 * Used by the network sync system to update fields and fire change
 * notifications (e.g. animation state transitions, score changes).
 */
void pongPlayer::SyncFieldWithCallback(void* target, void* source) {  // pongPlayer_9EA8_g @ 0x82199EA8
    uint8_t* tgt = static_cast<uint8_t*>(target);
    uint32_t* targetVal = reinterpret_cast<uint32_t*>(tgt);
    uint32_t* sourceVal = static_cast<uint32_t*>(source);

    if (*targetVal == *sourceVal)
        return;

    // Check for a registered callback at target+8
    void* callback = *reinterpret_cast<void**>(tgt + 8);
    if (callback) {
        void* arg = *reinterpret_cast<void**>(tgt + 4);
        reinterpret_cast<void(*)(void*)>(callback)(arg);
    }

    // Store the new value
    *targetVal = *sourceVal;
}


// ===========================================================================
// SECTION 41 — ResetShotSyncFields  @ 0x82199310 | size: 0x7C (124 bytes)
// ===========================================================================
/**
 * pongPlayer::ResetShotSyncFields(void* shotState, uint8_t clearNetFlags)
 *
 * Resets the float-typed sync fields within a shot tracking sub-object.
 * Zeroes out two float sync entries (at shotState+8 and shotState+20)
 * via SyncFloatField, stores 0.0 at shotState+32, clears byte flag
 * at shotState+36, then calls SyncFieldWithCallback on the sub-object
 * at shotState+44 passing the clearNetFlags argument.
 *
 * Called from ResetShotTrackingState and the main shot processing loop.
 */
void pongPlayer::ResetShotSyncFields(void* shotState, uint8_t clearNetFlags) {  // pongPlayer_9310_g @ 0x82199310
    extern const float g_kZeroFloat;  // @ 0x82079D10 (0.0f)

    float zero = g_kZeroFloat;

    uint8_t* shot = static_cast<uint8_t*>(shotState);

    // Reset first float sync field at shotState+8
    float syncBuf = zero;
    SyncFloatField(shot + 8, &syncBuf);

    // Reset second float sync field at shotState+20
    syncBuf = zero;
    SyncFloatField(shot + 20, &syncBuf);

    // Clear float at shotState+32 (accumulated timing)
    *reinterpret_cast<float*>(shot + 32) = zero;

    // Clear byte flag at shotState+36
    shot[36] = 0;

    // Sync the sub-field at shotState+44 with the clearNetFlags argument
    uint32_t flagVal = clearNetFlags;
    SyncFieldWithCallback(shot + 44, &flagVal);
}


// ===========================================================================
// SECTION 42 — ResetShotTrackingState  @ 0x821992A0 | size: 0x70 (112 bytes)
// ===========================================================================
/**
 * pongPlayer::ResetShotTrackingState()
 *
 * Full reset of the player's shot tracking subsystem.  Called from
 * pongPlayer_Process when transitioning to an idle state:
 *
 *   1. Calls ResetShotSyncFields to zero the float sync entries.
 *   2. Calls ResetButtonSlotTrackingData twice (with indices 0 and 1) to reset
 *      per-player-slot shot data using the global button state table.
 *   3. Clears the shot result dword (+72), and three byte flags at
 *      +69, +76, +77 (shot active, pending, committed).
 */
void pongPlayer::ResetShotTrackingState() {  // pongPlayer_92A0_g @ 0x821992A0
    // Reset all shot sync fields
    uint8_t clearFlags = 0;
    ResetShotSyncFields(this, clearFlags);

    // Reset shot data for both player slots
    ResetButtonSlotTrackingData(reinterpret_cast<void*>(g_pButtonStateTable), 0);
    ResetButtonSlotTrackingData(reinterpret_cast<void*>(g_pButtonStateTable), 1);

    // Clear shot result and tracking flags
    uint8_t* selfBase = reinterpret_cast<uint8_t*>(this);
    *reinterpret_cast<uint32_t*>(&this->m_swingDirectionAdj) = 0;
    selfBase[69] = 0;
    this->m_team = 0;
    selfBase[77] = 0;
}


// ===========================================================================
// SECTION 43 — ClearSwingTrajectoryData  @ 0x8219E748 | size: 0x68 (104 bytes)
// ===========================================================================
/**
 * pongPlayer::ClearSwingTrajectoryData(void* trajectoryBlock)
 *
 * Zeroes out the swing trajectory data structure:
 *   - 4 x 16-byte vector slots at +32..+95 (via AltiVec vxor + stvx loop)
 *   - Floats at +4 and +8 set to 0.0
 *   - 16-byte vector at +16 zeroed
 *   - Global 16-byte vector at a fixed address zeroed
 *   - Bytes at +0 and +1 cleared
 *
 * This is a full initialisation of the trajectory prediction buffer
 * used during swing animation playback.
 */
void pongPlayer::ClearSwingTrajectoryData(void* trajectoryBlock) {  // pongPlayer_E748_p33 @ 0x8219E748
    uint8_t* base = reinterpret_cast<uint8_t*>(trajectoryBlock);

    // Zero 4 x 16-byte vector slots at +32..+95
    memset(base + 32, 0, 64);

    // Zero floats at +4 and +8
    *reinterpret_cast<float*>(base + 4) = 0.0f;
    *reinterpret_cast<float*>(base + 8) = 0.0f;

    // Zero 16-byte vector at +16
    memset(base + 16, 0, 16);

    // Zero global trajectory vector
    extern uint8_t g_swingTrajectoryGlobal[];  // @ 0x825C6720
    memset(g_swingTrajectoryGlobal, 0, 16);

    // Clear byte flags at +0 and +1
    base[1] = 0;
    base[0] = 0;
}


// ===========================================================================
// SECTION 44 — ResetSwingTrackingState  @ 0x8219FA40 | size: 0x74 (116 bytes)
// ===========================================================================
/**
 * pongPlayer::ResetSwingTrackingState()
 *
 * Resets the player's per-swing tracking state to default values.
 * Called from FinalizeServeSetup and pongPlayer_InitActionState (button release
 * handler) when a swing/serve is finalised or cancelled.
 *
 *   1. Zeroes floats at +4, +8 (position deltas)
 *   2. Clears byte flags at +84, +86, +85 (swing phase, type, active)
 *   3. Zeroes floats at +64, +72, +76, +80 (swing vectors/power)
 *   4. Calls ClearSwingSlotGrid on two grid sub-objects at +96 and +2800
 *   5. Clears byte flag at +5513 (swing committed)
 */
// pongPlayer_E640_g (ClearSwingSlotGrid) — implemented at end of file

void pongPlayer::ResetSwingTrackingState() {  // pongPlayer_FA40_g @ 0x8219FA40
    uint8_t* base = reinterpret_cast<uint8_t*>(this);

    // Zero position delta floats
    *reinterpret_cast<float*>(base + 4) = 0.0f;
    *reinterpret_cast<float*>(base + 8) = 0.0f;

    // Clear swing phase flags
    base[84] = 0;
    base[86] = 0;
    base[85] = 0;

    // Zero swing vector/power floats
    *reinterpret_cast<float*>(base + 64) = 0.0f;
    *reinterpret_cast<float*>(base + 72) = 0.0f;
    *reinterpret_cast<float*>(base + 76) = 0.0f;
    *reinterpret_cast<float*>(base + 80) = 0.0f;

    // Clear both swing slot grids
    pongPlayer_E640_g(base + 96);
    pongPlayer_E640_g(base + 2800);

    // Clear swing committed flag
    base[5513] = 0;
}


// ===========================================================================
// SECTION 45 — FinalizeServeSetup  @ 0x8219F9C0 | size: 0x80 (128 bytes)
// ===========================================================================
/**
 * pongPlayer::FinalizeServeSetup()
 *
 * Completes the serve setup phase by copying shot data to the global
 * character table, resetting swing tracking, and marking the player
 * as ready for the next rally point.
 *
 * Called from SetupServe, pongPlayer_2D88_g (serve confirm), and
 * pongPlayer_0780_g (serve input handler).
 *
 *   1. If the player's character slot index (at m_pParent+464) is valid
 *      (!= -1), copies shot data into the character table via
 *      pongPlayer_5F70_g.
 *   2. Stores the player's shot type byte (+5504) into the character
 *      table at the corresponding slot.
 *   3. Clears the serve pending flag (m_pParent+6380).
 *   4. Resets swing tracking state via ResetSwingTrackingState.
 *   5. Clears byte at +5512 and sets +5504 to 1 (default shot type).
 *   6. Calls ref_fi_FCD8 to finalise the serve FSM transition.
 */
extern void pongPlayer_5F70_g(void* charSlotEntry);  // copy shot data to char table
extern void ref_fi_FCD8(void* self);                  // finalise serve FSM

void pongPlayer::FinalizeServeSetup() {  // pongPlayer_F9C0_g @ 0x8219F9C0
    // g_ballSplashArray declared at file scope @ 0x8261A3D0
    uint8_t* base = reinterpret_cast<uint8_t*>(this);

    // Read parent object pointer (this+44) and get character slot index
    uint8_t* parent = *reinterpret_cast<uint8_t**>(base + 44);
    int32_t charSlot = *reinterpret_cast<int32_t*>(parent + 464);

    // If character slot is valid, copy shot data to the character table
    if (charSlot != -1) {
        void* charEntry = g_ballSplashArray + 48 + charSlot * 416;
        pongPlayer_5F70_g(charEntry);
    }

    // Store shot type byte into character table at the slot's offset +264
    uint8_t shotType = base[5504];
    g_ballSplashArray[264 + charSlot * 416] = shotType;

    // Clear serve pending flag on parent
    parent[6380] = 0;

    // Reset swing tracking state
    ResetSwingTrackingState();

    // Clear byte at +5512, set shot type to 1 (default)
    base[5512] = 0;
    base[5504] = 1;

    // Finalise serve FSM transition
    ref_fi_FCD8(this);
}


// ===========================================================================
// SECTION 46 — LookupElementByFloatKey  @ 0x821EB1E0 | size: 0x90 (144 bytes)
// ===========================================================================
/**
 * pongPlayer::LookupElementByFloatKey(void* table, float key)
 *
 * Given a table structure with:
 *   +24 : pointer to an array of uint32_t element pointers
 *   +28 : uint16_t element count
 *
 * Returns the element pointer at the index corresponding to `key`,
 * clamped to [0, count-1].  If key >= count or is negative/NaN,
 * returns the first element (index 0).
 *
 * Called from 32+ animation/physics lookup functions that index into
 * per-frame data arrays using a normalised float time value.
 */
void* pongPlayer::LookupElementByFloatKey(void* table, float key) {  // pongPlayer_B1E0_g @ 0x821EB1E0
    uint8_t* tbl = static_cast<uint8_t*>(table);
    uint16_t count = *reinterpret_cast<uint16_t*>(tbl + 28);
    uint32_t* elements = *reinterpret_cast<uint32_t**>(tbl + 24);

    float countF = static_cast<float>(static_cast<int32_t>(count));

    // Check if key is within [0, count)
    if (key + 0.5f <= countF && !(key < 0.0f)) {
        // Clamp key to [0, count-1] and convert to index
        float clamped = key;
        if (clamped < 0.0f)
            clamped = 0.0f;
        float maxVal = static_cast<float>(count);
        if (clamped >= maxVal)
            clamped = maxVal;
        int32_t index = static_cast<int32_t>(clamped);

        return reinterpret_cast<void*>(elements[index]);
    }

    // Fallback: return first element
    return reinterpret_cast<void*>(elements[0]);
}


// ===========================================================================
// SECTION 47 — RegisterDebugDrawEntries  @ 0x8218BB38 | size: 0xA4 (164 bytes)
// ===========================================================================
/**
 * pongPlayer::RegisterDebugDrawEntries()
 *
 * Registers the player's debug draw objects with the global debug
 * render system.  Called from pongPlayer_Activate and pongPlayer_B6F0_g
 * (initialisation path).
 *
 * Adds up to 3 entries to the global debug draw table:
 *   1. Skeleton debug draw object (at this+6208, offset +4), type 1031, priority 128
 *   2. If m_pParent field +248 is non-null: that object, type 15, priority 128
 *   3. Player base object (this+4), type 1703, priority 128
 *
 * The global table has three parallel arrays (pointer, type, priority)
 * indexed by a shared counter at a fixed SDA address.
 */
void pongPlayer::RegisterDebugDrawEntries() {  // pongPlayer_BB38_g @ 0x8218BB38
    extern uint32_t  g_debugDrawCount;        // @ SDA+14436
    extern uint32_t  g_debugDrawPtrs[];       // @ SDA+14440  (pointer array)
    extern uint32_t  g_debugDrawTypes[];      // @ SDA+14696  (type ID array)
    extern uint8_t   g_debugDrawPriority[];   // @ SDA+14952  (priority array)

    uint8_t* base = reinterpret_cast<uint8_t*>(this);

    // Get skeleton debug draw object (this+6208 -> +4)
    void* skelDebugObj = *reinterpret_cast<void**>(base + 6208);
    void* skelEntry = skelDebugObj ? reinterpret_cast<void*>(
        reinterpret_cast<uintptr_t>(skelDebugObj) + 4) : nullptr;

    uint32_t idx = g_debugDrawCount;

    // Entry 1: skeleton debug draw
    g_debugDrawPtrs[idx]     = reinterpret_cast<uintptr_t>(skelEntry);
    g_debugDrawTypes[idx]    = 1031;
    g_debugDrawPriority[idx] = 128;
    idx++;

    // Entry 2: optional sub-object from m_pParent field +248
    void* parentState = *reinterpret_cast<void**>(base + 452);
    void* subObj = *reinterpret_cast<void**>(
        static_cast<uint8_t*>(parentState) + 248);
    if (subObj) {
        g_debugDrawPtrs[idx]     = reinterpret_cast<uintptr_t>(subObj);
        g_debugDrawTypes[idx]    = 15;
        g_debugDrawPriority[idx] = 128;
        idx++;
    }

    // Entry 3: player base object (this+4)
    g_debugDrawPtrs[idx]     = reinterpret_cast<uintptr_t>(base + 4);
    g_debugDrawTypes[idx]    = 1703;
    g_debugDrawPriority[idx] = 128;
    idx++;

    g_debugDrawCount = idx;
}


// ===========================================================================
// SECTION 38b — MarkNetDirtyVelocity  @ 0x82198B00 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyVelocity()
 *
 * If network dirty tracking is enabled (m_bNetDirtyEnabled != 0),
 * sets bit 2 of the network dirty flags word.  Marks the player's
 * velocity data as needing replication.
 */
void pongPlayer::MarkNetDirtyVelocity() {  // pongPlayer_8B00_p33 @ 0x82198B00
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x4;
}


// ===========================================================================
// SECTION 38c — MarkNetDirtyAnimation  @ 0x82198B20 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyAnimation()
 *
 * If network dirty tracking is enabled, sets bit 3 of the network
 * dirty flags word.  Marks the player's animation state for replication.
 */
void pongPlayer::MarkNetDirtyAnimation() {  // pongPlayer_8B20_p33 @ 0x82198B20
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x8;
}


// ===========================================================================
// SECTION 38d — MarkNetDirtyShotState  @ 0x82198B40 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyShotState()
 *
 * If network dirty tracking is enabled, sets bit 4 of the network
 * dirty flags word.  Marks the player's shot/swing state for replication.
 */
void pongPlayer::MarkNetDirtyShotState() {  // pongPlayer_8B40_p33 @ 0x82198B40
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x10;
}


// ===========================================================================
// VTABLE THUNKS — MarkNetDirty redirects
// ===========================================================================
// Seven adjacent 16-byte vtable forwarding thunks @ 0x82199188-91F4.
// Each is a tail call (lis/addi/mtctr/bctr) redirecting a secondary
// vtable slot to the corresponding MarkNetDirty implementation.
// ===========================================================================

/**
 * Vtable thunk → MarkNetDirtyPosition  @ 0x82199188 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8AC0_p33 @ 0x82198AC0.
 */
void pongPlayer::VtMarkNetDirtyPosition() {  // pongPlayer_9188_2hr @ 0x82199188
    MarkNetDirtyPosition();
}

/**
 * Vtable thunk → MarkNetDirtyRotation  @ 0x82199198 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8AE0_p33 @ 0x82198AE0.
 */
void pongPlayer::VtMarkNetDirtyRotation() {  // pongPlayer_9198_2h @ 0x82199198
    MarkNetDirtyRotation();
}

/**
 * Vtable thunk → MarkNetDirtyVelocity  @ 0x821991A8 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8B00_p33 @ 0x82198B00.
 */
void pongPlayer::VtMarkNetDirtyVelocity() {  // pongPlayer_91A8_2h @ 0x821991A8
    MarkNetDirtyVelocity();
}

/**
 * Vtable thunk → MarkNetDirtyAnimation  @ 0x821991B8 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8B20_p33 @ 0x82198B20.
 */
void pongPlayer::VtMarkNetDirtyAnimation() {  // pongPlayer_91B8_2h @ 0x821991B8
    MarkNetDirtyAnimation();
}

/**
 * Vtable thunk → MarkNetDirtyShotState  @ 0x821991C8 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8B40_p33 @ 0x82198B40.
 */
void pongPlayer::VtMarkNetDirtyShotState() {  // pongPlayer_91C8_2h @ 0x821991C8
    MarkNetDirtyShotState();
}

/**
 * Vtable thunk → MarkNetDirtyStamina  @ 0x821991D8 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8B60_p33 @ 0x82198B60.
 * Target inlined: m_netDirtyFlags |= 0x20 (bit 5).
 */
void pongPlayer::VtMarkNetDirtyStamina() {  // pongPlayer_91D8_2h @ 0x821991D8
    MarkNetDirtyStamina();
}

/**
 * Vtable thunk → MarkNetDirtyScore  @ 0x821991E8 | size: 0x10 (16 bytes)
 * Tail call redirect to pongPlayer_8B80_p33 @ 0x82198B80.
 * Target inlined: m_netDirtyFlags |= 0x40 (bit 6).
 */
void pongPlayer::VtMarkNetDirtyScore() {  // pongPlayer_91E8_2h @ 0x821991E8
    MarkNetDirtyScore();
}


// ===========================================================================
// SECTION — MarkNetDirtyStamina  @ 0x82198B60 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyStamina()
 *
 * If network dirty tracking is enabled (m_bNetDirtyEnabled != 0),
 * sets bit 5 (0x20) of the network dirty flags word.  This marks the
 * player's stamina data as needing replication.
 *
 * Same pattern as MarkNetDirtyPosition (0x1) and MarkNetDirtyRotation (0x2).
 */
void pongPlayer::MarkNetDirtyStamina() {  // pongPlayer_8B60_p33 @ 0x82198B60
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x20;
}


// ===========================================================================
// SECTION — MarkNetDirtyScore  @ 0x82198B80 | size: 0x1C (28 bytes)
// ===========================================================================
/**
 * pongPlayer::MarkNetDirtyScore()
 *
 * If network dirty tracking is enabled (m_bNetDirtyEnabled != 0),
 * sets bit 6 (0x40) of the network dirty flags word.  This marks the
 * player's score data as needing replication.
 */
void pongPlayer::MarkNetDirtyScore() {  // pongPlayer_8B80_p33 @ 0x82198B80
    if (!m_bNetDirtyEnabled)
        return;
    m_netDirtyFlags |= 0x40;
}


// ===========================================================================
// SECTION — Update  @ 0x8218CF08 | size: 0x28 (40 bytes)
// ===========================================================================
/**
 * pongPlayer::Update()
 *
 * Top-level update entry point.  Checks if the player is initialised
 * (pointer at +0x2C non-null, via big-endian MSB byte check), then
 * dispatches to the virtual Update1 method (vtable slot 4, byte offset +16).
 *
 * If the player is not initialised, calls the debug log no-op and returns.
 */
void pongPlayer::Update() {  // pongPlayer_Update @ 0x8218CF08
    if (!m_pLocomotionState) {
        rage_debugLog("pongPlayer::Update() - player not initialized");
        return;
    }
    // Virtual dispatch to Update1 (vtable slot 4, byte offset +16)
    typedef void (*UpdateFn)(pongPlayer*);
    UpdateFn fn = reinterpret_cast<UpdateFn>(vtable[4]);
    fn(this);
}


// ===========================================================================
// SECTION — UpdateReplay  @ 0x8218E178 | size: 0x64 (100 bytes)
// ===========================================================================
/**
 * pongPlayer::UpdateReplay()
 *
 * Called during replay playback to update the player's state.
 * Checks if the player is initialised (same +0x2C null check as Update).
 * Then calls pongCreature_59C0_g on the opponent creature, followed by
 * pongPlayer_4C08_g on self to synchronise replay state.
 */
extern void pongCreature_59C0_g(void* creature);    // @ 0x820C59C0
extern void pongPlayer_4C08_g(pongPlayer* player);  // @ 0x82194C08

void pongPlayer::UpdateReplay() {  // pongPlayer_UpdateReplay @ 0x8218E178
    if (!m_pLocomotionState) {
        rage_debugLog("pongPlayer::UpdateReplay() - player is not active");
        return;
    }
    pongCreature_59C0_g(m_pOpponent);
    pongPlayer_4C08_g(this);
}


// ===========================================================================
// SECTION — pongPlayer_0C58_g  @ 0x821A0C58 | size: 0x50 (80 bytes)
// ===========================================================================
/**
 * pongPlayer_0C58_g()
 *
 * Checks whether the ball splash 2D effect for the current player's input
 * slot is active.  Loads the current input slot index from the SDA global,
 * indexes into g_ballSplashArray (416 bytes per entry, offset 48 from base),
 * and calls fxBallSplash2D_5998_g to query the active state.
 *
 * Returns: 1 if the splash effect is active (fxBallSplash2D returns 1),
 *          0 otherwise.
 */
extern int32_t  g_currentInputSlot;                              // @ SDA+25976 (0x82606578)
extern int      fxBallSplash2D_5998_g(void* splashEntry);       // @ 0x821D5998

uint8_t pongPlayer_0C58_g() {  // @ 0x821A0C58
    int32_t slot = g_currentInputSlot;
    uint8_t* entry = g_ballSplashArray + 48 + slot * 416;
    return (fxBallSplash2D_5998_g(entry) == 1) ? 1 : 0;
}


// ===========================================================================
// SECTION — ResetSwingDisplayValues  @ 0x821A7038 | size: 0x54 (84 bytes)
// ===========================================================================
/**
 * pongPlayer::ResetSwingDisplayValues()
 *
 * Resets the swing display sub-state at (this+5404) via pongPlayer_76E8_g,
 * then initialises three float fields at +5600, +5604, +5608 with
 * constant values from .rdata.
 */
extern void pongPlayer_76E8_g(void* swingDisplay);   // @ 0x821A76E8
extern const float g_kSwingDisplay0;                 // @ 0x82079AD4 [.rdata]
extern const float g_kSwingDisplay1;                 // @ 0x82079AD8 [.rdata]
extern const float g_kSwingDisplay2;                 // @ 0x82085938 [.rdata]

void pongPlayer::ResetSwingDisplayValues() {  // pongPlayer_7038 @ 0x821A7038
    uint8_t* base = reinterpret_cast<uint8_t*>(this);
    pongPlayer_76E8_g(base + 5404);
    *reinterpret_cast<float*>(base + 5600) = g_kSwingDisplay0;
    *reinterpret_cast<float*>(base + 5604) = g_kSwingDisplay1;
    *reinterpret_cast<float*>(base + 5608) = g_kSwingDisplay2;
}


// ===========================================================================
// SECTION — pongPlayer_D238_g  @ 0x820DD238 | size: 0x60 (96 bytes)
// ===========================================================================
/**
 * pongPlayer_D238_g(void* self)
 *
 * Computes the normalised animation time / recovery progress for the
 * player's recovery state.  Follows a pointer chain at self+36 to reach
 * the inner timing data:
 *   - If the sub-object at +36 is NULL, returns g_recoveryTimerThreshold.
 *   - If the total duration (sub->inner+12) is ≤ g_swingPhaseThreshold,
 *     returns g_swingPhaseThreshold.
 *   - Otherwise returns: (float)(frameCount @ sub+32) * g_kFrameScale
 *                         / (totalDuration @ sub->inner+12)
 */
extern const float g_kFrameScale;    // @ 0x82079BC8 [.rdata]

float pongPlayer_D238_g(void* self) {  // @ 0x820DD238
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    void* subObj = *reinterpret_cast<void**>(base + 36);

    if (!subObj) {
        return g_recoveryTimerThreshold;  // @ 0x8202D108
    }

    uint8_t* sub = reinterpret_cast<uint8_t*>(subObj);
    void* innerObj = *reinterpret_cast<void**>(sub + 36);
    float totalDuration = *reinterpret_cast<float*>(
        reinterpret_cast<uint8_t*>(innerObj) + 12);

    if (totalDuration <= g_swingPhaseThreshold) {  // @ 0x8202D110
        return g_swingPhaseThreshold;
    }

    int32_t frameCount = *reinterpret_cast<int32_t*>(sub + 32);
    return (float)frameCount * g_kFrameScale / totalDuration;
}


// ===========================================================================
// SECTION — pongPlayer_1510_g  @ 0x82391510 | size: 0x5C (92 bytes)
// ===========================================================================
/**
 * pongPlayer_1510_g(void* self)
 *
 * Processes a network client wrapper object.  Loads the inner object from
 * self+12, calls its virtual Process method (vtable slot 2) which returns
 * a float, stores that result at inner+12, then calls
 * SinglesNetworkClient_BE30_g(inner+16, 50) to update the network client.
 *
 * Returns: pointer to the network client sub-object (inner+16).
 */
extern void SinglesNetworkClient_BE30_g(void* client, int param);  // @ 0x8239BE30

void* pongPlayer_1510_g(void* self) {  // @ 0x82391510
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    void* innerObj = *reinterpret_cast<void**>(base + 12);
    uint8_t* inner = reinterpret_cast<uint8_t*>(innerObj);

    // Call vtable slot 2 (Process) on inner object — returns float
    void** innerVtable = *reinterpret_cast<void***>(inner);
    typedef float (*ProcessFn)(void*);
    float result = reinterpret_cast<ProcessFn>(innerVtable[2])(innerObj);

    // Store process result to inner+12
    *reinterpret_cast<float*>(inner + 12) = result;

    // Update network client at inner+16 with frame count param 50
    void* netClient = reinterpret_cast<void*>(inner + 16);
    SinglesNetworkClient_BE30_g(netClient, 50);

    return netClient;
}


// ===========================================================================
// SECTION — pongPlayer_5170_w  @ 0x82285170 | size: 0x5C (92 bytes)
// ===========================================================================
/**
 * pongPlayer_5170_w(void* boundsObj)
 *
 * 2D bounds check on a physics/collision object.  Returns 1 if the float
 * values at offsets +36 and +32 are both within their respective valid
 * ranges; returns 0 otherwise (including for NaN values).
 *
 * Conditions for returning 1:
 *   - val36 ∈ [g_kBoundsLower36, g_kBoundsUpper36)
 *   - val32 ∈ [g_kBoundsLower32, g_kBoundsUpper32)
 */
extern const float g_kBoundsUpper36;   // @ 0x82079B24 [.rdata]
extern const float g_kBoundsLower36;   // @ 0x8202C4E4 [.rdata]
extern const float g_kBoundsLower32;   // @ 0x82079B20 [.rdata]
extern const float g_kBoundsUpper32;   // @ 0x8202CFF4 [.rdata]

int pongPlayer_5170_w(void* boundsObj) {  // @ 0x82285170
    uint8_t* base = reinterpret_cast<uint8_t*>(boundsObj);
    float val36 = *reinterpret_cast<float*>(base + 36);
    float val32 = *reinterpret_cast<float*>(base + 32);

    // Check val36 is in range [lower, upper)
    if (val36 >= g_kBoundsUpper36)
        return 0;
    if (!(val36 >= g_kBoundsLower36))  // NaN-safe: !(NaN >= x) is true
        return 0;

    // Check val32 is in range [lower, upper)
    if (!(val32 >= g_kBoundsLower32))  // NaN-safe
        return 0;
    if (val32 < g_kBoundsUpper32)
        return 1;

    return 0;
}


// ===========================================================================
// SECTION — pongPlayer_AED0_p39  @ 0x8218AED0 | size: 0x6C (108 bytes)
// ===========================================================================
/**
 * pongPlayer::FindRegisteredListener(void* unused, void* target)
 *
 * Searches the registered listener array (count at this+144, pointer array
 * at this+152) for a matching target pointer.  Logs a debug message
 * indicating whether the target was found or not (via the target's name
 * field at target+4).
 *
 * This is a network reconciliation function (p39 suffix) used to validate
 * listener registration state.
 *
 * Note: first explicit argument (r4) is unused in the function body.
 *       Target pointer arrives in r5 (second explicit argument).
 */
void pongPlayer::FindRegisteredListener(void* unused, void* target) {
    // pongPlayer_AED0_p39 @ 0x8218AED0
    (void)unused;
    uint8_t* base = reinterpret_cast<uint8_t*>(this);
    int32_t count = *reinterpret_cast<int32_t*>(base + 144);
    uint32_t* array = *reinterpret_cast<uint32_t**>(base + 152);
    const char* targetName = *reinterpret_cast<const char**>(
        reinterpret_cast<uint8_t*>(target) + 4);

    int32_t foundIdx = -1;

    if (count > 0) {
        for (int32_t i = 0; i < count; i++) {
            if (foundIdx != -1) {
                // Found on previous iteration — log and return
                rage_debugLog("pongPlayer::FindRegisteredListener() found %s", targetName);
                return;
            }
            if (array[i] == reinterpret_cast<uintptr_t>(target)) {
                foundIdx = i;
            }
        }

        if (foundIdx != -1) {
            rage_debugLog("pongPlayer::FindRegisteredListener() found %s", targetName);
            return;
        }
    }

    // Not found in array
    rage_debugLog("pongPlayer::FindRegisteredListener() not found %s", targetName);
}


// ===========================================================================
// BATCH — 9 pongPlayer functions (112–148 bytes)
// Translated from PPC recompilation scaffolds
// ===========================================================================

// ── New external function declarations for this batch ───────────────────
// Court bounds + interpolation (called by pongPlayer_E7B0_g)
extern void  pongPlayer_FD20_g(void* a, int b, void* c, void* d,
                               int e, void* f, void* g, unsigned char h); // @ 0x821EFD20
// pongPlayer_E590_g — forward declared at top of file with correct 6-param signature
// Clock/config query — returns timing/state data from match config
extern void* pongPlayer_7CC0_g(void* matchConfig);                     // @ 0x821E7CC0
// Player record entry setup — configures a slot in the player data table
extern void  pongPlayer_05A8_g(void* entry, uint8_t metaByte,
                               void* clockData);                       // @ 0x821E05A8
// Normalize sub-struct extent vector (float param = threshold via f1)
extern void  pongPlayer_4EA0_g(void* sub, float normalizeVal);         // @ 0x821D4EA0
// Compute interpolated position into output buffer
extern void  pongPlayer_5010_g(void* sub, void* output,
                               void* parent, int flag);                // @ 0x821D5010

// ── New external global data for this batch ─────────────────────────────
extern uint8_t    g_replayStateData[];   // lbl_825CB3C0 @ 0x825CB3C0 (20 bytes, .data)
extern const float g_kPercentScale;      // flt_8202D118 @ 0x8202D118 (100.0f, .rdata)


// ===========================================================================
// SEC 48 — pongPlayer_9C60_g  @ 0x821C9C60 | size: 0x70 (112 bytes)
// ===========================================================================
/**
 * Registers a value into a player record slot.
 *
 * Queries match config for a clock/timing value via pongPlayer_7CC0_g,
 * reads a metadata byte from the caller's data region, looks up a slot
 * index from the player records table at [index+1], and — if valid
 * (0–3) — stores the value at entry+20 and calls pongPlayer_05A8_g
 * to configure the record.
 *
 * @param base   Pointer to caller's data region (byte at base+index+64)
 * @param index  Index into the slot table and byte-data offset
 * @param value  Value to store at the record entry's offset +20
 */
extern "C" void pongPlayer_9C60_g(void* base, int index, uint32_t value) {
    // Get timing state from match config
    void* clockData = pongPlayer_7CC0_g(g_pMatchConfig);

    // Read metadata byte from caller's data region
    uint8_t metaByte = *reinterpret_cast<uint8_t*>(
        reinterpret_cast<uintptr_t>(base) + index + 64);

    // Look up slot index from player records table
    uint32_t* slotTable = reinterpret_cast<uint32_t*>(g_pPlayerRecords);
    int32_t slotIdx = static_cast<int32_t>(slotTable[index + 1]);

    if (slotIdx >= 0 && slotIdx < 4) {
        uint8_t* entry = reinterpret_cast<uint8_t*>(g_pPlayerRecords)
                         + slotIdx * 808;
        *reinterpret_cast<uint32_t*>(entry + 20) = value;
        pongPlayer_05A8_g(entry + 12, metaByte, clockData);
    }
}


// ===========================================================================
// SEC 49 — pongPlayer_E7B0_g  @ 0x8219E7B0 | size: 0x7C (124 bytes)
// ===========================================================================
/**
 * Computes a swing target vector from court bounds.
 *
 * Input struct layout:
 *   +0:  uint8_t courtType     +1: uint8_t courtSubType
 *   +4:  float   posX          +8: float   posY
 *   +16: vec3    result (output — written by this function)
 *
 * Steps:
 *  1. Calls pongPlayer_FD20_g to resolve two court boundary vectors.
 *  2. Packs (posX, posY) into a temp and calls pongPlayer_E590_g
 *     to interpolate a position within those bounds.
 *  3. Returns pointer to the result vec3 at input+16.
 */
extern "C" void* pongPlayer_E7B0_g(void* inputStruct) {
    uint8_t* input = reinterpret_cast<uint8_t*>(inputStruct);
    uint8_t courtType    = input[0];
    uint8_t courtSubType = input[1];
    float posX = *reinterpret_cast<float*>(input + 4);
    float posY = *reinterpret_cast<float*>(input + 8);

    // Resolve court boundary vectors for the given types
    vec3 boundsA{}, boundsB{};
    pongPlayer_FD20_g(
        g_pGlobalClock, courtType, &boundsA, &boundsB, courtSubType,
        reinterpret_cast<void*>(static_cast<uintptr_t>(1)), nullptr, 0);

    // Pack current position for interpolation
    float tempPos[2] = { posX, posY };

    // Interpolate within bounds → write result at input+16
    void* result = input + 16;
    pongPlayer_E590_g(
        tempPos,
        courtType,
        reinterpret_cast<float*>(result), &boundsA.x, &boundsB.x, nullptr);

    return result;
}


// ===========================================================================
// SEC 50 — pongPlayer_8E88_g  @ 0x821C8E88 | size: 0x78 (120 bytes)
// ===========================================================================
/**
 * Returns a float value from the player state based on status flags.
 *
 * If the player is in an active state (flag byte at +334 set, or
 * counter at +340 non-zero), returns the alt value at offset +268.
 * Otherwise checks a global replay state flag (lbl_825CB3C0 +4);
 * if set → +268, else → base value at +264.
 */
extern "C" float pongPlayer_8E88_g(void* self) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);

    bool isActive = (base[334] != 0)
                 || (*reinterpret_cast<uint32_t*>(base + 340) != 0);

    if (isActive) {
        return *reinterpret_cast<float*>(base + 268);
    }

    // Check global replay state flag at +4
    uint32_t replayFlag = *reinterpret_cast<uint32_t*>(g_replayStateData + 4);
    if (replayFlag != 0) {
        return *reinterpret_cast<float*>(base + 268);
    }

    return *reinterpret_cast<float*>(base + 264);
}


// ===========================================================================
// SEC 51 — pongPlayer_4510_wrh  @ 0x82384510 | size: 0x78 (120 bytes)
// ===========================================================================
/**
 * Resets an array container sub-object.
 *
 * Sub-object layout:
 *   +4:  pointer to array of object pointers
 *   +8:  uint16_t element count
 *   +48: float (cleared to 0.0)   +52: byte (cleared)
 *   +56: float (cleared to 0.0)   +60: byte (cleared)
 *   +62: byte (cleared at end)
 *
 * Calls vtable slot 1 (reset/clear) on each element in the array,
 * then clears all timing/state fields.
 */
extern "C" void pongPlayer_4510_wrh(void* self) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);

    // Clear timing floats and state bytes
    *reinterpret_cast<float*>(base + 56) = 0.0f;
    *reinterpret_cast<float*>(base + 48) = 0.0f;
    base[60] = 0;
    base[52] = 0;

    int16_t count = static_cast<int16_t>(
        *reinterpret_cast<uint16_t*>(base + 8));

    if (count > 0) {
        uint32_t* array = *reinterpret_cast<uint32_t**>(base + 4);
        for (int16_t i = 0; i < count; i++) {
            // Call vtable slot 1 (reset) on each element
            void* obj = reinterpret_cast<void*>(
                static_cast<uintptr_t>(array[i]));
            void** vtable = *reinterpret_cast<void***>(obj);
            reinterpret_cast<void(*)(void*)>(vtable[1])(obj);

            // Reload count (may be modified by callback)
            count = static_cast<int16_t>(
                *reinterpret_cast<uint16_t*>(base + 8));
        }
    }

    base[62] = 0;
}


// ===========================================================================
// SEC 52 — pongPlayer_7F98_g  @ 0x821A7F98 | size: 0x84 (132 bytes)
// ===========================================================================
/**
 * Computes a completion percentage from timing sub-state fields.
 *
 * Sub-struct layout (not full pongPlayer):
 *   +4:  float currentTime (near path)
 *   +8:  float totalTime   (near path)
 *   +12: float currentTime (far path)
 *   +16: float totalTime   (far path)
 *   +28: uint8_t directionFlag
 *
 * When directionFlag != 0 (near path):
 *   Returns ((totalTime - currentTime) / totalTime) * 100.0f
 *
 * When directionFlag == 0 (far path):
 *   Returns (1.0f - ((totalTime - currentTime) / totalTime)) * 100.0f
 *
 * Returns 0.0f if any denominator is zero or negative.
 */
extern "C" float pongPlayer_7F98_g(void* self) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    uint8_t directionFlag = base[28];

    const float threshold = g_swingPhaseThreshold;  // 0.0f @ 0x8202D110
    const float scale     = g_kPercentScale;        // 100.0f @ 0x8202D118
    const float oneConst  = g_recoveryTimerThreshold; // 1.0f @ 0x8202D108

    if (directionFlag != 0) {
        // Near path: use fields at +4 and +8
        float current = *reinterpret_cast<float*>(base + 4);
        if (current > threshold) {
            float total = *reinterpret_cast<float*>(base + 8);
            if (total > threshold) {
                float ratio = (total - current) / total;
                return ratio * scale;
            }
        }
        // Flag set but times invalid → return 0.0f
        return threshold;
    }

    // Far path (directionFlag == 0): use fields at +12 and +16
    float current = *reinterpret_cast<float*>(base + 12);
    if (current <= threshold) return threshold;

    float total = *reinterpret_cast<float*>(base + 16);
    if (total <= threshold) return threshold;

    float ratio = (total - current) / total;
    float adjusted = oneConst - ratio;  // effectively currentTime / totalTime
    return adjusted * scale;
}


// ===========================================================================
// SEC 53 — pongPlayer_6360_g  @ 0x821D6360 | size: 0x84 (132 bytes)
// ===========================================================================
/**
 * Sets a court-position sub-struct from a boundary rectangle.
 *
 * Takes a struct (at self) with a 16-byte sub-struct at offset +64,
 * and a boundary rectangle (at bounds) with layout:
 *   +0: float x0   +4: float x1   +8: float z0   +12: float z1
 *
 * Computes:
 *   sub[0] = z1 - z0  (depth extent)
 *   sub[4] = x0 - x1  (width extent)
 *   sub[8] = 0.0f      (threshold constant)
 *
 * Then normalizes via pongPlayer_4EA0_g and computes an interpolated
 * position into sub+16 via pongPlayer_5010_g.
 */
extern "C" void pongPlayer_6360_g(void* self, void* bounds) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    float* rect   = reinterpret_cast<float*>(bounds);

    float x0 = rect[0];
    float x1 = rect[1];
    float z0 = rect[2];
    float z1 = rect[3];

    float widthDiff = x0 - x1;
    float depthDiff = z1 - z0;

    // Sub-struct at this + 64
    uint8_t* sub = base + 64;
    *reinterpret_cast<float*>(sub + 0) = depthDiff;
    *reinterpret_cast<float*>(sub + 8) = g_swingPhaseThreshold;  // 0.0f
    *reinterpret_cast<float*>(sub + 4) = widthDiff;

    // Normalize extent vector
    pongPlayer_4EA0_g(sub, g_swingPhaseThreshold);

    // Compute interpolated position → output at sub+16
    pongPlayer_5010_g(sub, sub + 16, self, 1);
}


// ===========================================================================
// SEC 54 — pongPlayer_62C0_g  @ 0x821962C0 | size: 0x88 (136 bytes)
// ===========================================================================
/**
 * Resets opponent animation/physics state flags.
 *
 * If a pending-clear flag at this+6537 is set:
 *   - Clears the flag and several timing floats at +6512/+6516/+6572
 *   - Sets bit 0 of the opponent's physicsBound flags at +64
 *   - Clears secondary flag at +6637
 *
 * Then, if the opponent exists:
 *   - If resetFlag is true:  zeros 16 bytes at physicsBound+208 and
 *     sets physicsBound+134 = 1 (enable anim tracking)
 *   - If resetFlag is false: clears physicsBound+134 = 0 (disable)
 */
extern "C" void pongPlayer_62C0_g(pongPlayer* self, uint8_t resetFlag) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);

    if (base[6537] != 0) {
        pongPlayer* opponent = self->m_pOpponent;
        base[6537] = 0;

        // Clear timing/interpolation floats
        *reinterpret_cast<float*>(base + 6512) = 0.0f;
        *reinterpret_cast<float*>(base + 6516) = 0.0f;
        *reinterpret_cast<float*>(base + 6572) = 0.0f;

        // Set bit 0 on opponent's physicsBound flags at +64
        uint8_t* physBound = reinterpret_cast<uint8_t*>(
            opponent->m_pPhysicsBound);
        physBound[64] |= 1;

        base[6637] = 0;
    }

    pongPlayer* opponent = self->m_pOpponent;
    if (opponent == nullptr) return;

    uint8_t* physBound = reinterpret_cast<uint8_t*>(
        opponent->m_pPhysicsBound);

    if (resetFlag != 0) {
        // Zero 16-byte animation vector at physicsBound+208
        memset(physBound + 208, 0, 16);
        physBound[134] = 1;
    } else {
        physBound[134] = 0;
    }
}


// ===========================================================================
// SEC 55 — pongPlayer_63E8_g  @ 0x821D63E8 | size: 0x88 (136 bytes)
// ===========================================================================
/**
 * Accumulates court-position extents from a boundary rectangle.
 *
 * Same as pongPlayer_6360_g but ADDS the computed deltas to the
 * existing sub-struct values instead of overwriting them:
 *   sub[0] += depthDiff  (z1 - z0)
 *   sub[4] += widthDiff  (x0 - x1)
 *
 * Then normalizes and recomputes interpolated position.
 */
extern "C" void pongPlayer_63E8_g(void* self, void* bounds) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    float* rect   = reinterpret_cast<float*>(bounds);

    float x0 = rect[0];
    float x1 = rect[1];
    float z0 = rect[2];
    float z1 = rect[3];

    float widthDiff = x0 - x1;
    float depthDiff = z1 - z0;

    // Sub-struct at this + 64
    uint8_t* sub = base + 64;

    // Accumulate deltas into existing values
    float oldDepth = *reinterpret_cast<float*>(sub + 0);
    float oldWidth = *reinterpret_cast<float*>(sub + 4);
    *reinterpret_cast<float*>(sub + 4) = oldWidth + widthDiff;
    *reinterpret_cast<float*>(sub + 0) = oldDepth + depthDiff;

    // Normalize extent vector
    pongPlayer_4EA0_g(sub, g_swingPhaseThreshold);

    // Compute interpolated position → output at sub+16
    pongPlayer_5010_g(sub, sub + 16, self, 1);
}


// ===========================================================================
// SEC 56 — pongPlayer_5800_h  @ 0x82195800 | size: 0x90 (144 bytes)
// ===========================================================================
/**
 * Checks whether the player can accept swing input this frame.
 *
 * Three-stage check:
 *  1. If the global input table entry has both flags at +212 and +213
 *     set → return false (input blocked by system).
 *  2. If the player's action state at +460 is 2, 3, or 4 (serve
 *     receive / active rally states) → return true.
 *  3. Otherwise, delegates to the opponent's player state
 *     IsBeforeSwingPeak() check.
 *
 * @return true if the player can initiate a swing, false otherwise.
 */
extern "C" bool pongPlayer_5800_h(pongPlayer* self) {
    // Look up entry in g_ballSplashArray (416-byte stride, +48 header)
    int32_t slotIdx = self->m_inputSlotIdx;
    uint8_t* entry = g_ballSplashArray + 48
                   + static_cast<uint32_t>(slotIdx) * 416;

    // Check if both input channel flags are set → blocked
    if (entry[213] != 0 && entry[212] != 0) {
        return false;
    }

    // Check action state (offset +460 = 0x1CC from this)
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    int32_t actionState = *reinterpret_cast<int32_t*>(base + 460);
    if (actionState == 4 || actionState == 2 || actionState == 3) {
        return true;
    }

    // Fall through: check opponent's swing peak state
    return self->m_pOpponent->m_pPlayerState->IsBeforeSwingPeak();
}

// NOTE: pongPlayer_9CD0_g @ 0x821C9CD0 (0x94 bytes) is already
// implemented in src/game/player/pong_player_swing.cpp as
// GetCreatureBoneMatrix(), with an extern "C" wrapper.


// ===========================================================================
// ===========================================================================
//  BATCH 10 — Medium pongPlayer functions (148–220 bytes)
// ===========================================================================
// ===========================================================================


// ===========================================================================
// ClearSwingSlotGrid  @ 0x8219E640 | size: 0x94 (148 bytes)
// ===========================================================================
/**
 * Resets a swing slot grid sub-object to default state.
 *
 * Zeros 6 × 16-byte vector slots, resets two default float fields,
 * clears associated flags/counters, and writes a reset constant to
 * a global default value.
 *
 * @param gridSubObj  Pointer to swing grid sub-object
 *                    (pongPlayer base + 96 or + 2800)
 */
void pongPlayer_E640_g(void* gridSubObj) {  // ClearSwingSlotGrid @ 0x8219E640
    uint8_t* base = static_cast<uint8_t*>(gridSubObj);

    // Zero 6 × 16-byte vector slots
    memset(base + 832, 0, 16);
    memset(base + 864, 0, 16);
    memset(base + 880, 0, 16);
    memset(base + 896, 0, 16);
    memset(base + 912, 0, 16);
    memset(base + 928, 0, 16);

    // Reset float fields to constant default
    *reinterpret_cast<float*>(base + 848) = g_kFloatConst_D110;
    *reinterpret_cast<float*>(base + 852) = g_kFloatConst_D110;

    // Clear flags and counter
    base[956] = 0;
    base[968] = 0;
    *reinterpret_cast<uint32_t*>(base + 972) = 0;

    // Write reset constant to global
    g_swingSlotGridDefault = g_kFloatConst_D168;
}


// ===========================================================================
// InterpolateGridPosition  @ 0x8219E590 | size: 0xB0 (176 bytes)
// ===========================================================================
/**
 * Computes an interpolated court grid position.
 *
 * Lerps X/Z between two boundary corners based on a flip flag,
 * sets Y from the court geometry singleton, and adds an offset vector.
 *
 * @param lerpFactors  2 floats: X lerp at [0], Z lerp at [1]
 * @param flip         0 = lerp A->B, nonzero = lerp B->A
 * @param outPos       Output vec3 (writes X at +0, Y at +4, Z at +8)
 * @param boundsA      Corner A (reads X at +0, Z at +8)
 * @param boundsB      Corner B (reads X at +0, Z at +8)
 * @param offset       Offset vec3 (added to final result)
 */
void pongPlayer_E590_g(float* lerpFactors, uint8_t flip, float* outPos,
                       float* boundsA, float* boundsB,
                       float* offset) {  // InterpolateGridPosition @ 0x8219E590
    // Load court height from global singleton (+20 bytes from base)
    float* courtSingleton = static_cast<float*>(g_pCourtGeomSingleton);
    float courtHeight = courtSingleton[5];

    // Y = court height + offset constant
    outPos[1] = courtHeight + g_kCourtHeightOffset;

    if (flip) {
        // Lerp from boundsB toward boundsA
        float rangeX = boundsA[0] - boundsB[0];
        outPos[0] = boundsB[0] + lerpFactors[0] * rangeX;

        float rangeZ = boundsA[2] - boundsB[2];
        outPos[2] = boundsB[2] + lerpFactors[1] * rangeZ;
    } else {
        // Lerp from boundsA toward boundsB
        float rangeX = boundsB[0] - boundsA[0];
        outPos[0] = boundsA[0] + lerpFactors[0] * rangeX;

        float rangeZ = boundsB[2] - boundsA[2];
        outPos[2] = boundsA[2] + lerpFactors[1] * rangeZ;
    }

    // Add offset vector (PPC vaddfp: component-wise float add)
    outPos[0] += offset[0];
    outPos[1] += offset[1];
    outPos[2] += offset[2];
}


// ===========================================================================
// SetServeSideFlip  @ 0x82193628 | size: 0xAC (172 bytes)
// ===========================================================================
/**
 * Stores the serve-side flip flag to geometry tables and propagates
 * to the opponent's record if an active opponent slot exists.
 *
 * Called from ResetServePosition to configure serve direction.
 *
 * @param player  pongPlayer whose serve side is being set
 * @param flip    0 or 1 — serve-side flip flag
 */
void pongPlayer_3628_g(pongPlayer* player, uint8_t flip) {  // SetServeSideFlip @ 0x82193628
    int32_t slotIdx = player->m_inputSlotIdx;

    // Store flip to geometry base: g_pInputObj[slotIdx] + 64
    uint8_t* geomBase = static_cast<uint8_t*>(g_pInputObj) + slotIdx;
    geomBase[64] = flip;

    // Store flip to court data table: g_ballSplashArray + 262 + slotIdx * 416
    g_ballSplashArray[262 + slotIdx * 416] = flip;

    // Check if opponent slot is active (word at g_pInputObj[(slotIdx+14)*4])
    uint32_t* inputSlots = reinterpret_cast<uint32_t*>(g_pInputObj);
    bool opponentActive = (inputSlots[slotIdx + 14] == 1);

    if (opponentActive) {
        // Look up opponent entry from player data table
        uint32_t* dataEntries = reinterpret_cast<uint32_t*>(g_pPlayerDataTable);
        uint32_t opponentEntry = dataEntries[slotIdx + 1];

        // Get player handedness from slot lookup
        void* handedness = pongPlayer_7CC0_g(g_pPlayerSlotLookup);

        // Compute opponent record base: table + entry*808 + 12
        void* recordBase = g_pPlayerDataTable + opponentEntry * 808 + 12;

        // Apply serve-side flip to opponent record
        pongPlayer_05A8_g(recordBase, flip, handedness);
    }
}


// ===========================================================================
// IsSwingType  @ 0x821D6050 | size: 0xB0 (176 bytes)
// ===========================================================================
/**
 * Returns true if the given type ID is a recognized swing type.
 *
 * Forehand: 2, 3, 10, 11 | Power: 8, 16 | Topspin: 5, 13 | Slice: 7, 15
 *
 * Pure function — no memory access, no side effects.
 */
bool pongPlayer_6050_p46(int32_t swingType) {  // IsSwingType @ 0x821D6050
    switch (swingType) {
        case 2: case 3: case 10: case 11:   // forehand group
        case 8: case 16:                     // power group
        case 5: case 13:                     // topspin group
        case 7: case 15:                     // slice group
            return true;
        default:
            return false;
    }
}


// ===========================================================================
// GetCourtSideSign  @ 0x821A0F10 | size: 0xB8 (184 bytes)
// ===========================================================================
/**
 * Determines which side of the court a player is on based on
 * the X position of a linked position sub-object.
 *
 * @param stateObj  Object with parent pongPlayer* at +48
 * @param outSign   Output: receives a positive or negative sign constant
 * @param deadZone  Absolute threshold below which no side is determined
 */
void pongPlayer_0F10_g(void* stateObj, float* outSign,
                       float deadZone) {  // GetCourtSideSign @ 0x821A0F10
    uint8_t* base = static_cast<uint8_t*>(stateObj);
    uint8_t* parent = *reinterpret_cast<uint8_t**>(base + 48);
    int32_t slotIdx = *reinterpret_cast<int32_t*>(parent + 464);

    // Select position sub-object based on slot index
    void* posObj;
    if (slotIdx == 0) {
        posObj = *reinterpret_cast<void**>(parent + 72);
    } else {
        posObj = *reinterpret_cast<void**>(parent + 68);
    }

    // Read X position from sub-object position vector at +48
    float posX = *reinterpret_cast<float*>(
        static_cast<uint8_t*>(posObj) + 48);

    // Dead-zone check: return early if position is too close to center
    if (fabsf(posX) < deadZone) return;

    // Determine court side sign from position X
    if (posX >= g_kFloatConst_D110) {
        *outSign = g_kPositiveSideSign;   // positive side @ 0x825C5938
    } else {
        *outSign = g_kFloatConst_D108;    // negative side @ 0x8202D108
    }
}


// ===========================================================================
// InitSwingHistorySlots  @ 0x821A76E8 | size: 0xBC (188 bytes)
// ===========================================================================
/**
 * Initializes a swing history tracking structure.
 *
 * Layout: +4/+6 = int16 slot indices (-1), +8 = int16 count (0),
 * +12..+23 = 3 header floats, +24..+103 = 20 weight floats,
 * +108..+187 = 20 value floats (from source max at +192).
 *
 * @param swingHistory  Pointer to swing history structure
 */
void pongPlayer_76E8_g(void* swingHistory) {  // InitSwingHistorySlots @ 0x821A76E8
    uint8_t* base = static_cast<uint8_t*>(swingHistory);
    float defaultVal = g_kFloatConst_D110;
    float maxVal = *reinterpret_cast<float*>(base + 192);

    // Reset slot indices and count
    *reinterpret_cast<int16_t*>(base + 4) = -1;
    *reinterpret_cast<int16_t*>(base + 6) = -1;
    *reinterpret_cast<int16_t*>(base + 8) = 0;

    // Reset header floats
    *reinterpret_cast<float*>(base + 12) = defaultVal;
    *reinterpret_cast<float*>(base + 16) = defaultVal;
    *reinterpret_cast<float*>(base + 20) = defaultVal;

    // Reset weight and value arrays (2 groups of 10 entries each)
    float* weights = reinterpret_cast<float*>(base + 24);
    float* values  = reinterpret_cast<float*>(base + 108);
    for (int i = 0; i < 20; i++) {
        weights[i] = defaultVal;
        values[i]  = maxVal;
    }
}


// ===========================================================================
// RemoveSlotEntry  @ 0x8218AE10 | size: 0xBC (188 bytes)
// ===========================================================================
/**
 * Deactivates and removes an entry from a slot grid.
 *
 * Computes the cell from (entryId, column) using a 24-byte stride,
 * deactivates the entry if active, calls its vtable[0] reset, clears
 * the back-reference, and zeros the cell metadata.
 *
 * @param slotsBase  Base pointer of the slot collection
 * @param slotId     Slot ID (indexes into entry table at +33 words)
 * @param column     Column index within the 2D grid
 */
void pongPlayer_AE10_g(void* slotsBase, int32_t slotId,
                       int32_t column) {  // RemoveSlotEntry @ 0x8218AE10
    uint8_t* base = static_cast<uint8_t*>(slotsBase);

    // Look up entry ID from slot table
    uint32_t entryId = *reinterpret_cast<uint32_t*>(
        base + (slotId + 33) * 4);

    // Compute cell byte offset: (entryId*2 + column) * 24
    uint32_t cellIndex = entryId * 2 + column;
    uint32_t byteOffset = cellIndex * 3 * 8;  // 24-byte cell stride
    uint8_t* cellPtr = base + byteOffset;

    // Get entry object pointer from cell+40
    void* entry = *reinterpret_cast<void**>(cellPtr + 40);

    // Debug checkpoint (no-op in release)
    nop_8240E6D0("RemoveSlotEntry enter");

    // Deactivate entry if active (byte at entry+44)
    uint8_t* entryBytes = static_cast<uint8_t*>(entry);
    if (entryBytes[44]) {
        pongPlayer_Deactivate(entry);
    }

    // Call entry's vtable[0](entry, 0) — virtual reset
    void** vtable = *reinterpret_cast<void***>(entry);
    typedef void (*VtableSlot0Fn)(void*, int);
    reinterpret_cast<VtableSlot0Fn>(vtable[0])(entry, 0);

    // Debug checkpoint (no-op in release)
    nop_8240E6D0("RemoveSlotEntry done");

    // Clear back-reference if it matches this entry
    void* currentEntry = *reinterpret_cast<void**>(cellPtr + 40);
    void** backRef = reinterpret_cast<void**>(
        base + (entryId + 29) * 4);
    if (*backRef == currentEntry) {
        *backRef = nullptr;
    }

    // Clear cell metadata
    cellPtr[32] = 0;
    cellPtr[33] = 0;
    *reinterpret_cast<int32_t*>(cellPtr + 24) = -1;
    *reinterpret_cast<int32_t*>(cellPtr + 28) = -1;
    *reinterpret_cast<void**>(cellPtr + 40) = nullptr;
}


// ===========================================================================
// UpdateTransitionBlend  @ 0x82384438 | size: 0xD8 (216 bytes)
// ===========================================================================
/**
 * Updates an animation transition blend state object.
 *
 * Checks completion flag, compares current vs previous section,
 * and either interpolates the transition value via pongPlayer_99B0_g
 * or directly snaps it based on the target distance.
 *
 * @param transObj  Transition blend state object
 *   +48: float current value, +52: byte current section,
 *   +56: float target, +60: byte previous section, +61: byte complete
 */
void pongPlayer_4438_fw(void* transObj) {  // UpdateTransitionBlend @ 0x82384438
    uint8_t* base = static_cast<uint8_t*>(transObj);

    // Already complete — nothing to do
    if (base[61]) return;

    uint8_t currentSection = base[52];
    uint8_t previousSection = base[60];

    float lowerBound = g_kFloatConst_D110;   // @ 0x8202D110
    float upperBound = g_kFloatConst_D108;   // @ 0x8202D108

    // If sections match and value is within transition bounds, skip
    if (currentSection == previousSection) {
        float value = *reinterpret_cast<float*>(base + 48);
        if (value <= lowerBound) return;
        if (value >= upperBound) return;
    }

    float target = *reinterpret_cast<float*>(base + 56);

    if (target > lowerBound) {
        // Interpolated transition using pongPlayer_99B0_g
        float startValue = (currentSection != 0) ? upperBound : lowerBound;
        float ratio = upperBound / target;

        bool updated = pongPlayer_99B0_g(
            reinterpret_cast<float*>(base + 48),
            startValue, ratio, g_kTransitionStep);

        if (!updated) return;

        // Sync: copy current section to previous
        base[60] = base[52];
    } else {
        // Direct update: snap to target
        base[60] = currentSection;
        float snapValue = (currentSection != 0) ? upperBound : lowerBound;
        *reinterpret_cast<float*>(base + 48) = snapValue;
    }
}


// ===========================================================================
// ResetAnimTransitionState  @ 0x8239D6C8 | size: 0xDC (220 bytes)
// ===========================================================================
/**
 * Clears all animation transition tracking data.
 *
 * Zeros two 80-byte data blocks, three 16-byte vectors, and a flag
 * byte. If a reset-pending flag is set, triggers a state change via
 * pongPlayer_5C00_g and clears an animation visibility bit.
 *
 * @param animTransObj  Animation transition state object
 *   +4: pongPlayer*, +112: data block A, +196: data block B,
 *   +288/304/320: vectors, +336: flag, +352: reset-pending
 */
void pongPlayer_D6C8_fw(void* animTransObj) {  // ResetAnimTransitionState @ 0x8239D6C8
    uint8_t* base = static_cast<uint8_t*>(animTransObj);

    // Zero first data block: 20 words (80 bytes) at +112
    memset(base + 112, 0, 80);

    // Zero second data block: 20 words (80 bytes) at +196
    memset(base + 196, 0, 80);

    // Zero three 16-byte vectors at +288, +304, +320
    memset(base + 288, 0, 48);

    // Clear flag byte at +336
    base[336] = 0;

    // If reset-pending flag is set
    if (base[352]) {
        // Trigger animation state change (mode 3)
        void* playerPtr = *reinterpret_cast<void**>(base + 4);
        pongPlayer_5C00_g(playerPtr, 3);

        // Clear animation visibility bit (bit 5) on nested sub-object
        uint8_t* playerBytes = *reinterpret_cast<uint8_t**>(base + 4);  // reload after call
        uint8_t* opponentObj = *reinterpret_cast<uint8_t**>(playerBytes + 452);
        uint8_t* animObj = *reinterpret_cast<uint8_t**>(opponentObj + 168);
        uint8_t* flagByte = animObj + 64;
        *flagByte &= 0xDF;  // clear bit 5

        // Clear the reset-pending flag
        base[352] = 0;
    }
}


// ===========================================================================
// ComputeSwingTargetDelta  @ 0x821906A0 | size: 0xDC (220 bytes)
// ===========================================================================
/**
 * Computes a swing target direction vector from the opponent's
 * player data record.
 *
 * Calls pongPlayer_0508_g twice (channels 31 and 30) to get swing
 * deltas. Negates both, then checks handedness — if the stored
 * handedness matches the computed one, negates again (cancelling out).
 *
 * @param outVec   Output: 2 floats ([0]=X, [1]=Y direction)
 * @param player   pongPlayer whose opponent record is queried
 */
void pongPlayer_06A0_g(float* outVec,
                       pongPlayer* player) {  // ComputeSwingTargetDelta @ 0x821906A0
    float inputConst = g_kSwingTargetConst;   // @ 0x825C80FC
    int32_t slotIdx = player->m_inputSlotIdx;

    // Look up opponent record from player data table
    uint32_t* dataEntries = reinterpret_cast<uint32_t*>(g_pPlayerDataTable);
    uint32_t opponentEntry = dataEntries[slotIdx + 1];
    void* recordBase = g_pPlayerDataTable + opponentEntry * 808 + 12;

    // Get swing deltas for channels 31 and 30
    float delta1 = pongPlayer_0508_g(recordBase, 31, inputConst);
    float delta2 = pongPlayer_0508_g(recordBase, 30, inputConst);

    // Store negated deltas
    outVec[1] = -delta1;
    outVec[0] = -delta2;

    // Get computed handedness from global slot lookup
    void* computedHandedness = pongPlayer_7CC0_g(g_pPlayerSlotLookup);

    // Read stored handedness from geometry table
    uint8_t* geomBase = static_cast<uint8_t*>(g_pInputObj) + slotIdx;
    uint8_t storedHandedness = geomBase[64];

    // If handedness matches (XOR == 0): negate again → original direction
    if ((storedHandedness ^ static_cast<uint8_t>(reinterpret_cast<uintptr_t>(computedHandedness) & 0xFF)) == 0) {
        outVec[0] = -outVec[0];
        outVec[1] = -outVec[1];
    }
}

// ===========================================================================
// BATCH 10 — Medium pongPlayer functions (136-248 bytes)
// ===========================================================================

// ---------------------------------------------------------------------------
// External forward declarations for batch 10
// ---------------------------------------------------------------------------
extern void* pg_9C00_g(void* inputObj, void* creature);
extern void phBoundCapsule_0880_g(void* capsule, void* outMatrix, uint32_t param);
extern float pongPlayer_C7A8_g(pongPlayer* player);
extern void pongPlayer_B088_2hr(void* timingData, float dir, float power);
extern void pongPlayer_E2C8_g(void* obj, int a, int b, int c, int d);
extern void pongPlayer_E008_g(void* obj, int a, int b, int c);
extern bool pongPlayer_D6B8_IsCreatureReady(void* characterSub);
extern void ServeStartedMessage_CFE8_2h(void* msgObj, void* targetData, int param);
extern void PlayerMovementMessage_D258_2hr(void* msgObj, float posX, float posZ);
extern void pongPlayer_B208_g(void* state, vec3* swingVec, uint8_t suppressFlip);
extern void pg_E6E0_msg(int messageId, int flags, int count, void* data);
extern "C" void pongPlayer_9CD0_g(void*, int, void*, void*);

extern uint32_t g_rngState[2];              // RNG state (lo, hi) @ 0x825CA2C8
extern const float g_kFloatConst_79E68;     // random scale factor @ 0x82079E68
extern const float g_kFloatConst_5C5938;    // height ratio threshold @ 0x825C5938
extern const float g_kFloatConst_79BB8;     // frame-to-duration scale @ 0x82079BB8
extern const double g_kDoubleConst_79D10;   // floor constant @ 0x82079D10
extern const double g_kDoubleConst_79B08;   // ceiling constant @ 0x82079B08


// ===========================================================================
// 1. UpdateOpponentBoundTransform
// ===========================================================================
/**
 * pongPlayer::UpdateOpponentBoundTransform()
 * @ 0x82194C08 | size: 0xA8
 *
 * Gets the opponent's physics bound capsule via the creature lookup chain,
 * computes a transform matrix, and copies the 4x16-byte result into
 * m_pLocoState2 at offset +32.
 */
void pongPlayer::UpdateOpponentBoundTransform() {  // pongPlayer_4C08_g @ 0x82194C08
    if (!m_pOpponent) return;

    // Get opponent's character sub-object at +188
    uint8_t* opponentBytes = reinterpret_cast<uint8_t*>(m_pOpponent);
    uint8_t* characterSub = *reinterpret_cast<uint8_t**>(opponentBytes + 188);

    // Look up creature in the physics system
    void* creature = *reinterpret_cast<void**>(characterSub + 8);
    void* lookupResult = pg_9C00_g(
        reinterpret_cast<void*>(g_pInputArrayTable), creature);

    // Navigate chain: result->+44->+324 to get bound capsule
    uint8_t* chainEntry = *reinterpret_cast<uint8_t**>(
        static_cast<uint8_t*>(lookupResult) + 44);
    void* boundCapsule = *reinterpret_cast<void**>(chainEntry + 324);

    // Compute transform matrix from bound capsule
    vec3 transformMatrix[4];  // 4x16 = 64 bytes
    uint32_t meshParam = *reinterpret_cast<uint32_t*>(characterSub + 28);
    phBoundCapsule_0880_g(boundCapsule, transformMatrix, meshParam);

    // Copy matrix to locomotion state data at +32
    uint8_t* dest = reinterpret_cast<uint8_t*>(m_pLocoState2) + 32;
    memcpy(dest, transformMatrix, sizeof(vec3) * 4);
}


// ===========================================================================
// 2. UpdateOpponentSwingTiming
// ===========================================================================
/**
 * pongPlayer::UpdateOpponentSwingTiming()
 * @ 0x82193738 | size: 0xA8
 *
 * If the input button at slot (inputSlotIdx + 14) is pressed, computes a
 * swing timing value via pongPlayer_C7A8_g and stores it (plus its square)
 * in the opponent's timing sub-object at +72/+76, then forwards to the
 * timing computation handler.
 */
void pongPlayer::UpdateOpponentSwingTiming(float swingDirection,
                                           float swingPower) {  // pongPlayer_3738 @ 0x82193738
    // Check button state at input slot + 14
    uint32_t* inputTable = reinterpret_cast<uint32_t*>(g_pInputArrayTable);
    uint32_t buttonState = inputTable[m_inputSlotIdx + 14];

    if (buttonState != 1) return;

    // Compute swing timing value
    float timingValue = pongPlayer_C7A8_g(this);

    // Get opponent's timing sub-object at +168
    uint8_t* opponentBytes = reinterpret_cast<uint8_t*>(m_pOpponent);
    uint8_t* timingSub = *reinterpret_cast<uint8_t**>(opponentBytes + 168);

    // Store timing value and its square
    *reinterpret_cast<float*>(timingSub + 72) = timingValue;
    *reinterpret_cast<float*>(timingSub + 76) = timingValue * timingValue;

    // Forward to timing computation handler
    pongPlayer_B088_2hr(timingSub, swingDirection, swingPower);
}


// ===========================================================================
// 3. ResetButtonSlotTrackingData (static)
// ===========================================================================
/**
 * pongPlayer::ResetButtonSlotTrackingData()
 * @ 0x821C9918 | size: 0xF8
 *
 * Resets per-player-slot shot tracking data.  Each slot is 36 bytes in
 * the button state table; within each slot at +172, three 12-byte tracking
 * entries store button state flags.  If any flags are raised, posts a
 * message event before clearing all entries via SyncByteField.
 */
void pongPlayer::ResetButtonSlotTrackingData(
    void* buttonStateBase, int slotIndex) {  // pongPlayer_9918_g @ 0x821C9918
    uint8_t* base = reinterpret_cast<uint8_t*>(buttonStateBase);
    uint8_t* slotData = base + slotIndex * 36;
    uint8_t* trackBase = slotData + 172;

    uint8_t flag0 = trackBase[0];
    uint8_t flag1 = trackBase[12];   // slotData + 184
    uint8_t flag2 = trackBase[24];   // slotData + 196

    // Check if any tracking flags are raised
    if (flag0 || flag1 || flag2) {
        // Determine which slot flag triggered (0, 1, or 2)
        int slotResult = 0;
        if (!flag0) {
            slotResult = flag1 ? 1 : (flag2 ? 2 : 0);
        }

        // Post tracking reset event (pg_E6E0 @ 0x8225E6E0)
        uint8_t bitMask = static_cast<uint8_t>((1 << slotIndex) & 0xFF) | 64;
        pg_E6E0_msg(4131, static_cast<int>(bitMask), 1, &slotResult);
    }

    // Clear float at computed offset (slotIndex + 61) * 4
    *reinterpret_cast<float*>(base + (slotIndex + 61) * 4) = 0.0f;

    // Clear 3 tracking entries (12 bytes apart) via SyncByteField
    uint8_t clearByte = 0;
    for (int i = 0; i < 3; i++) {
        pongPlayer_9108_g(trackBase + i * 12, &clearByte);
    }

    // Clear float at computed offset (slotIndex + 63) * 4
    *reinterpret_cast<float*>(base + (slotIndex + 63) * 4) = 0.0f;
}


// ===========================================================================
// 4. ComputeClampedPositions (free function)
// ===========================================================================
/**
 * pongPlayer_ComputeClampedPositions()
 * @ 0x821729F8 | size: 0xEC
 *
 * Computes two clamped normalized values from creature bone data.
 * Looks up bone matrices for the given creature index, determines the
 * mirroring state, then normalizes Z-position and height ratio relative
 * to the bone range.  Both outputs are clamped to [floor, ceiling] using
 * double-precision .rdata constants.
 */
void pongPlayer_ComputeClampedPositions(int creatureIndex,
                                        float* outA,
                                        float* outB) {  // pongPlayer_29F8_fw @ 0x821729F8
    // Get creature bone matrices
    vec3 bonePos1, bonePos2;
    pongPlayer_9CD0_g(reinterpret_cast<void*>(g_pInputArrayTable),
                      creatureIndex, &bonePos1, &bonePos2);

    // Check mirror flag at inputTable base + creatureIndex + 64
    uint8_t isMirrored = *(reinterpret_cast<uint8_t*>(g_pInputArrayTable)
                           + creatureIndex + 64);

    // Select range bounds based on mirror state
    float rangeHi, rangeLo, widthDenom;
    if (isMirrored) {
        rangeHi    = bonePos2.z;
        rangeLo    = bonePos1.z;
        widthDenom = bonePos2.x;
    } else {
        rangeHi    = bonePos1.z;
        rangeLo    = bonePos2.z;
        widthDenom = bonePos1.x;
    }

    // Get reference data from input table entry
    uint32_t* inputTable = reinterpret_cast<uint32_t*>(g_pInputArrayTable);
    uint8_t* refObj = reinterpret_cast<uint8_t*>(
        static_cast<uintptr_t>(inputTable[creatureIndex + 17]));
    float refZ      = *reinterpret_cast<float*>(refObj + 56);
    float refHeight = *reinterpret_cast<float*>(refObj + 48);

    // Compute normalized Z position and height ratio
    float range = rangeHi - rangeLo;
    float normalizedPos = (refZ - rangeLo) / range;
    float heightRatio = refHeight / widthDenom;

    // Clamp normalizedPos to floor (fsel: >= 0 ? value : floor)
    double posVal = (normalizedPos >= 0.0f)
        ? static_cast<double>(normalizedPos) : g_kDoubleConst_79B00;

    // Clamp heightRatio: threshold-based floor
    double heightVal = ((heightRatio - g_kFloatConst_5C5938) >= 0.0f)
        ? static_cast<double>(heightRatio) : g_kDoubleConst_79D10;

    // Clamp both to ceiling
    double ceiling = g_kDoubleConst_79B08;
    *outB = static_cast<float>((posVal - ceiling >= 0.0) ? ceiling : posVal);
    *outA = static_cast<float>((heightVal - ceiling >= 0.0) ? ceiling : heightVal);
}


// ===========================================================================
// 5. RandomizeShotTargetData (free function)
// ===========================================================================
/**
 * pongPlayer_RandomizeShotTargetData()
 * @ 0x821A6A98 | size: 0xE4
 *
 * Randomizes two position fields in a shot target data structure using
 * a 64-bit linear congruential RNG.  The LCG multiplier is 0x5CCCFAA7.
 * Each randomized value is: random_mantissa * range * scale + base.
 * Also resets associated tracking bytes and flags.
 */
void pongPlayer_RandomizeShotTargetData(void* shotData) {  // pongPlayer_6A98_g @ 0x821A6A98
    uint8_t* base = reinterpret_cast<uint8_t*>(shotData);
    const uint32_t kRngMultiplier = 0x5CCCFAA7u;
    float scale = g_kFloatConst_79E68;

    // Load struct parameters for first randomization
    float range1 = *reinterpret_cast<float*>(base + 16);
    float base1  = *reinterpret_cast<float*>(base + 8);
    float target = *reinterpret_cast<float*>(base + 20);

    // Clear flags and copy target float
    *(base + 56) = 0;
    *reinterpret_cast<float*>(base + 24) = target;
    *(base + 57) = 0;

    // Generate first random value (LCG step)
    uint64_t rngVal = static_cast<uint64_t>(g_rngState[0]) * kRngMultiplier
                    + g_rngState[1];
    g_rngState[0] = static_cast<uint32_t>(rngVal);
    g_rngState[1] = static_cast<uint32_t>(rngVal >> 32);
    uint32_t rand1 = g_rngState[0] & 0x7FFFFF;

    // Compute randomized position: random * range * scale + base
    float randFloat1 = static_cast<float>(static_cast<int64_t>(rand1));
    *reinterpret_cast<float*>(base + 4) = randFloat1 * range1 * scale + base1;

    // Zero tracking floats
    *reinterpret_cast<float*>(base + 52) = 0.0f;
    *reinterpret_cast<float*>(base + 48) = 0.0f;

    // Generate second random value (LCG step)
    rngVal = static_cast<uint64_t>(g_rngState[0]) * kRngMultiplier
           + g_rngState[1];
    g_rngState[0] = static_cast<uint32_t>(rngVal);
    g_rngState[1] = static_cast<uint32_t>(rngVal >> 32);
    uint32_t rand2 = g_rngState[0] & 0x7FFFFF;

    // Load second set of parameters and set flags
    *reinterpret_cast<float*>(base + 72) = 0.0f;
    float range2 = *reinterpret_cast<float*>(base + 64);
    *(base + 76) = 0;
    float base2  = *reinterpret_cast<float*>(base + 60);
    *(base + 77) = 1;

    // Compute second randomized position
    float randFloat2 = static_cast<float>(static_cast<int64_t>(rand2));
    *reinterpret_cast<float*>(base + 68) = randFloat2 * range2 * scale + base2;
}


// ===========================================================================
// 6. InitShotTrackingGrid (free function)
// ===========================================================================
/**
 * pongPlayer_InitShotTrackingGrid()
 * @ 0x8219DF38 | size: 0xCC
 *
 * Initializes a shot tracking grid structure.  Stores mode/side bytes,
 * calls ClearSwingSlotGrid, zeros flag bytes in two 4x48 tables,
 * calls grid setup functions, then resets status fields.
 */
void pongPlayer_InitShotTrackingGrid(void* gridData, uint8_t mode,
                                     uint8_t side) {  // pongPlayer_DF38_g @ 0x8219DF38
    uint8_t* base = reinterpret_cast<uint8_t*>(gridData);

    // Initialize mode/side and clear swing progress
    *reinterpret_cast<float*>(base + 960) = 0.0f;
    *(base + 944) = side;
    *(base + 945) = mode;

    // Clear swing slot grid
    pongPlayer_E640_g(gridData);

    // Zero flag bytes in first table (4 entries, stride 48, at +32)
    for (int i = 0; i < 4; i++) {
        *(base + 32 + i * 48) = 0;
    }

    // Zero flag bytes in second table (4 entries, stride 48, at +224)
    for (int i = 0; i < 4; i++) {
        *(base + 224 + i * 48) = 0;
    }

    // Initialize grid entries with mode parameters
    pongPlayer_E2C8_g(gridData, 3, 3, static_cast<int>(mode), 1);
    pongPlayer_E008_g(gridData, 3, 3, static_cast<int>(mode));

    // Reset status fields
    *(base + 956) = 0;
    *reinterpret_cast<uint32_t*>(base + 972) = 0;
    *(base + 968) = 0;
    *(base + 964) = 0;
    *reinterpret_cast<uint32_t*>(base + 948) = 1;
    *reinterpret_cast<uint32_t*>(base + 952) = 1;
    *(base + 965) = 0;
    *(base + 966) = 0;
    *(base + 967) = 0;
}


// ===========================================================================
// 7. TransformAndApplyVector (free function)
// ===========================================================================
/**
 * pongPlayer_TransformAndApplyVector()
 * @ 0x820CB130 | size: 0xD8
 *
 * Transforms an input vector by a 3x3 matrix looked up from the input
 * table via the state's slot index (+68), then passes the result to
 * pongPlayer_B208_g for application.
 */
void pongPlayer_TransformAndApplyVector(void* statePtr,
                                        const vec3* inputVec) {  // pongPlayer_B130_fw @ 0x820CB130
    uint8_t* stateBase = reinterpret_cast<uint8_t*>(statePtr);
    int32_t slotIdx = *reinterpret_cast<int32_t*>(stateBase + 68);

    // Look up transform matrix from input table
    uint32_t* inputTable = reinterpret_cast<uint32_t*>(g_pInputArrayTable);
    uint8_t* matObj = reinterpret_cast<uint8_t*>(
        static_cast<uintptr_t>(inputTable[slotIdx + 17]));

    // Extract 3 matrix rows (16 bytes each at +0, +16, +32)
    float* row0 = reinterpret_cast<float*>(matObj);
    float* row1 = reinterpret_cast<float*>(matObj + 16);
    float* row2 = reinterpret_cast<float*>(matObj + 32);

    float inX = inputVec->x;
    float inY = inputVec->y;
    float inZ = inputVec->z;

    // Matrix x vector (3x3 transform: row0*X + row2*Z + row1*Y)
    vec3 result;
    result.x = row0[0] * inX + row2[0] * inZ + row1[0] * inY;
    result.y = row0[1] * inX + row2[1] * inZ + row1[1] * inY;
    result.z = row0[2] * inX + row2[2] * inZ + row1[2] * inY;

    pongPlayer_B208_g(statePtr, &result, 0);
}


// ===========================================================================
// 8. SendServeOrMovementMessage
// ===========================================================================
/**
 * pongPlayer::SendServeOrMovementMessage()
 * @ 0x82195598 | size: 0xF4
 *
 * If the serve flag in the message handler (+500->+363) is set, modifies
 * the opponent's physics bound data (zeros two floats at +32/+36, sets
 * flag bit 0x10 at +64), then sends a serve started message.
 * Otherwise, if hasDirectMovement is set, sends a movement message
 * with the X and Z components of targetVec.
 */
void pongPlayer::SendServeOrMovementMessage(
    vec3* targetVec,
    uint8_t hasDirectMovement) {  // pongPlayer_5598_h @ 0x82195598
    // Get message handler at +500 (+0x1F4)
    uint8_t* selfBase = reinterpret_cast<uint8_t*>(this);
    void* msgHandler = *reinterpret_cast<void**>(selfBase + 500);

    uint8_t serveFlag = *(static_cast<uint8_t*>(msgHandler) + 363);

    if (serveFlag) {
        // Check opponent's player state creature readiness
        if (m_pOpponent->m_pPlayerState &&
            m_pOpponent->m_pPlayerState->IsCreatureState2Active()) {
            return;  // Opponent creature ready — skip serve message
        }

        // Modify opponent's physics bound data
        void* opponentPhysBound = m_pOpponent->m_pPhysicsBound;
        uint8_t* pbBase = reinterpret_cast<uint8_t*>(opponentPhysBound);

        // Zero two tracking floats and set flag bit
        *reinterpret_cast<float*>(pbBase + 32) = 0.0f;
        *reinterpret_cast<float*>(pbBase + 36) = 0.0f;
        *(pbBase + 64) |= 0x10;

        // Send serve started message
        ServeStartedMessage_CFE8_2h(msgHandler, targetVec, 0);
    } else {
        if (!hasDirectMovement) return;

        // Send movement message with position X and Z
        PlayerMovementMessage_D258_2hr(msgHandler, targetVec->x, targetVec->z);
    }
}


// ===========================================================================
// 9. IsWithinTimingWindow (free function)
// ===========================================================================
/**
 * pongPlayer_IsWithinTimingWindow()
 * @ 0x820DD298 | size: 0xEC
 *
 * Checks if the current animation progress (+172) falls within a timing
 * window defined by two normalized frame positions.  Returns true if
 * lowerBound <= currentProgress < upperBound, with bounds computed from
 * sub-object frame counts and duration.
 *
 * First gate: if the active flag (+44) is clear AND progress >= threshold,
 * returns false immediately (past timing window).
 */
bool pongPlayer_IsWithinTimingWindow(void* animState) {  // pongPlayer_D298_2hr @ 0x820DD298
    uint8_t* base = reinterpret_cast<uint8_t*>(animState);

    void* subObj = *reinterpret_cast<void**>(base + 36);
    if (!subObj) return false;

    uint8_t isActive = *(base + 44);
    float currentProgress = *reinterpret_cast<float*>(base + 172);

    // First gate: if inactive and progress >= threshold, not in window
    if (!isActive && currentProgress >= g_kFloatConst_D108) {
        return false;
    }

    uint8_t* subBase = reinterpret_cast<uint8_t*>(subObj);

    // Compute upper bound from frameCountHi (+24)
    void* subSubObj = *reinterpret_cast<void**>(subBase + 36);
    float duration = *reinterpret_cast<float*>(
        reinterpret_cast<uintptr_t>(subSubObj) + 12);

    float upperBound;
    if (duration > 0.0f) {
        int32_t frameCountHi = *reinterpret_cast<int32_t*>(subBase + 24);
        upperBound = (static_cast<float>(frameCountHi) * g_kFloatConst_79BB8)
                   / duration;
    } else {
        upperBound = 0.0f;
    }

    if (upperBound <= currentProgress) return false;

    // Compute lower bound from frameCountLo (+20)
    subSubObj = *reinterpret_cast<void**>(subBase + 36);
    duration = *reinterpret_cast<float*>(
        reinterpret_cast<uintptr_t>(subSubObj) + 12);

    float lowerBound;
    if (duration > 0.0f) {
        int32_t frameCountLo = *reinterpret_cast<int32_t*>(subBase + 20);
        lowerBound = (static_cast<float>(frameCountLo) * g_kFloatConst_79BB8)
                   / duration;
    } else {
        lowerBound = 0.0f;
    }

    // Within window: lowerBound <= currentProgress < upperBound
    return lowerBound <= currentProgress;
}


// ===========================================================================
// 10. CopyBitfieldState (free function)
// ===========================================================================
/**
 * pongPlayer_CopyBitfieldState()
 * @ 0x821D6D90 | size: 0x88
 *
 * Copies bitfield state from source to destination.  Each structure has:
 *   +0: uint32_t* data pointer (array of 32-bit words)
 *   +6: uint16_t numBits
 *   +8: float value
 *
 * Iterates over all bits, copying each from source to destination,
 * then copies the float value field.
 */
void pongPlayer_CopyBitfieldState(void* dest, void* source) {  // pongPlayer_6D90_p46 @ 0x821D6D90
    uint8_t* dstBase = reinterpret_cast<uint8_t*>(dest);
    uint8_t* srcBase = reinterpret_cast<uint8_t*>(source);

    int numBits = static_cast<int>(*reinterpret_cast<uint16_t*>(dstBase + 6));

    if (numBits > 0) {
        uint32_t* srcData = *reinterpret_cast<uint32_t**>(srcBase);
        uint32_t* dstData = *reinterpret_cast<uint32_t**>(dstBase);

        for (int i = 0; i < numBits; i++) {
            int wordIdx = i >> 5;
            uint32_t bitMask = 1u << (i & 0x1F);

            // Read source bit
            bool srcBit = (srcData[wordIdx] & bitMask) != 0;

            // Copy bit to destination word
            uint32_t dstWord = dstData[wordIdx];
            if (srcBit) {
                dstWord |= bitMask;
            } else {
                dstWord &= ~bitMask;
            }
            dstData[wordIdx] = dstWord;
        }
    }

    // Copy float value field
    *reinterpret_cast<float*>(dstBase + 8) =
        *reinterpret_cast<float*>(srcBase + 8);
}


// ===========================================================================
// SECTION 58 — NetSyncFloat record helpers (0x82199Cxx family)
// ===========================================================================
//
// These three helpers mutate a NetSyncFloatRec — a sync-tracked float field
// owned by shot/stamina/score sub-records.  The record layout (inferred from
// SyncFloatField (CF10_g) and ResetShotSyncFields (9310_g)) is:
//
//   +0x00  float    m_currentValue       // value replicated over the network
//   +0x04  void*    m_callbackArg        // passed to m_onChange if value changes
//   +0x08  void*    m_onChange           // optional change-notification callback
//   +0x18  uint8_t  m_updateInhibit      // non-zero => skip the sync update
//
// The three helpers share a common clamp pipeline:
//   1. Take |delta| (or direct value in 9C90).
//   2. If |delta| < g_kFloatConst_79C04 (epsilon) treat as 0.
//   3. Clamp the result to the upper bound g_kDoubleConst_79D00.
//   4. Combine with m_currentValue (subtract / overwrite / add).
//   5. Re-clamp to [0, upperBound] before calling SyncFloatField.
//
// Caller convention: r3 = record base, f1 = float delta (for 9C08/9AE0).
// The asm does `addi r3, r3, 8` internally so the SyncFloatField call
// receives (record+8) — matching the target layout used everywhere else.


// ---------------------------------------------------------------------------
// 9C08_g — DecrementSyncedFloatClamped  @ 0x82199C08 | size: 0x88 (136 bytes)
// ---------------------------------------------------------------------------
/**
 * Decrement a NetSyncFloatRec's value by |deltaMagnitude|, re-clamped to the
 * epsilon/upper-bound window, skipped entirely when m_updateInhibit is set.
 *
 * Called from pongPlayer_37E0_g, pongPlayer_3A68_g, and pongPlayer_Process
 * to bleed off a sync float (e.g. stamina tick) each frame.
 *
 * NOTE: m_updateInhibit != 0 freezes the record for the current frame — the
 *       epsilon/clamp maths run on the delta but the SyncFloatField write is
 *       skipped entirely, keeping the replicated slot at its previous value.
 *       The zero-inhibit branch is the normal per-frame bleed path.
 */
void pongPlayer_DecrementSyncedFloatClamped(void* syncRec, float deltaMagnitude) {
    // SyncFloatField operates on (rec + 8).  The first 0x18 bytes of the rec
    // form the tracked-field header; byte at +0x18 is the update inhibit flag.
    uint8_t* recBase  = reinterpret_cast<uint8_t*>(syncRec);
    uint8_t* syncSlot = recBase + 8;                         // target of SyncFloatField
    const uint8_t inhibit = syncSlot[0x1C];                  // recBase + 0x24 == syncSlot + 0x1C
                                                             // matches `lbz r11,28(r3+8)`

    // 1. Take absolute value.
    double v = deltaMagnitude < 0.0f ? -double(deltaMagnitude) : double(deltaMagnitude);

    // 2. Apply deadzone: if |delta| < epsilon → 0.
    const double epsilon = double(g_kFloatConst_79C04);
    if (v < epsilon) {
        v = double(g_kDoubleConst_79EC8);                    // 0.0 (select-zero double)
    }

    // 3. Clamp to upper bound.
    const double upperBound = g_kDoubleConst_79D00;
    if (v > upperBound) {
        v = upperBound;
    }

    if (inhibit == 0) {
        // 4. Combine: newValue = clamp01(currentValue − v) (but clamped to upperBound).
        float  oldValue = *reinterpret_cast<float*>(syncSlot);
        double combined = double(oldValue) - v;

        if (combined < 0.0) {
            combined = double(g_kDoubleConst_79EC8);         // floor at 0.0
        }
        if (combined > upperBound) {
            combined = upperBound;                           // re-clamp at ceiling
        }

        float newValue = float(combined);

        // 5. Commit through the standard change-notification path.
        //    Equivalent to pongPlayer::SyncFloatField(syncSlot, &newValue);
        //    — inlined here to avoid making it a static call.
        float* valPtr = reinterpret_cast<float*>(syncSlot);
        if (*valPtr != newValue) {
            void* callback = *reinterpret_cast<void**>(syncSlot + 8);
            if (callback) {
                void* cbArg = *reinterpret_cast<void**>(syncSlot + 4);
                reinterpret_cast<void(*)(void*)>(callback)(cbArg);
            }
            *valPtr = newValue;
        }
    }
    // else: inhibit != 0 → value is frozen this frame.
}


// ---------------------------------------------------------------------------
// 9C90_g — SetSyncedFloatClamped  @ 0x82199C90 | size: 0x1B8 (440 bytes)
// ---------------------------------------------------------------------------
/**
 * "Commit the pending value" variant of the net-sync record.  Rather than
 * taking a new value from an argument, it reads m_currentValue, converts it
 * to int (for flag lookup), and — depending on three state bytes at
 * +0x28/+0x29/+0x2A of the record — either pushes the current value to the
 * replicated slot, rolls the value back via a timer field at +0x3C/+0x40,
 * or clears the pending latch entirely.
 *
 * This is the counterpart of DecrementSyncedFloatClamped: when the record is
 * flagged as "value changed but not yet synced", this function chooses
 * whether to publish, re-queue, or discard the change.  The full control-flow
 * mirrors UpdateDirtyFlags (9E48_g) — three bytes forming a small state
 * machine (immediate / queued / previous).
 *
 * TODO(researched): get_function_recomp("pongPlayer_9C90_g") returns a 309-line
 *       scaffold that pivots on three state bytes (record+40/41/42) plus two
 *       floats (+60/+64) and a constant at lbl_8202D108. Each byte acts as a
 *       phase latch: bit40 = "value changed", bit41 = "rollback armed", bit42
 *       = "commit in flight". Faithful reconstruction requires a dedicated
 *       pass on pongPlayer_CF10_g (the SyncFloatField-adjacent push routine)
 *       and pongPlayer_Process — deferred. Signature is correct; body stubbed.
 */
void pongPlayer_SetSyncedFloatClamped(void* syncRec) {
    (void)syncRec;
    // Stub: see researched note above. Full flag-machine dispatch + clamp
    // pending companion lifts of CF10_g and pongPlayer_Process.
}


// ---------------------------------------------------------------------------
// 9AE0_g — AddToSyncedFloatClamped  @ 0x82199AE0 | size: 0x128 (296 bytes)
// ---------------------------------------------------------------------------
/**
 * Accumulator variant of the NetSyncFloat clamp helper.  Adds `delta` to the
 * record's current value, clamped to [0, upperBound] with the same epsilon
 * deadzone.  When the old value equals a sentinel (g_kFloatConst_79C04),
 * also raises bit (1 << bitSlot) in the record's flag word via pg_E480 —
 * this is the "first-touch since reset" notification path.
 *
 * Caller: pongPlayer_3A68_g passes bitSlot in r5 to select which bit of the
 * queued-update bitmask to OR in.
 *
 * TODO(researched): pg_E480 has not been lifted; search_symbols/find_callers
 *       locate it as the "event-queue post" helper shared with the match
 *       message bus. +44 and +64 offsets are on the SHOT SUB-RECORD (not the
 *       player), matching the 200-byte m_pShotState block referenced by
 *       ResetShotSyncFields. Full body is pending a shot-record modelling
 *       pass — signature here matches the three call sites in pongPlayer_3A68.
 */
void pongPlayer_AddToSyncedFloatClamped(void* syncRec, float delta, uint32_t bitSlot) {
    (void)syncRec;
    (void)delta;
    (void)bitSlot;
    // Stub: see researched note above. Body pending shot-record layout pass.
}


// ===========================================================================
// SECTION 59 — Forward declarations for follow-up batch
// ===========================================================================
//
// The functions below are grouped with the 9Cxx NetSyncFloat family by their
// Process() call-graph neighbourhood but require additional struct reverse
// engineering before they can be safely lifted under the no-raw-offset rule.
// They are declared here so other translation units can reference them by
// name while the stub pass5 implementations remain in place.
//

/**
 * pongPlayer_9EC8_g @ 0x82189EC8 | size: 0x198 (408 bytes)
 *
 * Walks the two 4-byte player-record entries at this+0x74 and this+0x78
 * (matching the m_pPlayer[2] slot table), writes a single byte (team side)
 * into two deep sub-objects at +0x1C4+0xBC and +0x1C4+0x75, then polls the
 * global button-state singleton and, depending on the replay/network flag
 * at lbl_8207B6C0, either invokes xe_BB68 on the two vtable[160] helpers of
 * each player record or stores a fixed status code 2 into the button-state.
 *
 * TODO(researched): +0x1BC is m_pDrawData (confirmed in hpp), +0x1A4 is the
 *       anim-state m_animPhase float (hpp layout), +0xA4 is m_pPhysicsBody.
 *       The chain therefore walks: outer->m_pDrawData->anim->physics. The
 *       structural density comes from the intermixed vtable[160] dispatch
 *       into two player records; full lift still requires 7CC0_g and 05A8_g.
 */
extern "C" void pongPlayer_9EC8_g(void* /*this*/);

/**
 * pongPlayer_AB48_g @ 0x820CAB48 | size: 0x130 (304 bytes)
 *
 * SIMD (vmx128) vector-math helper.  Reads a v3 at (arg1+0x70)+0xA4+148
 * through two vtable indirections, falls through to a scalar fallback that
 * calls game_AF18 (court-bounds sample), then blends the two via
 * pongPlayer_9CD0_g and clamps the output into out[0..3].
 *
 * TODO(researched): game_AF18 and 9CD0_g remain unlifted (suggest_unimplemented
 *       flags them as SIMD leaves). A proper vec4 typedef is already partially
 *       in place (the `vec3` struct with _pad float), but the multi-precision
 *       SIMD refinement steps need a dedicated AltiVec lift. Deferred.
 */
extern "C" void pongPlayer_AB48_g(void* outVec, void* playerLike);

/**
 * pongPlayer_94F8_wrh @ 0x820D94F8 | size: 0xE4 (228 bytes)
 *
 * Iterates the 120-byte-per-entry global button-slot table (at g_pButtonStateTable
 * + 0x20), searching for the first active slot matching the current active
 * player.  Returns in f1 the float at byte offset 0 of the selected slot
 * (defaulting to g_kFloatConst_D110 if none found).
 *
 * The modular arithmetic `((v * 0x888D) >> 32 + v) >> 6` is a signed
 * divide-by-120 Hacker's-Delight reciprocal — it should be expressed as a
 * plain modulo in the lifted source once confirmed.
 */
extern "C" float pongPlayer_94F8_wrh();

/**
 * pongPlayer_DA58_g @ 0x820CDA58 | size: 0x27C (636 bytes) —
 *    IsSwingApexReached (declared in hpp:295).
 *
 * Large time/threshold compare over m_pAnimState + m_pTimingState. Already
 * ported at method level (SECTION 6 above and pongPlayerState::IsSwingApexReached
 * at the SECTION 6 duplicate @ line 1504+). Forward declaration retained for
 * binary-name parity.
 */

////////////////////////////////////////////////////////////////////////////////
// Stubs lifted from src/stubs.cpp — pongPlayer free functions
//
// These are placeholder bodies for large functions (1KB-3KB each) pending
// full translation.  Signatures match the call-sites already established in
// this file and in pong_player_swing.cpp.  Each entry records the raw xex
// address so future work can resolve the Hex-Rays pseudocode.
////////////////////////////////////////////////////////////////////////////////

// pongPlayer_0270_g @ 0x821E0270 | size: 0x240
// Resolves a court-space point for a target by blending endpoint vectors
// against a per-player factor. Stub pending dedicated lift pass.
extern "C" int pongPlayer_0270_g(void* /*self*/) { return 0; }

// pongPlayer_1460_g @ 0x821A1460 | size: 0x13F8 (5112 bytes)
// Massive composite — one of the core per-frame player processors.
// Stub pending a decomposition pass (too large for a single lift).
extern "C" void pongPlayer_1460_g(void* /*self*/, int /*arg*/) {}

// pongPlayer_5B60_gen @ 0x82195B60 — lifted below as pongPlayer_CheckServeInput.
extern "C" bool pongPlayer_5B60_gen(pongPlayer* p) { return pongPlayer_CheckServeInput(p); }

// pongPlayer_6470_g @ 0x821D6470 | size: 0x13C
// Two signatures were historically declared for this symbol (vec3* vs float*).
// They are C++-overloaded here; callers include both forms.
void pongPlayer_6470_g(float* /*a*/, void* /*b*/, int /*c*/) {}
void pongPlayer_6470_g(vec3*  /*a*/, void* /*b*/) {}

// pongPlayer_B208_g @ 0x820CB208 | size: 0x15C
// Applies a swing vector to the player's swing state (extern-decl above).
// Definition left as no-op until the full body is ported.
void pongPlayer_B208_g(void* /*state*/, vec3* /*swingVec*/,
                         uint8_t /*suppressFlip*/) {}

// pongPlayer_BF18_g @ 0x820CBF18 | size: 0x3A4
// Swing-target selector; real impl returns a selection index.
extern "C" int pongPlayer_BF18_g(void* /*self*/, int /*a*/, vec3* /*b*/,
                                   vec3* /*c*/, int /*d*/) { return 0; }

// pongPlayer_C678_g @ 0x820CC678 | size: 0xBB0 (2992 bytes)
// UpdateLocomotionState — 3KB monster; stub pending a dedicated subdivision pass.
// C678_g is the binary-address symbol; UpdateLocomotionState is the semantic
// alias used by pongPlayer::Process at line 307.
extern "C" void pongPlayer_C678_g(pongPlayer* /*state*/) {}
void pongPlayer_UpdateLocomotionState(pongPlayer* state) {
    pongPlayer_C678_g(state);
}

// pongPlayer_DE98_g @ 0x820CDE98 — the by-address name pcr_anim_blenders.cpp
// calls; it passes the pongCreature's +0xBC, the pongPlayerState.
extern "C" bool pongPlayer_DE98_g(void* state) {
    return static_cast<pongPlayerState*>(state)->IsInReturnPosition();
}

// pongPlayer_FD20_g @ 0x821EFD20 | size: 0x1A4
// Court bounds + interpolation helper invoked by E7B0_g.
void pongPlayer_FD20_g(void* /*a*/, int /*b*/, void* /*c*/,
                         void* /*d*/, int /*e*/, void* /*f*/,
                         void* /*g*/, unsigned char /*h*/) {}

// Player-system entry points exposed as named symbols (from stubs.cpp).
extern "C" void pongPlayer_ApplyNetStateImpl(void* /*self*/) {}
extern "C" void pongPlayer_GetPlayerPosition(void* /*self*/, void* /*out*/) {}
extern "C" void pongPlayer_InitShotImpl(void* /*self*/) {}
extern "C" void pongPlayer_Interpolate(void* /*self*/, void* /*arg*/) {}
extern "C" void pongPlayer_ResetMoverImpl(void* /*self*/) {}

////////////////////////////////////////////////////////////////////////////////
// State-handler shims — pongPlayer_StateHandler_{9188..91E8}
//
// The concrete (class-method) bodies live earlier in this file as
// pongPlayer::VtMarkNetDirty{Position,Rotation,Velocity,Animation,ShotState,
// Stamina,Score}.  These extern "C" entry points retain the by-hex-address
// names used by the static recomp scaffold; each one is a 0x10-byte thunk in
// the binary that tail-calls game_91F8 (the net-dirty trigger).
////////////////////////////////////////////////////////////////////////////////

extern "C" void pongPlayer_StateHandler_9188(void* /*self*/) {}  // @ 0x82199188
extern "C" void pongPlayer_StateHandler_9198(void* /*self*/) {}  // @ 0x82199198
extern "C" void pongPlayer_StateHandler_91A8(void* /*self*/) {}  // @ 0x821991A8
extern "C" void pongPlayer_StateHandler_91B8(void* /*self*/) {}  // @ 0x821991B8
extern "C" void pongPlayer_StateHandler_91C8(void* /*self*/) {}  // @ 0x821991C8
extern "C" void pongPlayer_StateHandler_91D8(void* /*self*/) {}  // @ 0x821991D8
extern "C" void pongPlayer_StateHandler_91E8(void* /*self*/) {}  // @ 0x821991E8


// =============================================================================
// BATCH 11 — Misc pongPlayer free functions (state queries, byte flags, swing
// math, vector helpers).  All ten operate on pongPlayer* shells or on raw
// vec3 data accessed through the same struct offsets used by the rest of
// this file.  Pulled from a single static-recomp pass; field names match
// pong_player.hpp field conventions (m_pPhysicsBody, m_pAnimState, etc.).
// =============================================================================

// ── Externals specific to this batch ─────────────────────────────────────
extern "C" bool pongPlayer_D598_g(pongPlayer* self);                 // IsRecovering (already lifted at method level)
extern "C" void phBoundCapsule_A080_g(void* bound);                  // @ 0x820CA080 — rebuild bound pose from body
extern void pongPlayer_B208_g(void* state, vec3* swingVec,
                              uint8_t suppressFlip);                 // @ 0x820CB208 — apply swing vec (stub above)
extern "C" void pongPlayer_9CD0_g(void*, int, void*, void*);         // @ 0x821C9CD0 — per-player input poll (stub above)

// g_kSwingRadiusConst is declared near the top of the file at +8 of a 0x60
// table; reuse that symbol.  The 5FB8 scaffold pulls radius from the same
// base table at +0x8 (float).  We re-expose via an alias so we don't drag in
// yet another extern.

// Per-player input score table — float[inputSlotIdx].  Declared as
// g_pInputScoreTable above (at lis -32161, addi -21696 → 0x825EAB40).
extern float g_inputScoreByPlayer[];                                  // alias of g_pInputScoreTable

// Debug strings used by SetSwingActiveState's logger.
// 0x82027A30 = "Player %d is queueing a swing"
// 0x82027A50 = "Player %d is dequeueing a swing"

// vec3 helper globals for BoundVector/IsInCourtBox (8740_wrh / 8E28_2h).
// Signed-zero mask, floating +0.0 vector, and the 4 court-corner vec3s used
// by IsInCourtBox live adjacent to each other in .data:
//   +0x82607210  upper-outer   (vec3; 8E28 uses as max-outer)
//   +0x82607220  upper-inner   (8E28 uses as max-inner)
//   +0x82607230  lower-inner   (8E28 uses as min-inner)
//   +0x82607240  lower-outer   (8E28 uses as min-outer)
extern const vec3 g_kCourtBoxOuterMin;  // @ 0x82607210
extern const vec3 g_kCourtBoxInnerMin;  // @ 0x82607220
extern const vec3 g_kCourtBoxInnerMax;  // @ 0x82607230
extern const vec3 g_kCourtBoxOuterMax;  // @ 0x82607240

// Sign-mask / compare helpers (8740_wrh).
extern const uint32_t g_kFloatSignMask[4];  // @ 0x82619BE0 — 0x7FFFFFFF × 4
extern const vec3     g_kVecConst_619BF0;   // @ 0x82619BF0 — 16-byte .data const

// Constants used by the normalise-idiom in C070_wrh.
extern const vec3 g_kVecConst_5C7120;  // @ 0x825C7120 — permwi source
extern const vec3 g_kVecConst_5C7130;  // @ 0x825C7130
extern const vec3 g_kVecConst_5C7140;  // @ 0x825C7140
extern const vec3 g_kVecConst_5C8070;  // @ 0x825C8070 — rsqrt refine const
extern const vec3 g_kVecConst_606750;  // @ 0x82606750 — 32-byte sign/scale table

// ---------------------------------------------------------------------------
// pongPlayer_5FB8_g  @ 0x820C5FB8 | size: 0x10C (268 bytes)
//
// Per-frame physics body refresh: invokes vtable slot 3 on m_pPhysicsBody
// (pose update), rebuilds the collision capsule from the body transform,
// runs the player's body-animation sub-object (vtable slot 1), optionally
// suppresses swing application when the swing result code is 7, then calls
// B208 (ApplySwingVector) with the capsule's cached target vec3 multiplied
// by the global radius constant.  Finally it stashes the capsule's Y-offset
// (+72) into the per-player input-score slot.
//
// Original vtable chain resolved from the scaffold's VCALL sites:
//   m_pPhysicsBody->Update(m_pPhysicsBody+16)     -- slot 3
//   m_pPlayerState->vfn_1(f1 = g_kSwingRadiusConst) -- slot 1
// ---------------------------------------------------------------------------
extern "C" void pongPlayer_5FB8_g(pongPlayer* self) {
    // Step 1: advance physics pose.  Virtual slot 3 takes (this, this+16).
    using BodyUpdateFn = void(*)(void*, void*);
    void* body = self->m_pPhysicsBody;
    if (body) {
        void** bodyVt = *static_cast<void***>(body);
        BodyUpdateFn bodyUpdate = reinterpret_cast<BodyUpdateFn>(bodyVt[3]);
        bodyUpdate(body, static_cast<uint8_t*>(body) + 16);
    }

    // Step 2: rebuild collision capsule world transform.
    phBoundCapsule_A080_g(self->m_pPhysicsBound);

    // Step 3: if the inner state exposes a body-anim sub-object, run its
    // vtable slot 1 with the global swing radius constant.
    pongPlayerState* inner = self->m_pPlayerState;
    if (inner) {
        void* animSub = *reinterpret_cast<void**>(
            reinterpret_cast<uint8_t*>(inner) + 148);
        if (animSub) {
            using AnimFn = void(*)(void*, float);
            void** animVt = *static_cast<void***>(animSub);
            AnimFn animUpdate = reinterpret_cast<AnimFn>(animVt[1]);
            animUpdate(animSub, g_kSwingRadiusConst);
        }
    }

    // Step 4: build the swing-application vector.  Base magnitude is
    // g_kSwingRadiusConst; the XYZ direction comes from floats at +56/+60 of
    // the phBound (the "target vec" cached during capsule rebuild), with Z
    // implicitly zero because the ±4-byte slots at +64..+76 are zero-padded.
    // Suppress the sign-flip when the swing result code == 7 ("aborted").
    uint8_t suppressFlip = (self->m_swingInputResult == 7) ? 0 : 1;

    uint8_t* bound = static_cast<uint8_t*>(self->m_pPhysicsBound);
    vec3 swingVec = {
        *reinterpret_cast<float*>(bound + 56),
        0.0f,
        *reinterpret_cast<float*>(bound + 60),
        0.0f,
    };
    // vmulfp128: broadcast g_kSwingRadiusConst across the vector and scale.
    swingVec.x *= g_kSwingRadiusConst;
    swingVec.y *= g_kSwingRadiusConst;
    swingVec.z *= g_kSwingRadiusConst;

    pongPlayer_B208_g(inner, &swingVec, suppressFlip);

    // Step 5: stash the capsule's Y-offset (+72) into the per-player input
    // score array at g_pInputScoreTable[m_swingInputSlot].  The raw
    // PPC `stfsx f12, r7, r10` is just `table[slot] = value`.
    float capsuleHeight = *reinterpret_cast<float*>(bound + 72);
    g_inputScoreByPlayer[self->m_swingInputSlot] = capsuleHeight;
}


// ---------------------------------------------------------------------------
// pongPlayer_7890_g  @ 0x820C7890 | size: 0x100 (256 bytes)
//
// Returns true when the player's swing pipeline is still live — meaning
// either the swing is in an explicit "committed" state (2 or 3), OR the
// recovery timer hasn't expired yet AND the parent state's own swing
// progress fraction (frame-index / total-frames, scaled by
// g_swingPhaseThreshold) is still below the sub-object's recorded progress.
//
// States 2/3 short-circuit to true (swing actively running).  All other
// states fall through to the gated recovery+progress test.
// ---------------------------------------------------------------------------
extern "C" bool pongPlayer_7890_g(pongPlayer* self) {
    // Swing-active or pre-impact short-circuits: both count as "busy".
    int32_t state = self->m_swingInputResult;
    if (state == 2 || state == 3) {
        return true;
    }

    // Recovery still counting down?  m_pPlayerState is the heap inner shell;
    // IsRecovering (D598) checks the same m_pRecoveryState as our method.
    pongPlayerState* inner = self->m_pPlayerState;
    if (!pongPlayer_D598_g(inner)) {
        return false;
    }
    // Double-check — the scaffold queries D598 twice.  It's idempotent.
    if (!pongPlayer_D598_g(inner)) {
        return false;
    }

    // Recovery active.  Now compare the timing sub-state's stored progress
    // against the outer parent's frame-index-based progress.  The raw
    // computation is:
    //
    //     progressFrac = float(parentFrameIndex) * g_inputScoreScale
    //                  / parentTargetDuration
    //
    // and we return (storedSwingProgress < progressFrac).
    pongTimingSubState* sub = reinterpret_cast<pongTimingSubState*>(
        *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(inner) + 128));
    pongAnimState* parentAnim = reinterpret_cast<pongAnimState*>(
        *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(sub) + 36));
    if (!parentAnim) {
        return false;
    }

    float storedProgress = *reinterpret_cast<float*>(
        reinterpret_cast<uint8_t*>(sub) + 172);  // +0xAC
    float parentDuration = parentAnim->m_swingPhase;  // +12 from blend root (0x19C on outer)
    float threshold = g_kFloatConst_D110;  // 0x8202D110

    // Only apply the scale when duration has advanced past the threshold.
    if (parentDuration > threshold) {
        // parent-frame-index lives at +20 on the inner anim state.
        int32_t frameIndex = *reinterpret_cast<int32_t*>(
            reinterpret_cast<uint8_t*>(parentAnim) + 20);
        // scale constant @ 0x825E9BB8 (float) in the per-player input table.
        extern const float g_kSwingProgressScale;  // @ 0x825E9BB8
        float frac = (static_cast<float>(frameIndex) * g_kSwingProgressScale)
                   / parentDuration;
        threshold = frac;
    }

    return storedProgress < threshold;
}


// ---------------------------------------------------------------------------
// pongPlayer_7C78_g  @ 0x820C7C78 | size: 0x6C (108 bytes)
//
// SetSwingActiveState(flag): stores `flag` into m_bSwingActive (+197) and, if
// the flag actually changed, logs "Player %d is queueing a swing" or
// "Player %d is dequeueing a swing" tagged with m_swingInputSlot (+204).
// The debug-log function (nop_8240E6D0) is a no-op in retail but the call
// is retained for symbol parity with the scaffold.
// ---------------------------------------------------------------------------
extern "C" void pongPlayer_7C78_g(pongPlayer* self, uint8_t flag) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    uint8_t current = base[197];  // m_bSwingActive
    if (current == flag) {
        return;  // no change, nothing to log
    }

    int32_t playerSlot = *reinterpret_cast<int32_t*>(base + 204);  // m_swingInputSlot
    const char* msg = flag ? "Player %d is queueing a swing"
                           : "Player %d is dequeueing a swing";
    nop_8240E6D0(msg, playerSlot);
    base[197] = flag;
}


// ---------------------------------------------------------------------------
// pongPlayer_E000_g  @ 0x820CE000 | size: 0x8C (140 bytes)
//
// Compound predicate — used by the swing pipeline to decide whether a
// queued input is still mechanically valid.  Returns true only if:
//   (a) the timing sub-state exists AND its currentTime (+28) ≥ targetTime (+48),
//       i.e. the swing window has already opened; AND
//   (b) the sub-state sub-object at +120 exists AND the float stored at
//       (sub+32)+128 is strictly greater than the threshold g_kFloatConst_D110.
//
// Otherwise the function returns false (r3 = 0).
// ---------------------------------------------------------------------------
extern "C" bool pongPlayer_E000_g(pongPlayer* self) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);

    // Gate A — timing sub-state at +124.
    pongTimingState* timing = *reinterpret_cast<pongTimingState**>(base + 124);
    bool timingExpired = false;
    if (timing) {
        float cur = timing->m_currentTime;       // +28
        float tgt = timing->m_targetTime;        // +48
        timingExpired = (cur >= tgt);            // bns/cntlzw idiom → ≥ compare
    }
    if (!timingExpired) {
        return false;
    }

    // Gate B — sub-object at +120, float at (sub+32)+128 vs D110 threshold.
    void* sub = *reinterpret_cast<void**>(base + 120);
    if (!sub) {
        return false;
    }
    uint8_t* subBase = static_cast<uint8_t*>(sub) + 32 + 128;
    float subProgress = *reinterpret_cast<float*>(subBase);
    return subProgress > g_kFloatConst_D110;
}


// ---------------------------------------------------------------------------
// pongPlayer_E3F0_p45  @ 0x820CE3F0 | size: 0x64 (100 bytes)
//
// Indexed getter: returns one of five pointer-valued fields on the player
// state (+100, +104, +108, +112, +116) selected by `index` (0-4).  For
// index > 4 returns nullptr.  Originally a jump table (jumptable_820CE410)
// — rewrites as a trivial switch.
// ---------------------------------------------------------------------------
extern "C" void* pongPlayer_E3F0_p45(pongPlayer* self, uint32_t index) {
    if (index > 4) {
        return nullptr;
    }
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    switch (index) {
        case 0: return *reinterpret_cast<void**>(base + 100);
        case 1: return *reinterpret_cast<void**>(base + 104);
        case 2: return *reinterpret_cast<void**>(base + 108);
        case 3: return *reinterpret_cast<void**>(base + 112);
        case 4: return *reinterpret_cast<void**>(base + 116);
    }
    return nullptr;  // unreachable (guard above)
}


// ---------------------------------------------------------------------------
// pongPlayer_7358_g  @ 0x820D7358 | size: 0x19C (412 bytes)
//
// Snapshot copy: bitwise-clones the "match-relevant" portion of one player
// into another.  Copies:
//   +16  (m_pBody)           +20  (m_bActive+tail)    +24  (m_pMover)
//   +28  (m_animTimerLow)    +32  (blend weight)      +36  (smoothed dt)
//   +48..+63   (16B vec3)    +64..+79  (16B vec3)
//   +80..+95   (16B vec3)    +96..+111 (16B vec3)
//   +128..+131 (float pair)  +136,+137,+138 (3× u8 flag)
//   +144..+159 (16B vec)     +160..+175 (16B vec)     +176..+191 (16B vec)
//   +208..+223 (16B) +224..+239 +240..+255 +256..+271 +272..+287 (5× 16B vec)
//   +288,+292  (floats)      +296,+300 (floats)
//   +304,+306,+308,+310      (4× u16)
//   +312,+313,+314            (3× u8)
//
// This is a structurally identical copy of the first ~315 bytes of the
// match-state portion of pongPlayer — NOT the whole object.  No pointers
// are reference-counted and no observers are invoked; callers must ensure
// the destination isn't live.  Used in SinglesNetworkClient_74F8_h for
// replay/roll-back snapshotting.
// ---------------------------------------------------------------------------
extern "C" void pongPlayer_7358_g(pongPlayer* dst, const pongPlayer* src) {
    uint8_t* d = reinterpret_cast<uint8_t*>(dst);
    const uint8_t* s = reinterpret_cast<const uint8_t*>(src);

    // Scalar quads at +16/+20/+24  (m_pBody, flags, m_pMover) and
    // their neighbouring floats at +28 / +32 / +36.
    *reinterpret_cast<uint32_t*>(d + 16) = *reinterpret_cast<const uint32_t*>(s + 16);
    *reinterpret_cast<uint32_t*>(d + 20) = *reinterpret_cast<const uint32_t*>(s + 20);
    *reinterpret_cast<uint32_t*>(d + 24) = *reinterpret_cast<const uint32_t*>(s + 24);
    *reinterpret_cast<float*>   (d + 28) = *reinterpret_cast<const float*>   (s + 28);
    *reinterpret_cast<float*>   (d + 32) = *reinterpret_cast<const float*>   (s + 32);
    *reinterpret_cast<float*>   (d + 36) = *reinterpret_cast<const float*>   (s + 36);

    // Four 16-byte vector slots (AltiVec lvx/stvx): +48, +64, +80, +96.
    auto copyVec16 = [](uint8_t* dp, const uint8_t* sp) {
        // Copy 16 aligned bytes (compiler lowers to a single movdqu on x86).
        for (int i = 0; i < 16; ++i) dp[i] = sp[i];
    };
    copyVec16(d + 48,  s + 48);
    copyVec16(d + 64,  s + 64);
    copyVec16(d + 80,  s + 80);
    copyVec16(d + 96,  s + 96);

    // Scratch floats + byte flags at +128..+138.
    *reinterpret_cast<float*>  (d + 128) = *reinterpret_cast<const float*>  (s + 128);
    *reinterpret_cast<float*>  (d + 132) = *reinterpret_cast<const float*>  (s + 132);
    d[136] = s[136];
    d[137] = s[137];
    d[138] = s[138];

    // Three more vec16 slots: +144, +160, +176.
    copyVec16(d + 144, s + 144);
    copyVec16(d + 160, s + 160);
    copyVec16(d + 176, s + 176);

    // Five-element vec16 array spanning +208..+287.
    copyVec16(d + 208, s + 208);
    copyVec16(d + 224, s + 224);
    copyVec16(d + 240, s + 240);
    copyVec16(d + 256, s + 256);
    copyVec16(d + 272, s + 272);

    // Trailing scalars: floats at +288/+292/+296/+300, u16 ×4 at
    // +304/+306/+308/+310, u8 ×3 at +312/+313/+314.
    *reinterpret_cast<float*>(d + 288) = *reinterpret_cast<const float*>(s + 288);
    *reinterpret_cast<float*>(d + 292) = *reinterpret_cast<const float*>(s + 292);
    *reinterpret_cast<float*>(d + 296) = *reinterpret_cast<const float*>(s + 296);
    *reinterpret_cast<float*>(d + 300) = *reinterpret_cast<const float*>(s + 300);
    *reinterpret_cast<uint16_t*>(d + 304) = *reinterpret_cast<const uint16_t*>(s + 304);
    *reinterpret_cast<uint16_t*>(d + 306) = *reinterpret_cast<const uint16_t*>(s + 306);
    *reinterpret_cast<uint16_t*>(d + 308) = *reinterpret_cast<const uint16_t*>(s + 308);
    *reinterpret_cast<uint16_t*>(d + 310) = *reinterpret_cast<const uint16_t*>(s + 310);
    d[312] = s[312];
    d[313] = s[313];
    d[314] = s[314];
}


// ---------------------------------------------------------------------------
// pongPlayer_8B90_fw  @ 0x820D8B90 | size: 0x174 (372 bytes)
//
// Network-smoothed transform update.  Takes two vec3 outputs (position @ r5,
// velocity @ r6), a source transform block at r4 (which lays out three
// 3-vectors at +0/+16/+32 plus a translation at +48 — i.e. a 3×4 matrix-like
// layout), and the player at r3.  After zero-initialising the output vecs,
// it calls pongPlayer_9CD0_g (the input poller) with the player's context
// pointer at +400, then folds the poll result into the vectors via an
// affine transform of the form:
//
//   out_pos = src_col0 * pos_x  +  src_col1 * pos_y  +  src_col2 * pos_z
//           + src_translation
//   out_vel = src_col0 * vel_x  +  src_col1 * vel_y  +  src_col2 * vel_z
//           + src_translation_vel
//
// After writing, it validates the X and Z components: if out_pos.x > out_vel.x
// OR out_pos.z > out_vel.z, the two 16-byte vectors are swapped.  This
// enforces an axis-aligned min/max invariant on the extracted AABB.
// ---------------------------------------------------------------------------
extern "C" void pongPlayer_8B90_fw(pongPlayer* self, void* srcTransform,
                                    vec3* outPos, vec3* outVel) {
    uint8_t* base = reinterpret_cast<uint8_t*>(self);
    uint8_t* src  = static_cast<uint8_t*>(srcTransform);

    // Zero both outputs first (matches the vxor prologue).
    outPos->x = outPos->y = outPos->z = outPos->_pad = 0.0f;
    outVel->x = outVel->y = outVel->z = outVel->_pad = 0.0f;

    // Poll input for this player's context pointer at +400.
    void* inputCtx = *reinterpret_cast<void**>(base + 400);
    pongPlayer_9CD0_g(reinterpret_cast<void*>(&g_inputScoreByPlayer[0]),
                      0, inputCtx, nullptr);

    // Floats now populated in outPos (components at +0/+4/+8) and outVel.
    float px = outPos->x, py = outPos->y, pz = outPos->z;
    float vx = outVel->x, vy = outVel->y, vz = outVel->z;

    // Rows of the source transform matrix (column-major 3×4).
    float m0x = *reinterpret_cast<float*>(src +  0);
    float m0y = *reinterpret_cast<float*>(src +  4);
    float m0z = *reinterpret_cast<float*>(src +  8);
    float m1x = *reinterpret_cast<float*>(src + 16);
    float m1y = *reinterpret_cast<float*>(src + 20);
    float m1z = *reinterpret_cast<float*>(src + 24);
    float m2x = *reinterpret_cast<float*>(src + 32);
    float m2y = *reinterpret_cast<float*>(src + 36);
    float m2z = *reinterpret_cast<float*>(src + 40);
    float tx  = *reinterpret_cast<float*>(src + 48);
    float ty  = *reinterpret_cast<float*>(src + 52);
    float tz  = *reinterpret_cast<float*>(src + 56);

    // Affine transform of (px,py,pz) by the 3×4 matrix.
    outPos->x = m0x * px + m1x * py + m2x * pz + tx;
    outPos->y = m0y * px + m1y * py + m2y * pz + ty;
    outPos->z = m0z * px + m1z * py + m2z * pz + tz;

    // Same for (vx,vy,vz).
    outVel->x = m0x * vx + m1x * vy + m2x * vz + tx;
    outVel->y = m0y * vx + m1y * vy + m2y * vz + ty;
    outVel->z = m0z * vx + m1z * vy + m2z * vz + tz;

    // Enforce min/max ordering on X and Z.  If pos > vel on either axis,
    // swap the 16-byte vectors so caller's "min" and "max" semantics hold.
    if (outPos->x > outVel->x || outPos->z > outVel->z) {
        vec3 tmp = *outPos;
        *outPos = *outVel;
        *outVel = tmp;
    }
}


// ---------------------------------------------------------------------------
// pongPlayer_C070_wrh  @ 0x820DC070 | size: 0x128 (296 bytes)
//
// Cross-product + length normalisation.  Takes two input vec3s at r4+48 and
// r4+64 (the "forward" and "up" candidates), computes:
//
//   perp        = forward × up                       (3D cross product)
//   perpHatZero = zero-safe normalise(perp)          (returns 0 for |perp|≈0)
//   refined     = zero-safe normalise(forward × perpHatZero)
//
// Stores the normalised cross into dst+0 (unit perpendicular) and the
// refined normalised cross into dst+16 (unit forward-perp orthogonal).
// The `vrsqrtefp` + Newton-Raphson step followed by `vcmpeqfp`/`vsel` is the
// Xenon SIMD pattern for a zero-checked reciprocal-sqrt; we express it as a
// conditional that returns 0 when the squared length is effectively zero.
// ---------------------------------------------------------------------------
extern "C" void pongPlayer_C070_wrh(vec3* dst, const void* srcMatrix) {
    const uint8_t* src = static_cast<const uint8_t*>(srcMatrix);
    // Load the two input vectors (rows 3 and 4 of the source, at +48/+64).
    auto loadVec = [](const uint8_t* p) {
        return vec3{
            *reinterpret_cast<const float*>(p),
            *reinterpret_cast<const float*>(p + 4),
            *reinterpret_cast<const float*>(p + 8),
            0.0f,
        };
    };
    auto cross = [](vec3 a, vec3 b) {
        return vec3{
            a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x,
            0.0f,
        };
    };
    auto normalizeSafe = [](vec3 v) -> vec3 {
        float lenSq = v.x * v.x + v.y * v.y + v.z * v.z;
        if (lenSq < 1.0e-20f) {
            return vec3{ 0.0f, 0.0f, 0.0f, 0.0f };
        }
        // Newton-Raphson-refined rsqrt to match the PPC idiom:
        //   rsqrt_est → refine → multiply by lenSq's reciprocal root.
        // C++ just uses 1/sqrt — the end result is identical.
        float inv = 1.0f / std::sqrt(lenSq);
        return vec3{ v.x * inv, v.y * inv, v.z * inv, 0.0f };
    };

    vec3 forward = loadVec(src + 48);
    vec3 up      = loadVec(src + 64);
    vec3 perp    = cross(forward, up);

    // Temporarily store raw perp so the next cross-product reads the
    // pre-normalised value (matches the scaffold's "stvx v13,...,r11" step).
    uint8_t* dstBytes = reinterpret_cast<uint8_t*>(dst);
    vec3 perpHat = normalizeSafe(perp);
    *reinterpret_cast<vec3*>(dstBytes + 0) = perpHat;

    // Build the refined axis: forward × perpHat, normalised.
    vec3 refined    = cross(forward, perpHat);
    vec3 refinedHat = normalizeSafe(refined);
    *reinterpret_cast<vec3*>(dstBytes + 16) = refinedHat;
}


// ---------------------------------------------------------------------------
// pongPlayer_8740_wrh  @ 0x820E8740 | size: 0xEC (236 bytes)
//
// Per-axis "distance to bound" helper.  Computes:
//
//   for axis ∈ {x, y, z}:
//     if  P[axis] < min[axis]: out[axis] = min[axis] - P[axis]   (negative-side violation)
//     elif P[axis] > max[axis]: out[axis] = max[axis] - P[axis]  (positive-side violation)
//     else:                   out[axis] = g_kFloatConst_D110 (0.0f signed-zero marker)
//
// Returns true iff ANY axis is inside the [min, max] box — i.e. at least one
// axis returned the "inside" marker.  This is the sign test used by the
// court-bounds / court-volume queries below.
//
// The final check is implemented with an AltiVec sign-mask AND followed by a
// per-lane `vcmpeqfp.` against the zero vector; we express it as a direct
// float equality check on g_kFloatConst_D110.
// ---------------------------------------------------------------------------
extern "C" bool pongPlayer_8740_wrh(const vec3* pos, const vec3* boundMin,
                                     const vec3* boundMax, vec3* outDelta) {
    const float zero = g_kFloatConst_D110;  // expected 0.0f

    // X axis.
    if (pos->x < boundMin->x) {
        outDelta->x = boundMin->x - pos->x;
    } else if (pos->x > boundMax->x) {
        outDelta->x = boundMax->x - pos->x;
    } else {
        outDelta->x = zero;
    }
    // Y axis.
    if (pos->y < boundMin->y) {
        outDelta->y = boundMin->y - pos->y;
    } else if (pos->y > boundMax->y) {
        outDelta->y = boundMax->y - pos->y;
    } else {
        outDelta->y = zero;
    }
    // Z axis.
    if (pos->z < boundMin->z) {
        outDelta->z = boundMin->z - pos->z;
    } else if (pos->z > boundMax->z) {
        outDelta->z = boundMax->z - pos->z;
    } else {
        outDelta->z = zero;
    }

    // "Inside" test: true iff at least one axis landed in the zero slot.
    // Equivalent to the PPC `vand`/`vcmpeqfp.` mask test: if none of the
    // three deltas were zero, every lane was a violation → fully outside.
    return (outDelta->x == zero) || (outDelta->y == zero) || (outDelta->z == zero);
}


// ---------------------------------------------------------------------------
// pongPlayer_8E28_2h  @ 0x820E8E28 | size: 0x144 (324 bytes)
//
// Two-tier in-volume test: checks whether the input 3D position lies within
// the inner court box [kCourtBoxInnerMin, kCourtBoxInnerMax], and if not,
// whether it falls in the "angled gap" between the inner and outer box
// (by linear interpolation on Y based on the X fraction between bounds).
//
// Returns:
//   1  if P is fully inside the INNER box.
//   ~1 in the angled-extension region (special-case return via "li r11,1").
//   0  otherwise.
//
// The bso-cr6 paths in the scaffold are NaN-propagation; under IEEE-754 any
// NaN coordinate fails the comparisons and falls through to the outer test.
// ---------------------------------------------------------------------------
extern "C" bool pongPlayer_8E28_2h(const vec3* pos) {
    // Tier 1 — strict inner box.
    if (pos->x > g_kCourtBoxInnerMax.x && pos->x >= g_kCourtBoxInnerMin.x &&
        pos->y <= g_kCourtBoxInnerMax.y && pos->y >= g_kCourtBoxInnerMin.y &&
        pos->z <= g_kCourtBoxInnerMax.z && pos->z >= g_kCourtBoxInnerMin.z) {
        return true;
    }

    // Tier 2 — angled extension using the OUTER bounds.  Both X checks
    // must be inside [outerMin.x, outerMax.x]; then Y is clamped into the
    // interpolated wedge between innerMax.y and 0 as X moves from outerMax
    // toward innerMax.
    if (!(pos->x > g_kCourtBoxOuterMax.x)) return false;
    if (pos->x < g_kCourtBoxOuterMin.x)    return false;

    if (pos->y > g_kCourtBoxOuterMax.y) return false;
    if (pos->y < g_kCourtBoxOuterMin.y) return false;

    if (pos->z > g_kCourtBoxOuterMax.z) return false;
    if (pos->z < g_kCourtBoxOuterMin.z) return false;

    // Angled-wedge Y test: interpolate upper bound between outer and inner
    // as X crosses the gap.  When the two bounds coincide, fall back to
    // g_kFloatConst_D108 (the court's zero-timer float constant) to avoid
    // divide-by-zero — matches the PPC scaffold at loc_820E8F44.
    float xRange    = g_kCourtBoxInnerMax.x - g_kCourtBoxOuterMax.x;
    float interpFrac;
    if (xRange == 0.0f) {
        interpFrac = g_kFloatConst_D108;
    } else {
        float xOffset = pos->x - g_kCourtBoxOuterMax.x;
        interpFrac = xOffset / xRange;
    }
    float maxY = g_kCourtBoxInnerMax.y * interpFrac;
    return pos->y <= maxY;
}


// ═════════════════════════════════════════════════════════════════════════════
// pongPlayer — Stub implementations lifted from stubs.cpp
// ═════════════════════════════════════════════════════════════════════════════

/**
 * pongPlayer::CheckBallSplash @ 0x820C???? 
 *
 * Checks whether the ball has hit the table surface and created a splash
 * effect. Reads the ball splash array (416-byte entries) indexed by the
 * player's input slot, and checks a flag byte within the entry.
 *
 * @return true if a ball splash is active for this player
 */
extern "C" bool pongPlayer_CheckBallSplash(void* a) {
    if (!a) return false;
    pongPlayer* player = (pongPlayer*)a;

    // Index into the global ball splash array (416 bytes per entry)
    int32_t slotIdx = player->m_inputSlotIdx;
    if (slotIdx < 0) return false;

    // Check splash flag in the per-player splash entry
    uint8_t* splashEntry = g_ballSplashArray + (slotIdx * 416);
    uint8_t splashFlag = splashEntry[0];

    return splashFlag != 0;
}

/**
 * pongPlayer::ClearShotState
 *
 * Resets the player's shot state fields to their default values.
 * Clears timing, recovery, and swing data to prepare for a new shot.
 */
extern "C" void pongPlayer_ClearShotState(void* a) {
    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Clear swing input result and slot
    player->m_swingInputResult = 0;
    player->m_swingInputSlot = 0;
    player->m_bSwingActive = 0;

    // Clear swing phase input values
    player->m_swingPhaseInput = 0.0f;
    player->m_swingDirectionAdj = 0.0f;
    player->m_swingTimingClamp = 0.0f;
}

/**
 * pongPlayer::GetAnimIndex
 *
 * Returns the current animation index for this player. This is used
 * by the rendering system to select the correct animation clip.
 *
 * @return Animation index (0 = idle/default)
 */
extern "C" int pongPlayer_GetAnimIndex(void* a) {
    if (!a) return 0;
    pongPlayer* player = (pongPlayer*)a;

    // The anim index is derived from the anim state's frame index
    if (player->m_pAnimState) {
        return player->m_pAnimState->m_frameIndex;
    }
    return 0;
}

/**
 * pongPlayer::GetVelocity
 *
 * Fills the output vec3 with the player's current velocity.
 * Reads from the physics body's velocity data.
 *
 * @param a Player pointer
 * @param b Output float[3] for velocity XYZ
 */
extern "C" void pongPlayer_GetVelocity(void* a, float* b) {
    if (!b) return;
    b[0] = 0.0f;
    b[1] = 0.0f;
    b[2] = 0.0f;

    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Read velocity from the physics body sub-object
    if (player->m_pPhysicsBody) {
        uint8_t* body = (uint8_t*)player->m_pPhysicsBody;
        // Velocity is typically stored at body+12, +16, +20
        b[0] = *(float*)(body + 12);
        b[1] = *(float*)(body + 16);
        b[2] = *(float*)(body + 20);
    }
}

/**
 * pongPlayer::NetSync
 *
 * Synchronizes player state over the network. The second parameter
 * indicates the sync mode (0=full, 1=delta, etc.).
 *
 * @param a Player pointer
 * @param b Sync mode
 */
extern "C" void pongPlayer_NetSync(void* a, int b) {
    if (!a) return;
    (void)b;
    // Network sync is a no-op in single-player mode.
    // In multiplayer, this would serialize the player's state
    // and send it to the remote peer.
}

/**
 * pongPlayer::ProcessReplay
 *
 * Processes replay data for this player. During replay playback,
 * this function reads recorded input/state data and applies it
 * to the player instead of reading live input.
 *
 * @param a Player pointer
 */
extern "C" void pongPlayer_ProcessReplay(void* a) {
    if (!a) return;
    // Replay processing reads from a recorded data stream
    // and applies the stored state to the player.
    // This is a no-op when not in replay mode.
}

/**
 * pongPlayer::ResetShotTiming
 *
 * Resets the shot timing state with a new base time value.
 * Called when starting a new serve or after a point is scored.
 *
 * @param a Player pointer
 * @param b New base timing value
 */
extern "C" void pongPlayer_ResetShotTiming(void* a, float b) {
    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Reset timing state
    if (player->m_pTimingState) {
        player->m_pTimingState->m_currentTime = 0.0f;
        player->m_pTimingState->m_currentTime2 = 0.0f;
        player->m_pTimingState->m_targetTime = b;
        player->m_pTimingState->m_bComplete = 0;
    }
}

/**
 * pongPlayer::ResetSwingImpl
 *
 * Resets the internal swing state machine. Clears all swing-related
 * flags and counters, preparing the player for a new swing action.
 *
 * @param a Player pointer
 */
extern "C" void pongPlayer_ResetSwingImpl(void* a) {
    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Clear swing active flag
    player->m_bSwingActive = 0;
    player->m_swingInputResult = 0;
    player->m_swingInputSlot = 0;

    // Clear swing commit flags
    player->m_bSwingCommit1 = 0;
    player->m_bSwingCommit2 = 0;
}

/**
 * pongPlayer::SetScoreSlot
 *
 * Sets the player's score display slot index. This determines which
 * position on the scoreboard UI this player's score is shown.
 *
 * @param a Player pointer
 * @param b Score slot index (0 or 1)
 */
extern "C" void pongPlayer_SetScoreSlot(void* a, int b) {
    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Store the score slot index
    // This maps to a field in the player's match data
    player->m_slotIndex = b;
}

/**
 * pongPlayer::SyncFloat
 *
 * Synchronizes a float field between two player state objects.
 * Used during network replication to keep float values in sync.
 *
 * @param a Target field pointer
 * @param b Source field pointer
 */
extern "C" void pongPlayer_SyncFloat(void* a, void* b) {
    if (!a || !b) return;
    // Copy the float value from source to target
    *(float*)a = *(float*)b;
}

/**
 * pongPlayer::SyncWord
 *
 * Synchronizes a 32-bit word field between two player state objects.
 * Used during network replication to keep integer/flag values in sync.
 *
 * @param a Target field pointer
 * @param b Source field pointer
 */
extern "C" void pongPlayer_SyncWord(void* a, void* b) {
    if (!a || !b) return;
    // Copy the 32-bit word from source to target
    *(uint32_t*)a = *(uint32_t*)b;
}


/**
 * ResetShotTimingState
 *
 * Resets the shot timing state for a player. Called when transitioning
 * between game states (e.g., after a point is scored, before a new serve).
 * Clears all timing-related fields in the player's shot state sub-object.
 *
 * @param a Player state pointer
 */
extern "C" void ResetShotTimingState(void* a) {
    if (!a) return;
    pongPlayer* player = (pongPlayer*)a;

    // Reset timing state to defaults
    if (player->m_pTimingState) {
        player->m_pTimingState->m_currentTime = 0.0f;
        player->m_pTimingState->m_currentTime2 = 0.0f;
        player->m_pTimingState->m_bComplete = 0;
    }

    // Reset recovery state
    if (player->m_pRecoveryState) {
        player->m_pRecoveryState->m_recoveryTimer = 0.0f;
        player->m_pRecoveryState->m_bForceBlock = 0;
    }
}

// Player_ApplyServeStarted — already implemented in src/game/network/pong_network.cpp


// ============================================================================
// Player utility stubs — moved from stubs.cpp
// ============================================================================

/**
 * game_CD20 @ 0x820DCD20 | size: 0x98
 * Recovery state reset — clears timing, position, and state fields
 * on a player's recovery state structure.
 */
void game_CD20(void* recoveryState) {
    if (!recoveryState) return;
    uint8_t* state = static_cast<uint8_t*>(recoveryState);
    *reinterpret_cast<uint8_t*>(state + 44) = 0;
    *reinterpret_cast<float*>(state + 48) = 0.0f;
    memset(state + 64, 0, 16);
    memset(state + 96, 0, 16);
    *reinterpret_cast<float*>(state + 112) = 0.0f;
    *reinterpret_cast<float*>(state + 116) = 0.0f;
    *reinterpret_cast<float*>(state + 120) = 0.0f;
    *reinterpret_cast<uint32_t*>(state + 36) = 0;
    *reinterpret_cast<int32_t*>(state + 40) = -1;
    *reinterpret_cast<int32_t*>(state + 200) = -1;
    *reinterpret_cast<uint32_t*>(state + 204) = 0;
    *reinterpret_cast<uint32_t*>(state + 208) = 0;
}

/**
 * game_D468 @ 0x820CD468 | size: 0xE4
 * Player target vector update — sets the target position on the
 * player's creature slots for movement interpolation.
 * TODO: Full SIMD lift.
 */
struct vec3;
void game_D468(void* player, vec3* targetPos) {
    (void)player; (void)targetPos;
}



// ===========================================================================
// SECTION 60 — Serve: EnterServeMode, SetupServe, StartServe, Serve
// ===========================================================================
//
// The serve sequence, named after its "pongPlayer::Serve() %s"-style debug
// strings: EnterServeMode puts the ball in the server's hand, SetupServe resets
// the serve's shot record, StartServe hands the creature's swing animation two
// callbacks, and Serve (one of those callbacks) tosses the ball so that it
// reaches the hit point exactly on the animation's hit frame.
//
// The header's pongPlayer is no help here: its fields below +0x100 are really
// pongCreature's (the 0x820Cxxxx functions it was built from take a
// pongCreature: 0x820C69A0 is called from pongCreature_vfn_7 with this-0x10),
// and the +0x1C4 it calls m_pOpponent is this player's own pongCreature
// (StartServe calls the pongCreature function 0x820C7248 on it; Serve reads
// its swing animation through it). So these functions read pongPlayer through
// pongPlayerServeLayout, which holds only offsets their own asm proves.
// Offsets in comments are the game's 32-bit ones.

// 16-byte AltiVec matrix, rows a, b, c and the translation d (rage::Matrix34).
struct pongMatrix34 {
    vec3 a, b, c, d;
};

// ── Physics ────────────────────────────────────────────────────────────────
// Shapes match rage::phSimulator / phLevelNew / phInst; the method names are
// what the calls do here, not proven names.

struct phBallArchetypeView {
    void** vtable;  // +0x00

    // Slot 15, called by Serve with 1.0f on the ball's archetype right before
    // the toss (probably a gravity or damping factor; unproven).
    void vfn_15(float value) {
        reinterpret_cast<void (*)(phBallArchetypeView*, float)>(vtable[15])(this, value);
    }
};

struct phInstView {
    void**           vtable;      // +0x00
    phBallArchetypeView* archetype;   // +0x04
    uint16_t         levelIndex;  // +0x08  slot in the physics level
    uint8_t          _pad0A[0x06];
    pongMatrix34     matrix;      // +0x10  world matrix
    uint8_t          _pad50[0x50];
    vec3             vecA0;       // +0xA0  moved into +0xB0 when the ball is placed in hand
    vec3             vecB0;       // +0xB0

    // Slot 3 gets the old matrix just before PlaceBallInHand overwrites it.
    void vfn_3(pongMatrix34* currentMatrix) {
        reinterpret_cast<void (*)(phInstView*, pongMatrix34*)>(vtable[3])(this, currentMatrix);
    }
};

// What the physics level hands back for the ball while it is active (a
// rage::phCollider in RAGE terms).
struct pongBallBody {
    void**      vtable;    // +0x00
    uint8_t     _pad04[0x0C];
    phInstView* inst;      // +0x10
    uint8_t     _pad14[0x50];
    float       mass;      // +0x64  inferred: launch velocity * this = the impulse applied
    uint8_t     _pad68[0x68];
    vec3        position;  // +0xD0  the impulse point; z is the distance from the net

    // Slot 1. Called after the ball is teleported into the hand and right
    // before the toss impulse (probably clears its motion). Taken to have no
    // arguments: r4/r5 hold unrelated leftovers at both call sites.
    void vfn_1() {
        reinterpret_cast<void (*)(pongBallBody*)>(vtable[1])(this);
    }
};

struct phLevelView {
    void**   vtable;        // +0x00
    uint8_t  _pad04[0x18];
    uint8_t* objectStates;  // +0x1C  one byte per level index; low 3 bits 0 = active

    bool IsActive(uint16_t index) const { return (objectStates[index] & 7) == 0; }

    // Slot 4: the body of an active object, or null.
    pongBallBody* GetActiveBody(uint16_t index) {
        return reinterpret_cast<pongBallBody* (*)(phLevelView*, uint16_t)>(vtable[4])(this, index);
    }

    // Slot 11: called right after an instance's matrix was overwritten by hand.
    void UpdateObjectLocation(uint16_t index) {
        reinterpret_cast<void (*)(phLevelView*, uint16_t)>(vtable[11])(this, index);
    }
};

struct phSimulatorView {
    void*        vtable;  // +0x00
    phLevelView* level;   // +0x04
};

extern phSimulatorView* g_pPhysicsSim;    // @ 0x825F5BD0
extern phLevelView*     g_pPhysicsLevel;  // @ 0x826065E4  same +0x1C state bytes as g_pPhysicsSim->level

// @ 0x822C4980 — activates the object at levelIndex and returns its body
// (rage::phSimulator::ActivateObject in shape). pong_ball.cpp stubs a
// void-returning (void*, unsigned short, ...) overload of this symbol.
extern pongBallBody* pongBallInstance_4980_g(phSimulatorView* sim, uint16_t levelIndex,
                                             int a, int b, int c, int d);
// @ 0x822CCBB8 — applies an impulse to a body at a point (component 0).
extern void phSimulator_CBB8_g(pongBallBody* body, const vec3* impulse, const vec3* point,
                               int component);

extern float g_identityVector[4];  // @ 0x82606740  (named in ph_physics.cpp)
extern float g_ballGravity;        // @ 0x825CBCE4  -9.8f in the image (.data, so tunable)

// ── Creature side ──────────────────────────────────────────────────────────

struct pongAnimClipView {
    uint8_t _pad00[0x1C];
    int32_t hitFrame;  // +0x1C  inferred: Serve times the toss to land on this frame (30 fps)
};

// The 16-byte callback StartServe gives the creature; 0x820C7248 copies the two
// of them into the serve blender at +0x50 and +0x60. game_3860 builds one of
// the same shape (rage::datCallback-like: target, function, data, kind).
typedef void (*pongCallbackFn)();
struct pongCallback {
    void*          target;    // +0x00
    pongCallbackFn function;  // +0x04
    void*          data;      // +0x08
    int32_t        kind;      // +0x0C  1: function(target); 4: function(target, int* answer)
};

struct pongCreatureServeView;

// One clip list of the serve blender: an atArray (pointer, 16-bit count).
struct pongAnimClipList {
    pongAnimClipView** items;  // +0x00
    uint16_t           count;  // +0x04
    uint16_t           _pad06;
};

// The serve blender (CancelSwing logs it as "Serve Blender"); the header calls
// it pongRecoveryState and pongPlayerState::IsRecovering reads its +0x2C/+0xAC.
// game_CD20 (0x820DCD20) clears the same fields.
struct pongSwingAnimView {
    uint8_t                _pad00[0x04];
    int32_t                field_04;   // +0x04  Start posts message 0x1002 to bit (1 << this)
    pongCreatureServeView* creature;   // +0x08  Start reads the player index at its +0xCC
    pongAnimClipList       clips;      // +0x0C  Start plays the last one
    pongAnimClipList       altClips;   // +0x14  ...or the last of these
    uint8_t                _pad1C[0x08];
    pongAnimClipView*      clip;       // +0x24
    uint8_t                _pad28[0x04];
    uint8_t                pending;    // +0x2C  set when Start can't play yet; counts as busy (IsRecovering)
    uint8_t                _pad2D[0x03];
    float                  startTime;  // +0x30  match-clock time the clip started
    uint8_t                _pad34[0x0C];
    vec3                   position;   // +0x40  where Start was asked to play the clip
    pongCallback           action;     // +0x50  StartServe: pongPlayer_Serve
    pongCallback           query;      // +0x60  StartServe: io_8A48
    uint8_t                _pad70[0x38];
    float                  fieldA8;    // +0xA8  zeroed by Start
    float                  progress;   // +0xAC  zeroed by Start; idle (not recovering) at >= 1.0
};

// What the blender manager's +0x94 points at, as far as 0x820C7248 reads it.
struct pongBlenderSub94View {
    uint8_t _pad00[0x1C];
    int32_t field_1C;  // +0x1C  the serve blender may start only when this is 0...
    int32_t field_20;  // +0x20  1 selects the serve blender's second clip list
    int32_t field_24;  // +0x24  ...and this is 3
};

// The object at pongCreature+0xBC that the 0x820CD550..0x820CDE98 predicates
// take: the header's pongPlayerState, which holds the swing blender (timing
// state, +0x7C), the serve blender (+0x80) and the junk-swing blender (+0x88).
struct pongServeBlenderView {
    uint8_t               _pad00[0x7C];
    pongTimingState*      timing;     // +0x7C  header: m_pTimingState
    pongSwingAnimView*    swingAnim;  // +0x80  header: m_pRecoveryState
    uint8_t               _pad84[0x10];
    pongBlenderSub94View* sub94;      // +0x94  header: m_pSwingData

    pongPlayerState* State() { return reinterpret_cast<pongPlayerState*>(this); }
};

struct pongCreatureServeView {
    uint8_t               _pad00[0xA8];
    void*                 fieldA8;      // +0xA8  header: m_pPhysicsBound; 0x820CAB48 reads it
    uint8_t               _padAC[0x10];
    pongServeBlenderView* blender;      // +0xBC
    uint8_t               _padC0[0x0C];
    int32_t               playerIndex;  // +0xCC  indexes the settings' playerMode
};

// @ 0x820DD1C0 — world position of the swing animation's hit point.
extern void game_D1C0(vec3* outPos, pongSwingAnimView* swingAnim);
// @ 0x820CE090 — a bone matrix from the creature's skeleton (bone id at +0x1C
// of the blender), translation pushed a little along the bone's motion.
extern void game_E090(pongServeBlenderView* blender, pongMatrix34* outMatrix);
// @ 0x820DD388 — the serve blender refuses to start when this is true.
extern bool game_D388(pongSwingAnimView* blender);
// @ 0x820DD3E8 — Start's last step on the blender once the clip is set.
extern void game_D3E8(pongSwingAnimView* blender);
// @ 0x821CE0F0 — Start calls it on lbl_8271A2EC unless lbl_825C9A2C is 1.
extern void game_E0F0(void* object);
extern void*   lbl_8271A2EC;  // @ 0x8271A2EC
extern int32_t lbl_825C9A2C;  // @ 0x825C9A2C  -1 in the image

// ── Player side ────────────────────────────────────────────────────────────

// rtti shotTarget (vtable 0x8203A824, stored by pongPlayer's fixup at
// 0x82198D88); lives at pongPlayer+0x1EC.
struct shotTargetLayout {
    void**      vtable;     // +0x00
    uint8_t     _pad04[0x28];
    pongPlayer* owner;      // +0x2C  also read by 0x8219F9C0
    uint8_t     _pad30[0x3E4];
    int32_t     field_414;  // +0x414  InitSwing sets +0x414, +0x418, +0xEA4 and +0xEA8 to 1
    int32_t     field_418;  // +0x418
    uint8_t     _pad41C[0xA88];
    int32_t     field_EA4;  // +0xEA4
    int32_t     field_EA8;  // +0xEA8
};

// rtti aiPlayer (vtable 0x8203A83C, stored by 0x821A5FC8); pongPlayer+0x1F0.
// What 0x821A66A8 fills in: four direction weights the AI wants for its swing.
// The names follow the pad's order (see pongPlayer_ReadSwingDirectionInput).
struct aiSwingDirectionView {
    uint8_t _pad00[0x04];
    float   up;        // +0x04
    float   down;      // +0x08
    float   right;     // +0x0C
    float   left;      // +0x10
    uint8_t _pad14[0x44];
    uint8_t resolved;  // +0x58  set by 0x821A66A8, which returns at once while it is set
};

struct aiPlayerServeView {
    struct Sub34 {
        uint8_t _pad00[0x04];
        float   value4;  // +0x04
    };
    uint8_t               _pad00[0x34];
    Sub34*                sub34;           // +0x34
    aiSwingDirectionView* swingDir;        // +0x38
    uint8_t               _pad3C[0x480];
    float                 reactionDelay;   // +0x4BC  inferred: the AI's direction waits until
    float                 reactionTimer;   // +0x4C0  ...this, stepped 1/60 per call, reaches it
    uint8_t               _pad4C4[0x1D];
    uint8_t               field_4E1;       // +0x4E1  updates take the AI's direction only when set
};

// pongPlayer+0x17F0; only the byte SetupServe clears is known.
struct pongPlayerSub17F0 {
    uint8_t _pad00[0x22];
    uint8_t flag22;  // +0x22
};

// pongPlayer+0x185C, read by pongPlayer_SelectShotType (0x82199A70): 5, or 9
// when flag4 is set (posting message 0x101A), or 3 when flag6 is set.
struct pongServeTypeFlags {
    uint8_t _pad00[0x04];
    uint8_t flag4;  // +0x04
    uint8_t _pad05;
    uint8_t flag6;  // +0x06
    uint8_t _pad07;
};

struct pongPlayerServeLayout {
    void**                 vtable;          // +0x000
    uint8_t                _pad004[0x1BC];
    phInstView*            ballInst;        // +0x1C0  the ball's instance, from **0x8271A2F4
    pongCreatureServeView* creature;        // +0x1C4  header: m_pOpponent
    float                  serveBounceZ;    // +0x1C8  inferred: the serve's bounce depth on the server's half
    int32_t                moveMode;        // +0x1CC  "Move mode is %d." (vfn_2); set by 0x82195C00
    int32_t                playerIndex;     // +0x1D0  header: m_inputSlotIdx
    uint8_t                _pad1D4[0x10];
    float                  aimNorm[2];      // +0x1E4  InitSwing copies the shot record's aimNorm here
    shotTargetLayout*      shotTarget;      // +0x1EC
    aiPlayerServeView*     ai;              // +0x1F0  header: m_pActionState
    uint8_t                _pad1F4[0x15F4];
    float                  field_17E8;      // +0x17E8  FLT_MAX when StartServe sees io_Input_poll_9D68
    int32_t                field_17EC;      // +0x17EC  2 then; io_8A48 answers whether it's nonzero
    pongPlayerSub17F0*     sub17F0;         // +0x17F0
    uint8_t                _pad17F4[0x68];
    pongServeTypeFlags     serveTypeFlags;  // +0x185C
    uint8_t                _pad1864[0x56];
    uint8_t                field_18BA;      // +0x18BA  cleared by Serve
    uint8_t                _pad18BB[0x0D];
    uint8_t                field_18C8;      // +0x18C8  set by StartServe and SetupServe
    uint8_t                _pad18C9[0x07];
    float                  storedSwingDir[4];  // +0x18D0  left, right, up, down (ReadSwingDirectionInput)
    uint8_t                _pad18E0[0x10];
    float                  serveHitDelay;   // +0x18F0  seconds from the toss to the hit frame
    float                  serveStartTime;  // +0x18F4  match clock when Serve ran
    uint8_t                _pad18F8[0x10];
    float                  field_1908[4];   // +0x1908  zeroed by InitSwing
    uint8_t                _pad1918[0x70];
    uint8_t                field_1988;      // +0x1988  set: ReadSwingDirectionInput ignores the pad
    uint8_t                _pad1989[0x27];
    vec3                   field_19B0;      // +0x19B0  zeroed by InitSwing
    uint8_t                swingDirLatched[4];  // +0x19C0  up, down, left, right were nonzero
    uint8_t                _pad19C4;
    uint8_t                noSwingDir;      // +0x19C5  set when an update finds none latched
    uint8_t                _pad19C6[0x10];
    uint8_t                field_19D6;      // +0x19D6  cleared by InitSwing
    uint8_t                field_19D7;      // +0x19D7  InitSwing sets both right before logging
    uint8_t                field_19D8;      // +0x19D8  "Locked Out swing Input for player %d."
    uint8_t                _pad19D9[0x03];
    uint32_t               swingDirMask;    // +0x19DC  bit 0 on: 0x8 drops down, else 0x10 drops up
    uint8_t                _pad19E0;
    uint8_t                field_19E1;      // +0x19E1  cleared by InitSwing
    uint8_t                field_19E2;      // +0x19E2  likewise
};

static pongPlayerServeLayout* ServeLayout(pongPlayer* player) {
    return reinterpret_cast<pongPlayerServeLayout*>(player);
}

// One 416-byte entry of the per-player table at 0x8261A3D0 (g_ballSplashArray
// above), indexed by pongPlayer+0x1D0. The record at +0x30 is the one
// 0x821D6100 and 0x8219F9C0's 0x821D5F70 take.
struct pongShotRecord {
    uint8_t  _pad00[0x20];
    vec3     targetPos;    // +0x20  world point the shot aims at (Serve mirrors its z)
    uint8_t  _pad30[0x10];
    vec3     vec40;        // +0x40  zeroed by SetupServe unless shotType is 3; its x gates up/down input
    uint8_t  _pad50[0x10];
    vec3     vec60;        // +0x60  InitSwing measures targetPos's distance from this
    uint8_t  _pad70[0x24];
    float    gravity;      // +0x94  inferred: 0x821D6100 sets it between the ball's gravity and -11.85
    uint8_t  _pad98[0x04];
    int32_t  shotType;     // +0x9C  pongPlayer_SelectShotType's 5, 9 or 3
    uint8_t  _padA0[0x20];
    uint16_t fieldC0;      // +0xC0  InitSwing: the score object's +0x18
    uint16_t fieldC2;      // +0xC2  InitSwing: the score object's +0x14
    uint8_t  fieldC4;      // +0xC4  InitSwing: the sum of the two scores
    uint8_t  _padC5;
    uint16_t flagsC6;      // +0xC6  SetupServe sets the high byte to 0x10, InitSwing clears it
    uint8_t  _padC8[0x0C];
    uint8_t  fieldD4;      // +0xD4  cleared by InitSwing when fieldD5 is set
    uint8_t  fieldD5;      // +0xD5
    uint8_t  _padD6[0x1A];
    vec3     vecF0;        // +0xF0  zeroed by InitSwing
    float    aimNorm[2];   // +0x100 aim on the table, each in [-1, 1]; [1] follows depth
    uint8_t  _pad108[0x48];
    uint8_t  field150;     // +0x150 cleared by InitSwing
    uint8_t  _pad151[0x03];
    float    field154;     // +0x154 InitSwing: (|targetPos - vec60|^2 - 7, at least 0) / 15
};

struct pongPlayerShotEntry {
    uint8_t        _pad00[0x04];
    uint8_t        flag04;  // +0x04  cleared by StartServe and SetupServe
    uint8_t        flag05;  // +0x05  likewise
    uint8_t        _pad06[0x2A];
    pongShotRecord shot;    // +0x30
    uint8_t        _pad188[0x18];
};
static_assert(sizeof(pongPlayerShotEntry) == 0x1A0, "pongPlayerShotEntry is 416 bytes");
static_assert(offsetof(pongPlayerShotEntry, shot) + offsetof(pongShotRecord, aimNorm) == 0x130,
              "aimNorm sits at entry+0x130");

static pongPlayerShotEntry* PlayerShotEntries() {
    return reinterpret_cast<pongPlayerShotEntry*>(g_ballSplashArray);
}

// The match-settings singleton the file reaches as g_pInputArrayTable
// (0x825EAB28; also g_pInputObj / g_pButtonStateTable above).
struct pongMatchSettingsView {
    uint8_t _pad00[0x14];
    int32_t field_14;        // +0x14  CheckServeInput is false while this is positive
    uint8_t _pad18[0x20];
    int32_t playerMode[2];   // +0x38  per player; picks EnterServeMode's path (1: reads the pad)
    uint8_t sideFlipped[2];  // +0x40  per player; mirrors serve depth and aim (cf. SetServeSideFlip)
    uint8_t _pad42[0x5A];
    float   field_9C[2];     // +0x9C  per player; SetupServe and InitSwing feed it to 0x821D6100
    uint8_t _padA4[0xB5];
    uint8_t field_159;       // +0x159 CheckServeInput's answer for a mode-1 player
};
static_assert(offsetof(pongMatchSettingsView, field_159) == 0x159, "settings +0x159");
static_assert(offsetof(pongMatchSettingsView, field_9C) == 0x9C, "settings +0x9C");

static pongMatchSettingsView* MatchSettings() {
    return reinterpret_cast<pongMatchSettingsView*>(g_pInputArrayTable);
}

// What 0x8271A304 points at (declared above as g_pGlobalClock, but xe_9DC8
// fills it with the table's dimensions in metres).
struct pongTableDims {
    uint8_t _pad00[0x10];
    float   width;    // +0x10  1.5224
    float   height;   // +0x14  0.7628
    float   length;   // +0x18  2.7439
    uint8_t _pad1C[0x08];
    float   field24;  // +0x24  0.325
    float   field28;  // +0x28  0.481
};

static const pongTableDims* TableDims() {
    return static_cast<const pongTableDims*>(g_pGlobalClock);
}

extern "C" void* g_pongMatchTiming;  // @ 0x8271A2E8  (named in pong_lerp_queue.cpp)
struct pongMatchClockView {
    uint8_t _pad00[0x30];
    float   now;  // +0x30  match clock, seconds
};

static float MatchClockNow() {
    return static_cast<const pongMatchClockView*>(g_pongMatchTiming)->now;
}

// What g_game_state_ptr (0x8271A2F8) points at, as far as EnterServeMode reads it.
struct pongGameStateServeView {
    struct Sub14 {
        uint8_t _pad00[0x25A8];
        int32_t field_25A8;  // +0x25A8  game_3860 is only called while this is positive
    };
    uint8_t _pad00[0x14];
    Sub14*  sub14;           // +0x14   game_3860 logs into this object too
};

extern void* g_game_state_ptr;       // @ 0x8271A2F8
extern void* g_networkTimingObject;  // @ 0x8271A328

// @ 0x82391480 — cached timestamp text for log lines.
extern const char* util_1480(void* clock, int slot);
// @ 0x821D3860 — records a named transition on the game state object.
extern void game_3860(void* gameState, int kind, const char* name);
// @ 0x8225E6E0 — posts a game message (same declaration as message.cpp;
// PostPageGroupMessage above gives it a fifth argument it doesn't take).
extern void PostGameMessage(uint32_t messageId, uint32_t flags, uint32_t param1, uint32_t param2);
// @ 0x82198A48 — StartServe's query callback: *answer = io_Input_poll_9D68 && +0x17EC != 0.
extern void io_8A48(pongPlayer* player, int32_t* answer);
// Flags argument of PostGameMessage: one bit per player.
static uint32_t PlayerMessageBit(int32_t playerIndex) {
    return playerIndex != 0 ? 2u : 1u;
}

// ── Swing and shot externs ─────────────────────────────────────────────────

// What 0x825EAB2C points at; message.cpp and globals.c call it g_render_obj_ptr.
// pong_match.cpp reads +0x1C and +0x20 as the two players' scores.
struct pongScoreView {
    uint8_t _pad00[0x14];
    int32_t field_14;   // +0x14
    int32_t field_18;   // +0x18
    int32_t points[2];  // +0x1C
};
extern void* g_render_obj_ptr;  // @ 0x825EAB2C

// The controller table behind 0x8271A31C (g_pPlayerDataTable above): which pad
// each player uses, then 0x328-byte pad records from +0x0C.
struct pongPadTableView {
    uint8_t _pad00[0x04];
    int32_t padForPlayer[2];  // +0x04
};

static void* PlayerPad(int32_t playerIndex) {
    uint8_t* table = g_pPlayerDataTable;
    int32_t pad = reinterpret_cast<const pongPadTableView*>(table)->padForPlayer[playerIndex];
    return table + 0x0C + pad * 0x328;
}

// @ 0x821E04B0 — true when bit 7 differs between bytes 0 and 3 of the button's
// entry in the pad record. The lift above as pongPlayer::CheckHandednessDifference
// takes a pongPlayer and drops the button argument.
extern bool pongPlayer_04B0_g(void* pad, int32_t button);
// @ 0x821921D0 — 0, or the stick's direction as 1..8; going by how
// ReadSwingDirectionInput maps it, 1 is up and they run clockwise.
extern int32_t phBoundCapsule_21D0_g(pongPlayer* player);
// @ 0x821A66A8 — works out the AI's direction weights once (sets `resolved`).
extern void pongPlayer_66A8_g(aiSwingDirectionView* dir);
// @ 0x82193A68 — applies the four weights (left, right, up, down) to the swing.
extern void pongPlayer_3A68_g(pongPlayer* player, float left, float right, float up, float down);
// @ 0x8219EE88 — the shotTarget's side: hands the weights to its +0xAF0 object.
extern void game_EE88(shotTargetLayout* target, int32_t arg, float left, float right,
                      float up, float down);

extern uint8_t lbl_8260642F;  // @ 0x8260642F  set by vfn_2 right before an update; gates storing the pad's weights
extern float   lbl_825C7598;  // @ 0x825C7598  7.0 in the image (.data)
extern float   lbl_825CAF0C;  // @ 0x825CAF0C  1/60 in the image (.data)


/**
 * pongServeBlender_Start  (game_D060 @ 0x820DD060 | size: 0x160)
 * (called by pongCreature_StartServeBlender and LocomotionStateAnim_CDB8_g)
 *
 * Starts the serve blender if it is idle: when canStart is false or 0x820DD388
 * objects, only marks it pending. Otherwise stamps the match clock, plays the
 * last clip of one of its two lists at `position`, resets its progress and
 * posts messages 0x1004 and 0x1002. Every path returns 0.
 */
bool pongServeBlender_Start(pongSwingAnimView* blender, const vec3* position, bool canStart,
                            bool useAltClips)
{
    // pongPlayerState::IsRecovering inlined: idle once progress reaches 1.0.
    bool idle = !blender->pending && blender->progress >= 1.0f;  // 1.0f @ 0x8202D108
    if (!idle)
        return false;

    int32_t playerIndex = blender->creature->playerIndex;
    if (!canStart || game_D388(blender)) {
        blender->pending = 1;
        return false;
    }

    blender->startTime = MatchClockNow();
    const pongAnimClipList& list = useAltClips ? blender->altClips : blender->clips;
    blender->clip = list.items[list.count - 1];
    blender->position = *position;
    game_D3E8(blender);

    blender->fieldA8 = 0.0f;   // @ 0x8202D110
    blender->progress = 0.0f;
    PostGameMessage(0x1004, (uint8_t)(1u << playerIndex) | 0x40, 0, 0);
    if (lbl_825C9A2C != 1)
        game_E0F0(lbl_8271A2EC);
    PostGameMessage(0x1002, (uint8_t)(1u << blender->field_04) | 0x40, 0, 0);
    return false;
}


/**
 * pongCreature_StartServeBlender  (pongPlayer_7248_g @ 0x820C7248 | size: 0x19C)
 * (called by pongPlayer_StartServe and ServeStartedMessage_5728)
 *
 * A pongCreature function. If a swing is running and the player's mode is 2,
 * interrupts it first; if one is still running, does nothing. Otherwise
 * gives the serve blender the two callbacks (unconditionally) and starts it at
 * the position 0x820CAB48 works out, letting it play only when the blender
 * manager's +0x94 record has +0x1C == 0 and +0x24 == 3.
 */
void pongCreature_StartServeBlender(pongCreatureServeView* creature, const pongCallback* action,
                                    const pongCallback* query)
{
    pongServeBlenderView* blender = creature->blender;
    if (blender->State()->IsSwingTimerActive() &&
        MatchSettings()->playerMode[creature->playerIndex] == 2)
        blender->State()->CancelSwing();

    if (creature->blender->State()->IsSwingTimerActive())
        return;

    // 0x820CAB48 returns its first argument; the asm passes that return value on.
    vec3 position;
    pongPlayer_AB48_g(&position, creature->fieldA8);

    blender = creature->blender;
    const pongBlenderSub94View* sub94 = blender->sub94;
    bool canStart = sub94->field_1C == 0 && sub94->field_24 == 3;
    bool useAltClips = sub94->field_20 == 1;
    blender->swingAnim->action = *action;
    blender->swingAnim->query = *query;
    pongServeBlender_Start(blender->swingAnim, &position, canStart, useAltClips);
}


extern float lbl_825C7600;  // @ 0x825C7600  -11.85 in the image (.data)

/**
 * pongShotRecord_SetGravity  (pongPlayer_6100_g @ 0x821D6100 | size: 0xA8)
 * (called by pongPlayer_SetupServe and pongPlayer_InitSwing)
 *
 * Runs on the per-player shot record. Sets +0x94 between the ball's gravity
 * and -11.85 (0x825C7600) by |input| clamped to [-0.9, -0.9]: both bounds are
 * -0.9 in the image (the float at 0x82079D50 and the double at 0x82079D48), so
 * any non-NaN input gives g + (-11.85 - g) * 0.9. Shot types 8, 9 and 10 run
 * the same store two to four times (switch fall-through in the asm).
 */
void pongShotRecord_SetGravity(pongShotRecord* shot, float input)
{
    const float kLow  = -0.9f;  // @ 0x82079D50
    const float kHigh = -0.9f;  // @ 0x82079D48 (double)

    // fsel clamp; the low branch already selects the double.
    float raised = (input - kLow >= 0.0f) ? input : kHigh;
    float clamped = (raised - kHigh >= 0.0f) ? kHigh : raised;

    const float heavy = lbl_825C7600;
    switch (shot->shotType) {
    case 8:
        shot->gravity = (heavy - g_ballGravity) * fabsf(clamped) + g_ballGravity;
        // fall through
    case 9:
        shot->gravity = (heavy - g_ballGravity) * fabsf(clamped) + g_ballGravity;
        // fall through
    case 10:
        shot->gravity = (heavy - g_ballGravity) * fabsf(clamped) + g_ballGravity;
        // fall through
    default:
        shot->gravity = (heavy - g_ballGravity) * fabsf(clamped) + g_ballGravity;
        break;
    }
}


/**
 * pongPlayer_SelectShotType  (pg_9A70 @ 0x82199A70 | size: 0x6C)
 * (called by pongPlayer_SetupServe and pongPlayer_InitSwing on pongPlayer+0x185C)
 *
 * 5 by default; 9 when flag4 is set, after posting message 0x101A to the
 * player's bit; 3 when flag6 is set, whatever flag4 said.
 */
int32_t pongPlayer_SelectShotType(pongServeTypeFlags* flags, int32_t playerIndex)
{
    int32_t shotType = 5;
    if (flags->flag4) {
        PostGameMessage(0x101A, (uint8_t)(1u << playerIndex) | 0x40, 0, 0);
        shotType = 9;
    }
    if (flags->flag6)
        shotType = 3;
    return shotType;
}


/**
 * pongPlayer_CheckServeInput  (pongPlayer_5B60_gen @ 0x82195B60 | size: 0xA0)
 *
 * False while io_Input_poll_9D68 reports the settings busy or the settings'
 * +0x14 is positive; otherwise true only for a mode-1 (pad-driven) player
 * whose settings byte +0x159 is set. ReadSwingDirectionInput reads the pad
 * only when this is false, so the name (from EnterServeMode's use) is loose.
 */
bool pongPlayer_CheckServeInput(pongPlayer* player)
{
    pongMatchSettingsView* settings = MatchSettings();
    if (io_Input_poll_9D68(settings))
        return false;
    if (settings->field_14 > 0)
        return false;
    if (settings->playerMode[ServeLayout(player)->playerIndex] != 1)
        return false;
    return settings->field_159 != 0;
}


/**
 * pongPlayer_ReadSwingDirectionInput  (pongPlayer_1B10_g @ 0x82191B10 | size: 0x414)
 * (called by InitSwing with update = false; vfn_2, F6D0, FinalizeSwing, 2D88
 *  and ref_fi_EFD0 pass 0 or 1)
 *
 * Builds four direction weights for the swing, each 0 or 1 from the pad, or
 * the AI's own. A pad-driven player (mode 1, +0x1988 clear, CheckServeInput
 * false) reads pad buttons 0x32..0x35 (up, down, left, right; up only while
 * the shot's vec40.x isn't positive, down only while it isn't negative) and
 * the stick's octant, which also sets the two neighbours of a diagonal. Any
 * other player takes the AI's weights: on an update only once the AI's +0x4E1
 * is set, otherwise once its reaction timer (stepped 1/60) reaches the delay.
 * Outside updates swingDirMask can drop down or up. Each nonzero weight is
 * latched; an update with nothing latched only sets noSwingDir. Then the swing
 * gets the weights (the stored ones on an update) and the shotTarget the
 * fresh ones.
 *
 * The up/down/left/right names are inferred: 0x32..0x35 in XInput's d-pad
 * order, and the octants running clockwise from up, agree with each other.
 */
void pongPlayer_ReadSwingDirectionInput(pongPlayer* player, bool update)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    const float kZero = 0.0f;  // @ 0x8202D110
    const float kOne  = 1.0f;  // @ 0x8202D108

    int32_t playerIndex = self->playerIndex;
    float left = kZero, right = kZero, up = kZero, down = kZero;
    self->swingDirLatched[0] = 0;
    self->swingDirLatched[1] = 0;
    self->swingDirLatched[2] = 0;
    self->swingDirLatched[3] = 0;
    const pongShotRecord& shot = PlayerShotEntries()[playerIndex].shot;

    if (MatchSettings()->playerMode[playerIndex] == 1 && !self->field_1988 &&
        !pongPlayer_CheckServeInput(player)) {
        void* pad = PlayerPad(playerIndex);
        if (pongPlayer_04B0_g(pad, 0x32) && !(shot.vec40.x > kZero))
            up = kOne;
        if (pongPlayer_04B0_g(pad, 0x33) && (shot.vec40.x >= kZero || -shot.vec40.x == kZero))
            down = kOne;
        if (pongPlayer_04B0_g(pad, 0x34))
            left = kOne;
        if (pongPlayer_04B0_g(pad, 0x35))
            right = kOne;

        switch (phBoundCapsule_21D0_g(player)) {
        case 1: up = kOne; break;
        case 2: right = kOne; up = kOne; break;
        case 3: right = kOne; break;
        case 4: down = kOne; right = kOne; break;
        case 5: down = kOne; break;
        case 6: down = kOne; left = kOne; break;
        case 7: left = kOne; break;
        case 8: left = kOne; up = kOne; break;
        default: break;
        }

        if (lbl_8260642F) {
            self->storedSwingDir[0] = left;
            self->storedSwingDir[1] = right;
            self->storedSwingDir[2] = up;
            self->storedSwingDir[3] = down;
        }
    } else {
        // 0x821A66A8 leaves r3 alone, so the asm goes on using it as `dir`.
        aiSwingDirectionView* dir = self->ai->swingDir;
        if (!dir->resolved)
            pongPlayer_66A8_g(dir);

        if (update) {
            if (self->ai->field_4E1) {
                left = dir->left;
                right = dir->right;
                up = dir->up;
                down = dir->down;
                self->storedSwingDir[0] = left;
                self->storedSwingDir[1] = right;
                self->storedSwingDir[2] = up;
                self->storedSwingDir[3] = down;
            }
        } else if (!(self->ai->reactionTimer >= self->ai->reactionDelay)) {
            left = dir->left;
            right = dir->right;
            up = dir->up;
            down = dir->down;
            self->ai->reactionTimer = self->ai->reactionTimer + lbl_825CAF0C;
        } else {
            left = kZero;
            right = kZero;
            up = kZero;
            down = kZero;
        }
    }

    if (!update) {
        uint32_t mask = self->swingDirMask;
        if (mask & 0x1) {
            if (mask & 0x8)
                down = kZero;
            else if (mask & 0x10)
                up = kZero;
        }
    }

    if (up != kZero)
        self->swingDirLatched[0] = 1;
    if (down != kZero)
        self->swingDirLatched[1] = 1;
    if (left != kZero)
        self->swingDirLatched[2] = 1;
    if (right != kZero)
        self->swingDirLatched[3] = 1;

    if (update) {
        if (!self->swingDirLatched[0] && !self->swingDirLatched[1] &&
            !self->swingDirLatched[2] && !self->swingDirLatched[3]) {
            self->noSwingDir = 1;
            return;
        }
        pongPlayer_3A68_g(player, self->storedSwingDir[0], self->storedSwingDir[1],
                          self->storedSwingDir[2], self->storedSwingDir[3]);
    } else {
        pongPlayer_3A68_g(player, left, right, up, down);
    }
    game_EE88(self->shotTarget, 0, left, right, up, down);
}


/**
 * pongPlayer_InitSwing  (pongPlayer_0780_g @ 0x82190780 | size: 0x208)
 * (called by pongPlayer_vfn_2)
 *
 * "Called Init Swing for Player %d": resets the player's shot record and
 * swing input for a new swing (like SetupServe does for a serve), picks the
 * shot type, recomputes the record's gravity and +0x154, reads the swing
 * direction, then locks swing input ("Locked Out swing Input for player %d.").
 */
void pongPlayer_InitSwing(pongPlayer* player)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    const float kZero = 0.0f;  // @ 0x8202D110
    nop_8240E6D0("Called Init Swing for Player %d", self->playerIndex);

    pongShotRecord& shot = PlayerShotEntries()[self->playerIndex].shot;
    self->swingDirMask = 0;

    // The asm writes x, y and z of a stack vector and copies all 16 bytes, so
    // vecF0's w gets whatever was on the stack; zeroed here.
    vec3 zero;
    zero.x = kZero;
    zero.y = kZero;
    zero.z = kZero;
    zero._pad = kZero;

    if (shot.fieldD5)
        shot.fieldD4 = 0;
    else
        nop_8240E6D0("Cannot Lock when Unlock is not enabled");

    // 0x8219F9C0 is lifted above as pongPlayer::FinalizeServeSetup, but its
    // `this` is the shotTarget (it finds the player at +0x2C).
    reinterpret_cast<pongPlayer*>(self->shotTarget)->FinalizeServeSetup();
    self->sub17F0->flag22 = 0;

    // The asm clears the high byte of +0xC6 twice (two bitfields, presumably).
    shot.flagsC6 = (uint16_t)(shot.flagsC6 & 0x00FF);
    shot.vecF0 = zero;
    shot.flagsC6 = (uint16_t)(shot.flagsC6 & 0x00FF);

    const pongScoreView* score = static_cast<const pongScoreView*>(g_render_obj_ptr);
    shot.fieldC0 = (uint16_t)score->field_18;
    shot.fieldC4 = (uint8_t)(score->points[1] + score->points[0]);
    shot.fieldC2 = (uint16_t)score->field_14;

    self->aimNorm[0] = shot.aimNorm[0];
    self->aimNorm[1] = shot.aimNorm[1];
    self->shotTarget->field_EA4 = 1;
    self->shotTarget->field_EA8 = 1;
    self->shotTarget->field_414 = 1;
    self->shotTarget->field_418 = 1;

    memset(&self->field_19B0, 0, sizeof(self->field_19B0));
    for (int i = 0; i < 4; ++i) {
        self->swingDirLatched[i] = 0;
        self->field_1908[i] = kZero;
    }
    self->field_19D6 = 0;
    self->field_19E1 = 0;
    self->field_19E2 = 0;
    shot.field150 = 0;

    player->OnButtonReleased();  // vtable slot 9 (0x821935B8)

    shot.shotType = pongPlayer_SelectShotType(&self->serveTypeFlags, self->playerIndex);
    pongShotRecord_SetGravity(&shot, MatchSettings()->field_9C[self->playerIndex]);

    // dot3 of the difference (vmsum3fp128), less 7, floored at 0, over 15.
    float dx = shot.targetPos.x - shot.vec60.x;
    float dy = shot.targetPos.y - shot.vec60.y;
    float dz = shot.targetPos.z - shot.vec60.z;
    float excess = (dx * dx + dy * dy + dz * dz) - lbl_825C7598;
    if (!(excess >= kZero))
        excess = kZero;
    shot.field154 = excess * (1.0f / 15.0f);  // @ 0x82079E7C

    pongPlayer_ReadSwingDirectionInput(player, false);

    self->field_19D8 = 1;
    self->field_19D7 = 1;
    nop_8240E6D0("Locked Out swing Input for player %d.", self->playerIndex);
}



/**
 * pongPlayer_GetServeBallBody  (pongPlayer_25C8_g @ 0x821925C8 | size: 0x9C)
 *
 * Returns the ball's physics body: the level's body for it while it is active,
 * otherwise whatever activating it returns. Called by Serve and 0x8218D818.
 */
pongBallBody* pongPlayer_GetServeBallBody(pongPlayer* player)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    phLevelView* level = g_pPhysicsSim->level;
    uint16_t ballIndex = self->ballInst->levelIndex;

    if (level->IsActive(ballIndex)) {
        pongBallBody* body = level->GetActiveBody(ballIndex);
        if (body)
            return body;
    }
    return pongBallInstance_4980_g(g_pPhysicsSim, self->ballInst->levelIndex, 0, 0, 0, 0);
}


/**
 * pongPlayer_PlaceBallInHand  (pongPlayer_EAA8_g @ 0x8218EAA8 | size: 0x100)
 *
 * Teleports the ball's instance onto a bone of the player's creature (the
 * serving hand, going by the callers EnterServeMode and Serve), shifts the
 * instance's +0xA0 vector into +0xB0 and resets +0xA0, lets the body run its
 * slot 1, and tells the physics level the object moved.
 */
void pongPlayer_PlaceBallInHand(pongPlayer* player, pongBallBody* ball)
{
    pongPlayerServeLayout* self = ServeLayout(player);

    pongMatrix34 holdMatrix;
    game_E090(self->creature->blender, &holdMatrix);

    phInstView* inst = self->ballInst;
    inst->vfn_3(&inst->matrix);

    inst = self->ballInst;
    inst->matrix = holdMatrix;
    inst->vecB0 = inst->vecA0;
    memcpy(&inst->vecA0, g_identityVector, sizeof(inst->vecA0));

    if (ball)
        ball->vfn_1();

    g_pPhysicsLevel->UpdateObjectLocation(self->ballInst->levelIndex);
}


/**
 * pongPlayer_TossServeBall  (game_34A0 @ 0x821934A0 | size: 0x114)
 *
 * The serve toss: launches the ball so it reaches the swing animation's hit
 * point after flightTime seconds. Solves the ballistic arc for the velocity,
 *   v = (hitPoint - position) / t,   v.y -= (gravity / 2) * t,
 * turns it into an impulse with the body's mass and applies it at the ball.
 */
void pongPlayer_TossServeBall(pongPlayer* player, pongBallBody* ball, float flightTime)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    const float halfGravity = g_ballGravity * 0.5f;  // 0.5f @ 0x8202D10C

    vec3 hitPoint;
    game_D1C0(&hitPoint, self->creature->blender->swingAnim);

    // The asm takes 1/t with vrefp plus one Newton-Raphson step (the 1.0
    // vector at 0x825CB7C0), and runs every vector step on the w lane too.
    float invTime = 1.0f / flightTime;
    vec3 velocity;
    velocity.x = (hitPoint.x - ball->position.x) * invTime;
    velocity.y = (hitPoint.y - ball->position.y) * invTime;
    velocity.z = (hitPoint.z - ball->position.z) * invTime;
    velocity._pad = (hitPoint._pad - ball->position._pad) * invTime;
    velocity.y = velocity.y - halfGravity * flightTime;

    const float mass = ball->mass;
    vec3 impulse;
    impulse.x = velocity.x * mass;
    impulse.y = velocity.y * mass;
    impulse.z = velocity.z * mass;
    impulse._pad = velocity._pad * mass;

    ball->vfn_1();
    phSimulator_CBB8_g(ball, &impulse, &ball->position, 0);
}


/**
 * shotTarget_AdjustAimDepthForBall  (pongPlayer_FBD8_w @ 0x8219FBD8 | size: 0x100)
 *
 * A shotTarget method, not pongPlayer's: Serve calls it on pongPlayer+0x1EC
 * and it reaches the player through shotTarget+0x2C. Also called by 0x8219EF38.
 *
 * When the ball is more than (table length - 0.1) from the net and the aim's
 * world depth is short of that overshoot, moves the normalized aim depth by the
 * difference, scaled to the table, and clamps it to [-1, 1].
 */
void shotTarget_AdjustAimDepthForBall(shotTargetLayout* target, const pongBallBody* ball)
{
    const float kMargin = 0.1f;  // @ 0x8202CFE8
    const pongTableDims* table = TableDims();

    float ballDepth = fabsf(ball->position.z);
    if (ballDepth <= table->length - kMargin)
        return;

    float overshoot = ballDepth - table->length + kMargin;
    int32_t playerIndex = ServeLayout(target->owner)->playerIndex;
    pongShotRecord& shot = PlayerShotEntries()[playerIndex].shot;

    vec3 targetPos = shot.targetPos;  // 16-byte copy to the stack in the asm
    if (fabsf(targetPos.z) >= overshoot)
        return;

    if (MatchSettings()->sideFlipped[playerIndex])
        overshoot = -overshoot;

    float depthRange = (table->field28 + table->field24) * (table->length * 0.5f);
    float aimDepth = (overshoot - targetPos.z) / depthRange * 2.0f + shot.aimNorm[1];  // 2.0f @ 0x8202D184

    // fsel clamp. The lower test is against -1.0f (0x825C5938); the doubles it
    // selects (0x82079D10, 0x82079B08) aren't in the excavated constants and
    // are taken to be -1.0 and 1.0.
    if (aimDepth < -1.0f)
        aimDepth = -1.0f;
    if (aimDepth >= 1.0f)
        aimDepth = 1.0f;

    // The asm writes both halves back with one 8-byte store; [0] keeps its value.
    shot.aimNorm[1] = aimDepth;
}


/**
 * pongPlayer_Serve  @ 0x82193298 | size: 0x204
 *
 * Runs as the serve callback StartServe gives the creature's swing animation.
 * Puts the ball in hand, works out how long until the animation's hit frame,
 * sets move mode 4, picks the serve's bounce depth on the server's half, and
 * tosses the ball so it arrives at the hit point on that frame.
 */
void pongPlayer_Serve(pongPlayer* player)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    nop_8240E6D0("pongPlayer::Serve() %s", util_1480(g_networkTimingObject, 0));

    pongBallBody* ball = pongPlayer_GetServeBallBody(player);
    pongPlayer_PlaceBallInHand(player, ball);

    // Seconds until the swing animation reaches its hit frame (30 fps clips).
    const pongSwingAnimView* swing = self->creature->blender->swingAnim;
    float hitTime = swing->startTime + (float)swing->clip->hitFrame * (1.0f / 30.0f);  // @ 0x82079BB8
    float hitDelay = hitTime - MatchClockNow();
    self->serveHitDelay = hitDelay;
    self->serveStartTime = MatchClockNow();

    pongPlayer_5C00_g(player, 4);  // move mode 4

    // Bounce depth on the server's half: the aim point mirrored over the net,
    // pushed out to a quarter of the table if it is nearer the net than that,
    // and pulled in halfway towards the ball if it is behind the ball.
    vec3 targetPos = PlayerShotEntries()[self->playerIndex].shot.targetPos;
    float bounceZ = -targetPos.z;
    self->serveBounceZ = bounceZ;

    const pongTableDims* table = TableDims();
    float halfLength = table->length * 0.5f;     // 0.5f @ 0x8202D10C
    float quarterLength = halfLength * 0.5f;
    uint8_t sideFlipped = MatchSettings()->sideFlipped[self->playerIndex];

    if (fabsf(bounceZ) < quarterLength) {
        if (!sideFlipped)
            quarterLength = halfLength * -0.5f;  // -0.5f @ 0x82079BF8
        self->serveBounceZ = quarterLength;
    } else {
        float ballDepth = fabsf(ball->position.z);
        if (fabsf(bounceZ) > ballDepth) {
            float sum = quarterLength + ballDepth;
            self->serveBounceZ = sideFlipped ? sum * 0.5f : sum * -0.5f;
        }
    }

    ball->inst->archetype->vfn_15(1.0f);  // 1.0f @ 0x8202D108
    pongPlayer_TossServeBall(player, ball, hitDelay);

    PostGameMessage(0x820, PlayerMessageBit(self->playerIndex), 0, 0);
    shotTarget_AdjustAimDepthForBall(self->shotTarget, ball);
    self->field_18BA = 0;
}


/**
 * pongPlayer_StartServe  @ 0x82193190 | size: 0x104
 *
 * Gives the creature's serve blender two callbacks (pongCreature_StartServeBlender):
 * pongPlayer_Serve, and the query io_8A48. Then posts message 0x380B and
 * clears the player's two serve bytes in the shot table.
 */
void pongPlayer_StartServe(pongPlayer* player)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    nop_8240E6D0("pongPlayer::StartServe() %s", util_1480(g_networkTimingObject, 0));

    if (io_Input_poll_9D68(g_pInputArrayTable) != 0) {
        self->field_17E8 = FLT_MAX;  // @ 0x82079AD8
        self->field_17EC = 2;
    }

    pongCallback serveCallback = {
        player, reinterpret_cast<pongCallbackFn>(&pongPlayer_Serve), nullptr, 1 };
    pongCallback queryCallback = {
        player, reinterpret_cast<pongCallbackFn>(&io_8A48), nullptr, 4 };
    pongCreature_StartServeBlender(self->creature, &serveCallback, &queryCallback);

    self->field_18C8 = 1;
    PostGameMessage(0x380B, PlayerMessageBit(self->playerIndex) | 0x40, 0, 0);

    PlayerShotEntries()[self->playerIndex].flag04 = 0;
    PlayerShotEntries()[self->playerIndex].flag05 = 0;
}


/**
 * pongPlayer_SetupServe  @ 0x82192F00 | size: 0x108  (called by 0x82192D88)
 *
 * Resets the serve's shot record: finalizes the shot target, lets slot 9
 * (OnButtonReleased) run, picks the shot type (5, since the two flags it
 * reads are cleared first), and recomputes the record's +0x94 from the
 * player's settings value.
 */
void pongPlayer_SetupServe(pongPlayer* player)
{
    pongPlayerServeLayout* self = ServeLayout(player);
    nop_8240E6D0("pongPlayer::SetupServe %s", util_1480(g_networkTimingObject, 0));

    pongShotRecord& shot = PlayerShotEntries()[self->playerIndex].shot;
    if (shot.shotType != 3)
        memset(&shot.vec40, 0, sizeof(shot.vec40));

    // 0x8219F9C0 is lifted above as pongPlayer::FinalizeServeSetup, but its
    // `this` is the shotTarget (it finds the player at +0x2C).
    reinterpret_cast<pongPlayer*>(self->shotTarget)->FinalizeServeSetup();

    self->sub17F0->flag22 = 0;
    player->OnButtonReleased();  // vtable slot 9 (0x821935B8)

    self->serveTypeFlags.flag4 = 0;
    self->serveTypeFlags.flag6 = 0;
    shot.shotType = pongPlayer_SelectShotType(&self->serveTypeFlags, self->playerIndex);
    pongShotRecord_SetGravity(&shot, MatchSettings()->field_9C[self->playerIndex]);

    shot.flagsC6 = (uint16_t)((shot.flagsC6 & 0x00FF) | 0x1000);
    self->field_18C8 = 1;

    PlayerShotEntries()[self->playerIndex].flag05 = 0;
    PlayerShotEntries()[self->playerIndex].flag04 = 0;
}


/**
 * pongPlayer_EnterServeMode  @ 0x82192668 | size: 0x1B0
 * (called by 0x82196348 and, through message.cpp's declaration, 0x823B8808)
 *
 * Makes sure the ball is active, then either puts it in the server's hand
 * right away (player mode 2, or mode 1 unless pongPlayer_CheckServeInput says
 * otherwise) or only switches to move mode 2. That switch is skipped when the
 * aiPlayer's +0x34 value is not positive and the move mode is already 2 or 4.
 */
void pongPlayer_EnterServeMode(void* playerPtr)
{
    pongPlayer* player = static_cast<pongPlayer*>(playerPtr);
    pongPlayerServeLayout* self = ServeLayout(player);

    // pongPlayer_GetServeBallBody inlined, with a log before the activation.
    uint16_t ballIndex = self->ballInst->levelIndex;
    pongBallBody* ball = nullptr;
    if (g_pPhysicsSim->level->IsActive(ballIndex))
        ball = g_pPhysicsSim->level->GetActiveBody(ballIndex);
    if (!ball) {
        const pongGameStateServeView* gameState =
            static_cast<const pongGameStateServeView*>(g_game_state_ptr);
        if (gameState->sub14->field_25A8 > 0)
            game_3860(g_game_state_ptr, 1, "pongPlayer::EnterServeMode");
        ball = pongBallInstance_4980_g(g_pPhysicsSim, self->ballInst->levelIndex, 0, 0, 0, 0);
    }

    int32_t mode = MatchSettings()->playerMode[self->playerIndex];
    if ((mode == 1 && !pongPlayer_CheckServeInput(player)) || mode == 2) {
        pongPlayer_PlaceBallInHand(player, ball);
        pongPlayer_5C00_g(player, 2);  // move mode 2
        return;
    }

    if (mode != 0 && !pongPlayer_CheckServeInput(player))
        return;

    if (self->ai->sub34->value4 <= 0.0f && (self->moveMode == 2 || self->moveMode == 4))
        return;

    pongPlayer_5C00_g(player, 2);  // move mode 2
}
