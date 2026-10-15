// pong_drill.cpp — Training drill implementations | Rockstar Presents Table Tennis (Xbox 360, 2006)

/**
 * Training Drill Classes Implementation
 * Rockstar Presents Table Tennis (Xbox 360)
 */

#include "pong_drill.hpp"
#include "globals.h"
#include "game/pong_strings.hpp"
#include <stdio.h>
#include <string.h>
#include <math.h>

// External function declarations
extern "C" {
    void NotifyUIEvent(int eventId, int flags, int param3, int param4);  // pg_E6E0 @ 0x8225E6E0
    void SetTrainingState(void* pStateMachine, int nState);             // atSingleton_E9F8_w @ 0x821EE9F8
    void rage_debugLog(const char* message);  // @ 0x8240E6D0 (empty in this build)
    void xmlNodeStruct_vfn_2(void* self);  // @ base class PostLoadProperties
}

// Game state globals
extern struct pongGameState* g_pGameState;   // @ 0x82606430 (SDA+25648) — player/game state manager
extern void*      g_pTrainingStateMachine;   // @ 0x8271A34C — training HSM singleton
// The object behind 0x8271A31C, as far as the drills read it: the save data
// keeps 12 words per drill set, and +0x04 picks the set.
struct pongTrainingProgress {
    uint32_t _unk00;
    int32_t  m_drillSetIndex;  // +0x04
};
extern pongTrainingProgress* g_pTrainingData;  // @ 0x8271A31C
extern int32_t*   g_pDrillSaveData;          // @ 0x8271A35C — best rank per drill, 12 words per set

// PRNG state (Multiply-With-Carry LCG)
extern uint32_t   g_prngState[2];            // @ 0x825CA2C8 — [0]=seed, [1]=carry
extern float      g_fPrngNormalize;          // @ 0x82079E68 — 1.0f / 2^23, scales 23-bit int to [0,1)

// Drill score scaling constant
extern float      g_fDrillScoreScale;        // @ 0x8202C504 — multiplier for bonus score computation

// ── Objects the drills drive, as far as they touch them (their own headers
// belong to other files) ──────────────────────────────────────────────────

struct alignas(16) DrillVector4 {  // a VMX vector in the game
    float x, y, z, w;
};

// gmPracticeTarget (pong_match.hpp), the fields the drill touches.
struct DrillPracticeTarget {
    uint8_t _pad00[0x14];
    bool    m_visible;        // +0x14
    uint8_t _pad15[2];
    bool    m_clampToTable;   // +0x17 SetPosition keeps the target on the table while set
    uint8_t _pad18[0x4C];
    bool    m_spinStopped;    // +0x64 set by IsPointOnTarget on a hit
};
extern DrillPracticeTarget* g_pPracticeTarget;  // @ 0x826063A8

// hudTrainingHUD (hud.hpp), the fields the drill touches.
struct DrillTrainingHud {
    uint8_t _pad00[0x98];
    char    m_timeText[32];   // +0x98 clock text; +0xB8 is pushed as "arrow_direction"
};
extern DrillTrainingHud* g_pTrainingHud;  // @ 0x82606614

struct DrillTransform {
    DrillVector4 m_axes[3];
    DrillVector4 m_position;  // +0x30
};

// The object at 0x825EAB28 (g_input_obj_ptr elsewhere). 0x821C9CD0 gives the
// play area of one side of it; the matrix at +0x44 is the one whose position
// the drill tests against the target and places targets around.
struct DrillMatchView {
    uint8_t               _pad00[0x44];
    const DrillTransform* m_pPlayerTransform;  // +0x44
};
extern void* g_input_obj_ptr;  // @ 0x825EAB28

// The game state at 0x82606430: each player's aiming reticle.
struct DrillReticle {
    uint8_t _pad00[0x18];
    bool    m_enabled;        // +0x18 pongTrainingDrill::Start sets it from EnableReticle
};
struct DrillPlayerView {
    uint8_t       _pad00[0x1840];
    DrillReticle* m_pReticle; // +0x1840
};
struct DrillGameStateView {
    uint8_t          _pad00[0x74];
    DrillPlayerView* m_players[4];   // +0x74
    int32_t          m_activePlayer; // +0x84
};

// Class id of gdDrillMovementData for the config's IsOfType (slot 20).
extern uint32_t g_gdDrillMovementData_classId;  // @ 0x825C6BC4

// Multiply-with-carry generator shared by the drills (state at 0x825CA2C8).
// Returns the next 23 random bits as a float; times g_fPrngNormalize that is [0, 1).
static inline float NextRandomBits() {
    uint64_t next = (uint64_t)g_prngState[0] * 0x5CDCFAA7u + g_prngState[1];
    g_prngState[0] = (uint32_t)next;
    g_prngState[1] = (uint32_t)(next >> 32);
    return (float)(g_prngState[0] & 0x7FFFFF);
}

extern "C" int _snprintf(char* buffer, size_t count, const char* format, ...);
extern void PostPageGroupMessageFmt(uint32_t messageId, uint32_t mask, const char* format, ...);  // @ 0x8225E480
extern int  RoundHalfAwayFromZero(float value);                                       // @ 0x8210CB88
extern void hudTrainingHUD_SetCompleted(DrillTrainingHud* hud, int count);            // @ 0x822FA818
extern void hudTrainingHUD_SetTimeLow(DrillTrainingHud* hud, bool low);               // @ 0x822FA878
// Pushes the HUD's +0xB8 as "arrow_direction". Every caller passes 0 in r4;
// the callee never reads it.
extern void hudTrainingHUD_PushArrowDirection(DrillTrainingHud* hud, int unused);     // @ 0x822FA8F0
// Corners of side `side`'s play area: (min.x, 0, min.z) and (max.x, 0, max.z).
extern void DrillMatch_GetSideBounds(  // @ 0x821C9CD0
    DrillMatchView* match, int side, DrillVector4* pMin, DrillVector4* pMax);
// Moves the target to `position` (w = radius); clamps it to the table while
// m_clampToTable is set.
extern void gmPracticeTarget_SetPosition(  // @ 0x82113BA8
    DrillPracticeTarget* target, const DrillVector4* position);
// Shows one of the table target sets (gmPracticeTarget, 0x821137B0).
extern void gmPracticeTarget_SelectSet(  // @ 0x821137B0
    DrillPracticeTarget* target, int32_t setId, int arg2, int arg3);
// Whether `point` (x/z) is inside the active target zone; sets m_spinStopped on a
// hit. Every caller leaves r4 unset and the callee reads neither it nor `radius`.
extern bool gmPracticeTarget_IsPointOnTarget(  // @ 0x82113C38
    DrillPracticeTarget* target, int unused, const DrillVector4* point, float radius);

static inline DrillReticle* ActivePlayerReticle() {
    DrillGameStateView* state = reinterpret_cast<DrillGameStateView*>(g_pGameState);
    return state->m_players[state->m_activePlayer]->m_pReticle;
}

static inline bool ConfigIsOfType(pongTrainingDrillConfig* config, uint32_t classId) {
    typedef bool (*IsOfTypeFn)(pongTrainingDrillConfig*, uint32_t);
    return reinterpret_cast<IsOfTypeFn>(config->vtable[20])(config, classId);
}

// True when the clock went from above `mark` to at or below it this frame.
static inline bool PassedMark(float before, float now, float mark) {
    return before > mark && now <= mark;
}


// Default for m_timeRemaining: -1, "no time limit". A .data word, so loaded.
extern float g_fDrillDefaultTime;   // @ 0x825C5938

inline void pongTrainingDrill::ResetCounters() {
    m_timeRemaining = g_fDrillDefaultTime;
    m_numAttempts = 0;
    m_numSuccesses = 0;
    m_prevSuccesses = 0;
    m_rank = 0;
    m_completionFlag = 0;
    m_targetIndex = 0xFFFFFFFF;  // no target
}

inline void pongTrainingDrill::TickTimeLimit(float dt) {
    if (m_timeRemaining > 0.0f) {
        m_timeRemaining -= dt;
        if (m_timeRemaining <= 0.0f) {
            m_timeRemaining = g_fDrillDefaultTime;
            NotifyUIEvent(0x10, 0x40, 0, 0);
        }
    }
}

/**
 * pongTrainingDrill::Init
 * @ 0x8210CDB8 | size: 0x30
 *
 * Clears the counters and the rank, puts the time limit back to its default
 * and forgets the target. pongDrillMovement::Init repeats this inline.
 */
void pongTrainingDrill::Init() {
    ResetCounters();
}

/**
 * pongTrainingDrill::SetConfig
 * @ 0x8210CDA0 | size: 0x8 (vfn_1)
 *
 * Stores the drill configuration pointer at +32 (m_pConfig).
 */
void pongTrainingDrill::SetConfig(pongTrainingDrillConfig* pConfig) {
    m_pConfig = pConfig;
}

/**
 * pongTrainingDrill::CallInit
 * @ 0x8210CDA8 | size: 0x10 (vfn_2)
 *
 * Thin thunk: dispatches to vtable slot 3 (Init) via virtual call.
 * Original loads vtable[12/4]=vtable[3] and jumps through CTR.
 */
void pongTrainingDrill::CallInit() {
    // vtable slot 3 (byte offset 12) → Init()
    (*(void(**)(pongTrainingDrill*))((*(void***)this) + 3))(this);
}

/**
 * pongTrainingDrill::Update
 * @ 0x8210D098 | size: 0x4C (vfn_6)
 *
 * Per-frame tick: runs down the optional time limit. pongDrillMovement::Update
 * starts with the same code inline.
 */
void pongTrainingDrill::Update(float dt) {
    TickTimeLimit(dt);
}

/**
 * pongTrainingDrill::IsFinished
 * @ 0x8210D0E8 | size: 0x40 (vfn_7)
 *
 * The drill is over once every try has been used; *pPassed then says
 * whether the player reached MinNumSuccesses.
 */
bool pongTrainingDrill::IsFinished(bool* pPassed) {
    if (m_numAttempts < m_pConfig->m_totalNumTries) {
        return false;
    }
    *pPassed = m_numSuccesses >= m_pConfig->m_minNumSuccesses;
    return true;
}

/**
 * pongTrainingDrill::Render
 * @ 0x8210D290 | size: 0x80 (vfn_10)
 *
 * Composed dispatch: calls OnRallyEnd (vfn_29) to randomize a rally
 * value, then calls OnPointScored (vfn_30) to choose the robot target
 * and compute spin. Afterwards it copies the configured progress target
 * (m_pConfig+40) to the event structure at +48, and dispatches
 * vfn_31 (unnamed — post-render hook).
 *
 * @param pEvent  Per-frame render/event context; receives progress
 *                target at +48 and is passed to OnRallyEnd/OnPointScored.
 */
void pongTrainingDrill::Render(void* pEvent) {
    // 1. Randomize rally data via virtual dispatch (vfn_29)
    OnRallyEnd(pEvent);

    // 2. Choose robot target + compute spin vector (vfn_30)
    typedef void (*OnPointScoredFn)(pongTrainingDrill*, void*);
    OnPointScoredFn fnPoint = (OnPointScoredFn)(((void***)this)[0][30]);
    fnPoint(this, pEvent);

    // 3. Copy progress target from config (+40) into event (+48)
    uint32_t nProgressTarget = *(uint32_t*)((uint8_t*)m_pConfig + 40);
    *(uint32_t*)((uint8_t*)pEvent + 48) = nProgressTarget;

    // 4. Dispatch trailing post-render hook (vfn_31, unnamed)
    typedef void (*PostRenderFn)(pongTrainingDrill*, void*);
    PostRenderFn fnPost = (PostRenderFn)(((void***)this)[0][31]);
    fnPost(this, pEvent);
}

/**
 * pongTrainingDrill::OnSuccess
 * @ 0x8210D310 | size: 0x10 (vfn_11)
 *
 * Resets the countdown timer by copying the default time constant
 * (@ 0x8202CFE8, 0.0f) into m_timeRemaining. Used when the player
 * completes a sub-objective and the drill should hold the current
 * timer state.
 */
void pongTrainingDrill::OnSuccess() {
    // Load hold value from .rdata @ 0x8202CFE8
    const float kHoldTime = 0.0f;  // lbl_8202CFE8
    m_timeRemaining = kHoldTime;
}

/**
 * pongTrainingDrill::IsScoreValid
 * @ 0x8210D320 | size: 0x20 (vfn_12)
 *
 * Reads m_pConfig->m_tableTargetSetID (+44). Returns true when the
 * threshold is >= 0 (i.e. a finite threshold is set); returns false
 * when negative (interpreted as "unlimited / no threshold").
 *
 * @return true if config specifies a valid score threshold
 */
bool pongTrainingDrill::IsScoreValid() {
    int32_t nThreshold = (int32_t)*(int32_t*)((uint8_t*)m_pConfig + 44);
    return (nThreshold >= 0);
}

/**
 * pongTrainingDrill::GetTimeLimit
 * @ 0x8210D340 | size: 0xC (vfn_13)
 *
 * @return  m_pConfig->m_aimDelay  (+52)
 */
float pongTrainingDrill::GetTimeLimit() {
    return m_pConfig->m_aimDelay;
}

/**
 * pongTrainingDrill::GetMaxTime
 * @ 0x8210D350 | size: 0xC (vfn_14)
 *
 * @return  m_pConfig->m_postPointDelay  (+56)
 */
float pongTrainingDrill::GetMaxTime() {
    return m_pConfig->m_postPointDelay;
}

/**
 * pongTrainingDrill::GetDrillCategory
 * @ 0x8210CC70 | size: 0x8 (vfn_15)
 *
 * Returns the fixed drill-category ID for the training-drill group.
 * All base drills share category 5 in the HSM enum.
 *
 * @return 5 — training-drill category
 */
int pongTrainingDrill::GetDrillCategory() {
    return 5;
}

/**
 * pongTrainingDrill::GetProgressTarget
 * @ 0x8210D360 | size: 0xC (vfn_16)
 *
 * @return  m_pConfig->m_unlockDrillName  (+68)
 */
uint32_t pongTrainingDrill::GetProgressTarget() {
    return m_pConfig->m_unlockDrillName;
}

/**
 * pongTrainingDrill::GetScore
 * @ 0x8210CBD8 | size: 0x8 (vfn_23)
 *
 * Returns the current success counter — the raw score used by the
 * result screen and UI HUD.
 *
 * @return m_numSuccesses  (+8)
 */
uint32_t pongTrainingDrill::GetScore() {
    // Original loads from +16, which is m_rank in this layout.
    // Matches the IDA-named 'score' slot stored in that field.
    return m_rank;
}

/**
 * pongTrainingDrill::GetDifficulty
 * @ 0x8210D370 | size: 0xC (vfn_24)
 *
 * @return  m_pConfig->m_enableReticle  (+48, byte)
 */
uint8_t pongTrainingDrill::GetDifficulty() {
    return *(uint8_t*)((uint8_t*)m_pConfig + 48);
}

/**
 * pongTrainingDrill::ApplyTargetSet
 * @ 0x8210D380 | size: 0x7C (vfn_25)
 *
 * For drills that use table targets (slot 12) and have a drill type of their
 * own, shows the config's TableTargetSetID on the practice target.
 */
void pongTrainingDrill::ApplyTargetSet() {
    if (!IsScoreValid()) {
        return;
    }
    if (GetDrillTypeIndex() == 0) {
        return;
    }
    gmPracticeTarget_SelectSet(g_pPracticeTarget, m_pConfig->m_tableTargetSetID, -1, 1);
}

/**
 * pongTrainingDrill::IncreaseNumSuccesses
 * @ 0x8210D400 | size: 0x84 (vfn_26)
 *
 * Adds to the successes, capped at TotalNumTries, shows the count on the
 * HUD ("completed") and posts 0x5008.
 */
void pongTrainingDrill::IncreaseNumSuccesses(int increment) {
    m_numSuccesses += increment;
    int32_t totalNumTries = m_pConfig->m_totalNumTries;
    if (m_numSuccesses > totalNumTries) {
        rage_debugLog("pongTrainingDrill::IncreaseNumSuccesses() - winning more than total possible, "
                      "something is wrong");
        m_numSuccesses = totalNumTries;
    }
    hudTrainingHUD_SetCompleted(g_pTrainingHud, m_numSuccesses);
    PostPageGroupMessageFmt(0x5008, 0x40, "i", 1);
}

/**
 * pongTrainingDrill::Finish
 * @ 0x8210CFF0 | size: 0xA4 (vfn_5)
 *
 * Ends the drill: posts 0x5004, turns the active player's reticle off,
 * computes the final rank (saving it if it beats the best), runs slot 28 and
 * moves the training state machine to state 5.
 */
void pongTrainingDrill::Finish() {
    NotifyUIEvent(0x5004, 0x40, 0, 0);

    DrillReticle* reticle = ActivePlayerReticle();
    if (reticle != nullptr) {
        reticle->m_enabled = false;
    }
    UpdateRank(true);
    OnBallMiss();  // slot 28
    SetTrainingState(g_pTrainingStateMachine, 5);
}

/**
 * pongTrainingDrill::UpdateRank
 * @ 0x8210D488 | size: 0x144 (324 bytes)
 *
 * Rates the drill 1..5 once the player has MinNumSuccesses: 5 when every
 * try beyond the minimum succeeded, otherwise the floored share of them,
 * at least 1. With saveBest, a rank above the saved best for this drill
 * replaces it and posts 0x500B.
 *
 * @param saveBest  check and update the drill's saved best rank
 *
 * Key addresses:
 *   - g_fDrillScoreScale  (0x8202C504) — scaling multiplier for bonus score
 *   - g_pTrainingData     (0x8271A31C) — +4 gives drill-set index
 *   - g_pDrillSaveData    (0x8271A35C) — per-drill save array
 */
void pongTrainingDrill::UpdateRank(bool saveBest) {
    int32_t nSuccesses = (int32_t)m_numSuccesses;
    int32_t nRequired  = (int32_t)m_pConfig->m_minNumSuccesses;

    // Only compute score if player has met or exceeded the requirement
    if (nSuccesses < nRequired) {
        return;
    }

    int32_t nMaxTotal = (int32_t)m_pConfig->m_totalNumTries;
    int32_t nRange = nMaxTotal - nRequired;

    if (nRange == 0) {
        // No extra shots available — assign default score of 5
        m_rank = 5;
    } else {
        // Compute performance score: how far into the extra range the player reached
        int32_t nExcess = nSuccesses - nRequired;
        float fRatio  = (float)nExcess / (float)nRange;
        float fScaled = fRatio * g_fDrillScoreScale;
        int nScore = RoundHalfAwayFromZero(floorf(fScaled));

        // Clamp to minimum of 1
        if (nScore < 1) {
            nScore = 1;
        }
        m_rank = (uint32_t)nScore;
    }

    // If save-data update is enabled, check and update the player's best score
    if (!saveBest) {
        return;
    }

    // Load drill-set index from training data manager (+4)
    int32_t nDrillSetIdx = g_pTrainingData->m_drillSetIndex;

    // Get this drill's type index via virtual dispatch (vfn_17)
    int nDrillTypeIdx = GetDrillTypeIndex();

    // Compute save data array index: stride = drillSetIdx * 12, entry = stride + typeIdx + 3
    int nSaveIdx = nDrillSetIdx * 12 + nDrillTypeIdx + 3;
    int32_t nSavedBest = (int32_t)g_pDrillSaveData[nSaveIdx];

    // Only update if current score exceeds saved best
    if (nSavedBest >= (int32_t)m_rank) {
        return;
    }

    // Re-query drill type index (matches original — two VCALLs in scaffold)
    nDrillTypeIdx = GetDrillTypeIndex();
    nSaveIdx = nDrillSetIdx * 12 + nDrillTypeIdx + 3;

    // Write new best score and notify UI
    g_pDrillSaveData[nSaveIdx] = m_rank;
    NotifyUIEvent(20491, 64, 0, 0);
}

/**
 * pongTrainingDrill::OnRallyEnd
 * @ 0x8210D660 | size: 0xD4 (212 bytes)
 *
 * Called when a rally ends. If the drill config specifies a valid
 * random range (min > 0, max > 0, min <= max), generates a random
 * float in [min, max] using a Multiply-With-Carry PRNG and stores
 * it at pRallyEvent+128. If min == max, stores the exact value.
 *
 * PRNG details:
 *   - Multiply-With-Carry LCG: next = seed * 0x5CDCFAA7 + carry
 *   - Extracts 23-bit random, normalizes to [0,1), lerps in [min, max]
 *   - State at 0x825CA2C8: [0]=seed, [1]=carry
 *
 * @param pRallyEvent  Rally event data; result written to +128
 */
void pongTrainingDrill::OnRallyEnd(void* pRallyEvent) {
    float fMin = m_pConfig->m_minBallSpeed;
    float fMax = m_pConfig->m_maxBallSpeed;

    // Validate: both must be positive and min <= max
    if (!(fMin > 0.0f && fMax > 0.0f && fMin <= fMax)) {
        return;
    }

    // If min == max, store exact value (no randomness needed)
    if (fMin == fMax) {
        *(float*)((uint8_t*)pRallyEvent + 128) = m_pConfig->m_minBallSpeed;
        return;
    }

    // Generate random float in [min, max] using MWC-LCG
    uint32_t nSeed  = g_prngState[0];
    uint32_t nCarry = g_prngState[1];
    uint64_t nNext  = (uint64_t)nSeed * 0x5CDCFAA7ULL + nCarry;

    uint32_t nNewSeed  = (uint32_t)nNext;
    uint32_t nNewCarry = (uint32_t)(nNext >> 32);
    g_prngState[0] = nNewSeed;
    g_prngState[1] = nNewCarry;

    // Extract 23-bit random value and normalize to [0, 1)
    uint32_t nRandomBits = nNewSeed & 0x7FFFFF;
    float fNormalized = (float)nRandomBits * g_fPrngNormalize;

    // Lerp: result = min + (max - min) * t
    float fRange  = fMax - fMin;
    float fResult = fRange * fNormalized + fMin;
    *(float*)((uint8_t*)pRallyEvent + 128) = fResult;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongDrillMovement — "Movement" drill (vtable 0x82031CCC)
//
// A target appears on the floor on the player's side of the table; the player
// runs onto it. Each try places a new target (NextAttempt), a hit counts once
// the player's position is inside the target (Update), and the rank depends on
// how much of DrillTime was left after the last target (UpdateRank). The drill
// ends when the clock runs out or every try was used.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * pongDrillMovement::SetConfig
 * @ 0x8210DAE0 | size: 0x64 (vfn_1)
 *
 * Keeps the config, and also as m_pMovementData when it is a gdDrillMovementData.
 */
void pongDrillMovement::SetConfig(pongTrainingDrillConfig* pConfig) {
    m_pConfig = pConfig;
    if (ConfigIsOfType(pConfig, g_gdDrillMovementData_classId)) {
        m_pMovementData = static_cast<pongDrillMovementConfig*>(pConfig);
    }
}

/**
 * pongDrillMovement::Init
 * @ 0x8210DB48 | size: 0x54 (vfn_3)
 *
 * pongTrainingDrill::Init (inline), then a full clock and no target.
 */
void pongDrillMovement::Init() {
    ResetCounters();
    m_finished = false;
    m_timeLeft = m_pMovementData->m_drillTime;
    m_targetSide = TARGET_NONE;
    m_hitHoldTimer = 0.0f;
    m_urgentShown = false;
}

/**
 * pongDrillMovement::Start
 * @ 0x8210DBA0 | size: 0xA4 (vfn_4)
 *
 * After the common start: shows the clock, clears "time_low", turns the
 * player's reticle off and lets the target leave the table.
 */
void pongDrillMovement::Start() {
    pongTrainingDrill::Start();
    hudTrainingHUD_PushArrowDirection(g_pTrainingHud, 0);
    UpdateTimeDisplay();
    hudTrainingHUD_SetTimeLow(g_pTrainingHud, false);

    DrillReticle* reticle = ActivePlayerReticle();
    if (reticle != nullptr) {
        reticle->m_enabled = false;
    }
    g_pPracticeTarget->m_clampToTable = false;
}

/**
 * pongDrillMovement::Finish
 * @ 0x8210DC48 | size: 0x30 (vfn_5)
 */
void pongDrillMovement::Finish() {
    pongTrainingDrill::Finish();
    hudTrainingHUD_PushArrowDirection(g_pTrainingHud, 0);
}

/**
 * pongDrillMovement::Update
 * @ 0x8210DC78 | size: 0x210 (vfn_6)
 *
 * Runs the clock (beeping, message 0x1806, as it passes 5, 4, 3, 2 and 1
 * seconds) and ends the drill at 0. While no hit is being held, a player
 * standing on the target scores a success (message 0x5008); TargetHitTime
 * later the next try starts.
 */
void pongDrillMovement::Update(float dt) {
    TickTimeLimit(dt);  // pongTrainingDrill::Update, inline
    if (m_finished) {
        return;
    }

    float before = m_timeLeft;
    m_timeLeft = before - dt;
    // 4 and 3 are .data words in the original, 5, 2 and 1 .rdata.
    if (PassedMark(before, m_timeLeft, 5.0f) || PassedMark(before, m_timeLeft, 4.0f) ||
        PassedMark(before, m_timeLeft, 3.0f) || PassedMark(before, m_timeLeft, 2.0f) ||
        PassedMark(before, m_timeLeft, 1.0f)) {
        NotifyUIEvent(0x1806, 0x40, 0, 0);
    }
    UpdateTimeDisplay();

    if (m_timeLeft <= 0.0f) {
        m_timeLeft = 0.0f;
        m_finished = true;
        return;
    }

    if (m_hitHoldTimer > 0.0f) {
        m_hitHoldTimer -= dt;
        if (m_hitHoldTimer <= 0.0f) {
            m_hitHoldTimer = 0.0f;
            NextAttempt(1);
        }
        return;
    }

    DrillMatchView* match = static_cast<DrillMatchView*>(g_input_obj_ptr);
    if (gmPracticeTarget_IsPointOnTarget(g_pPracticeTarget, 0, &match->m_pPlayerTransform->m_position,
                                         m_pMovementData->m_detectRadius)) {
        m_numSuccesses++;
        PostPageGroupMessageFmt(0x5008, 0x40, "i", 1);
        m_hitHoldTimer = m_pMovementData->m_targetHitTime;
        if (m_hitHoldTimer <= 0.0f) {
            NextAttempt(1);
        }
    }
}

/**
 * pongDrillMovement::IsFinished
 * @ 0x8210DE88 | size: 0x38 (vfn_7)
 *
 * Like the base, *pPassed is set once every try is used; but the answer is
 * m_finished, which the clock can set first.
 */
bool pongDrillMovement::IsFinished(bool* pPassed) {
    if (m_numAttempts >= m_pConfig->m_totalNumTries) {
        *pPassed = m_numSuccesses >= m_pConfig->m_minNumSuccesses;
    }
    return m_finished;
}

/**
 * pongDrillMovement::NextAttempt
 * @ 0x8210DEC0 | size: 0x348 (vfn_9)
 *
 * After the base's bookkeeping: ends the drill (and hides the target) once
 * every try was used, otherwise puts the target somewhere new in the
 * player's half, TargetRadius plus 0.05 inside its edges. Sides alternate:
 * after a target beside the player (x) the next one is along an end (z) with
 * 90 % chance and vice versa; it goes to the side with more room. A target
 * beside the player lies between the player and that edge, at the near-z
 * edge; one along an end spans the whole width.
 */
void pongDrillMovement::NextAttempt(int count) {
    pongTrainingDrill::NextAttempt(count);

    if (m_numAttempts > m_pMovementData->m_totalNumTries) {
        g_pPracticeTarget->m_visible = false;
        m_finished = true;
        return;
    }

    DrillMatchView* match = static_cast<DrillMatchView*>(g_input_obj_ptr);
    DrillVector4 areaMin, areaMax;
    DrillMatch_GetSideBounds(match, 0, &areaMin, &areaMax);

    // Chance of a target beside the player (x) rather than along an end (z).
    float besideChance = 0.5f;
    switch (m_targetSide) {
    case TARGET_LOW_X:
    case TARGET_HIGH_X:
        besideChance = 0.1f;
        break;
    case TARGET_NEAR_Z:
    case TARGET_FAR_Z:
        besideChance = 0.9f;  // a .data word in the original
        break;
    }

    const float kEdgeMargin = 0.05f;
    DrillVector4 player = match->m_pPlayerTransform->m_position;
    DrillVector4 target = {0.0f, 0.0f, 0.0f, 0.0f};
    float xLo, xHi, zLo, zHi;
    bool randomZ = false;

    if (NextRandomBits() * g_fPrngNormalize < besideChance) {
        float radius = m_pMovementData->m_targetRadius;
        if (areaMax.x - player.x > player.x - areaMin.x) {
            m_targetSide = TARGET_HIGH_X;
            xLo = player.x + radius + kEdgeMargin;
            xHi = areaMax.x - radius - kEdgeMargin;
        } else {
            m_targetSide = TARGET_LOW_X;
            xLo = areaMin.x + radius + kEdgeMargin;
            xHi = player.x - radius - kEdgeMargin;
        }
        zLo = areaMin.z + radius + kEdgeMargin;
        zHi = areaMax.z - radius - kEdgeMargin;  // computed, but z stays at zLo
    } else {
        float radius = m_pMovementData->m_targetRadius;
        xLo = areaMin.x + radius + kEdgeMargin;
        xHi = areaMax.x - radius - kEdgeMargin;
        if (player.z - areaMin.z > areaMax.z - player.z) {
            m_targetSide = TARGET_NEAR_Z;
            zLo = areaMin.z + radius + kEdgeMargin;
        } else {
            m_targetSide = TARGET_FAR_Z;
            zLo = areaMax.z - radius - kEdgeMargin;
        }
        zHi = zLo;
        randomZ = true;  // over an empty range: still draws a number
    }

    target.x = (xHi - xLo) * NextRandomBits() * g_fPrngNormalize + xLo;
    target.y = m_pMovementData->m_verticalOffset;
    if (randomZ) {
        target.z = (zHi - zLo) * NextRandomBits() * g_fPrngNormalize + zLo;
    } else {
        target.z = zLo;
    }
    target.w = m_pMovementData->m_targetRadius;

    DrillPracticeTarget* practiceTarget = g_pPracticeTarget;
    practiceTarget->m_spinStopped = false;
    practiceTarget->m_clampToTable = false;
    gmPracticeTarget_SetPosition(practiceTarget, &target);
    practiceTarget->m_visible = true;
}

/**
 * pongDrillMovement::UpdateRank
 * @ 0x8210E208 | size: 0x16C (vfn_27)
 *
 * Rank 0 when the clock ran out before every target was reached. Reaching
 * them all with at least DrillTime - HighestRankTime left is rank 5; less
 * time left scales down to 1. With saveBest, a rank above the saved best
 * for this drill replaces it and posts 0x500B.
 */
void pongDrillMovement::UpdateRank(bool saveBest) {
    const pongDrillMovementConfig* data = m_pMovementData;
    if (m_timeLeft <= 0.0f && m_numSuccesses < data->m_totalNumTries) {
        m_rank = 0;
    } else if (m_numSuccesses >= data->m_totalNumTries) {
        float topRankTime = data->m_drillTime - data->m_highestRankTime;
        if (m_timeLeft >= topRankTime) {
            m_rank = 5;
        } else {
            int rank = RoundHalfAwayFromZero(floorf(m_timeLeft / topRankTime * 5.0f));
            if (rank < 1) {
                rank = 1;
            }
            m_rank = rank;
        }
    }

    if (!saveBest) {
        return;
    }
    int slot = g_pTrainingData->m_drillSetIndex * 12 + GetDrillTypeIndex() + 3;
    if (g_pDrillSaveData[slot] >= m_rank) {
        return;
    }
    slot = g_pTrainingData->m_drillSetIndex * 12 + GetDrillTypeIndex() + 3;
    g_pDrillSaveData[slot] = m_rank;
    NotifyUIEvent(0x500B, 0x40, 0, 0);
}

/**
 * pongDrillMovement::UpdateTimeDisplay
 * @ 0x8210E378 | size: 0x118
 *
 * Writes the clock, rounded up to whole seconds, as "m:ss" into the HUD,
 * and raises "time_low" once when it drops to UrgentTime.
 */
void pongDrillMovement::UpdateTimeDisplay() {
    float seconds = ceilf(m_timeLeft);
    // RoundHalfAwayFromZero, inline here
    int totalSeconds = seconds >= 0.0f ? (int)(seconds + 0.5f) : (int)(seconds - 0.5f);
    int minutes = totalSeconds / 60;
    int secondsPart = totalSeconds % 60;

    char text[32];
    _snprintf(text, sizeof(text), secondsPart < 10 ? "%d:0%d" : "%d:%d", minutes, secondsPart);
    strncpy(g_pTrainingHud->m_timeText, text, sizeof(text));

    if (!m_urgentShown && m_timeLeft <= m_pMovementData->m_urgentTime) {
        hudTrainingHUD_SetTimeLow(g_pTrainingHud, true);
        m_urgentShown = true;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// hitTipData — XML data node for hit tip configuration
//
// Inherits from rage::xmlNodeStruct (2 vtables — multiple inheritance).
// Describes a play state tip that triggers based on shot type, score,
// and consecutive shot thresholds.
//
// Vtable 1 @ 0x82043300 (primary, 12 bytes)
// Vtable 2 @ 0x8204330C (secondary, 100 bytes)
// Inner class: hitTipData::xmlNodeStructGroupType @ 0x82043370
// ─────────────────────────────────────────────────────────────────────────────

// External type descriptor globals (used for XML property type tags)
extern uint32_t g_xmlType_ShotType;         // @ 0x825CB5B4 (.data, 4 bytes) — shot type enum descriptor
extern uint32_t g_xmlType_Int;              // @ 0x825CAF90 (.data, 4 bytes) — integer type descriptor
extern uint32_t g_xmlType_Bool;             // @ 0x825CAF94 (.data, 4 bytes) — boolean type descriptor

// XML property registration function
// Signature: RegisterProperty(this, propertyName, fieldPtr, typeDescriptor, flags)
extern void RegisterSerializedField(void* node, const char* name, void* field, void* typedesc, int flags);

// Base class destructor
extern void atSingleton_29E8_p25(void* obj);

// Type hash globals for IsApplicable checks
extern uint32_t g_tipType_Play1;            // @ 0x825C5EC4 (.data, 4 bytes)
extern uint32_t g_tipType_Play2;            // @ 0x825C803C (.data, 4 bytes)
extern uint32_t g_tipType_Play3;            // @ 0x825C8038 (.data, 4 bytes)

// Enum string lookup table for xmlNodeStructGroupType::GetGroupName
extern const char* g_shotTypeNames[];       // @ 0x8202D034 (.rdata, 24 bytes = 6 entries)

/**
 * hitTipData::~hitTipData() @ 0x821F2AB8 | size: 0x8
 *
 * Virtual destructor. Adjusts 'this' by -20 (to unwind MI offset)
 * and delegates to base class destructor at 0x821F29E8.
 */
hitTipData::~hitTipData() {
    // The MI destructor adjusts 'this' by -20 to reach the primary base
    // then calls the base xmlNodeStruct destructor chain
    // Original: addi r3,r3,-20; b atSingleton_29E8_p25
    atSingleton_29E8_p25((char*)this - 20);
}

/**
 * hitTipData::PostLoadProperties() @ 0x821F2298 | size: 0x88
 * vtable slot 2
 *
 * Validates XML properties after they are loaded from the data file.
 * Ensures ShotType is in range [0,5], and that the score/consecutive
 * fields have consistent values (or applies defaults).
 *
 * Assertion strings:
 *   @ 0x82043090 (26 bytes) — ShotType range assertion
 *   @ 0x820430AC (43 bytes) — score/consecutive consistency assertion
 */
void hitTipData::PostLoadProperties() {
    // Validate ShotType: must be in range [0, 5]
    if (m_shotType < 0 || m_shotType >= 6) {
        rage_debugLog("Invalid hit tip found: %d");  // string at 0x82043090
    }

    // Check score/consecutive field consistency
    if (m_consecutiveThreshold < 0) {
        if (m_scoreThreshold >= 0 && m_minScore >= 0) {
            // Both score and min thresholds are valid: call base and return
            xmlNodeStruct_vfn_2(this);
            return;
        }
        // Score fields invalid: log error and set default
        rage_debugLog("Invalid hit tip, setting InARow to default");  // string at 0x820430AC
        m_consecutiveThreshold = 2;  // Default to 2
    }

    // Call base class PostLoadProperties
    xmlNodeStruct_vfn_2(this);
}

/**
 * hitTipData::LoadProperties() @ 0x821F21D0 | size: 0xC8
 * vtable slot 21
 *
 * Registers 5 XML properties with the property system via RegisterSerializationField:
 *   - "ShotType"  → m_shotType     (+16), type: ShotType enum (@ 0x825CB5B4)
 *   - property2   → m_minScore     (+20), type: int (@ 0x825CAF90)
 *   - property3   → m_scoreThreshold (+24), type: int
 *   - property4   → m_consecutiveThreshold (+28), type: int
 *   - property5   → m_enabled      (+32), type: bool (@ 0x825CAF94)
 */
void hitTipData::LoadProperties() {
    // Register ShotType enum property
    // r4 = "ShotType" @ 0x82033438, r5 = this+16, r6 = &g_xmlType_ShotType @ 0x825CB5B4
    RegisterSerializedField(this, "ShotType", &m_shotType, &g_xmlType_ShotType, 0);

    // Register integer properties with type descriptor @ 0x825CAF90
    // r4 @ 0x82043070 (8 bytes), r5 = this+20
    RegisterSerializedField(this, "MinScore", &m_minScore, &g_xmlType_Int, 0);

    // r4 @ 0x82043078 (6 bytes), r5 = this+24
    RegisterSerializedField(this, "Score", &m_scoreThreshold, &g_xmlType_Int, 0);

    // r4 @ 0x82043080 (7 bytes), r5 = this+28
    RegisterSerializedField(this, "InARow", &m_consecutiveThreshold, &g_xmlType_Int, 0);

    // Register boolean property with type descriptor @ 0x825CAF94
    // r4 @ 0x82043088 (7 bytes), r5 = this+32
    RegisterSerializedField(this, "Active", &m_enabled, &g_xmlType_Bool, 0);
}

/**
 * hitTipData::IsApplicable() @ 0x821F2188 | size: 0x48
 * vtable slot 20
 *
 * Checks whether this tip data applies to the given type hash.
 * Compares against three global type hashes:
 *   - g_tipType_Play1 @ 0x825C5EC4
 *   - g_tipType_Play2 @ 0x825C803C
 *   - g_tipType_Play3 @ 0x825C8038
 *
 * @param typeHash  The type identifier to check against
 * @return true if this tip applies to the given type
 */
bool hitTipData::IsApplicable(uint32_t typeHash) {
    // Check against first two type hashes (either matches → true)
    if (typeHash == g_tipType_Play1 || typeHash == g_tipType_Play2) {
        return true;
    }

    // Check against third type hash
    return (typeHash == g_tipType_Play3);
}

/**
 * hitTipData::GetNodeTypeName() @ 0x82115BD8 | size: 0xC
 * vtable slot 22
 *
 * Returns the XML node type name string for this data class.
 * Used by the XML serialization system to identify node types.
 *
 * @return "HitTip" — the XML element name for hit tip data nodes
 */
const char* hitTipData::GetNodeTypeName() {
    return "HitTip";  // @ 0x820326DC (.rdata, "HitTip")
}

/**
 * hitTipData::xmlNodeStructGroupType::GetGroupName() @ 0x821F2130 | size: 0x18
 * vtable slot 5 of inner class xmlNodeStructGroupType @ 0x82043370
 *
 * Returns the display name for the shot type group based on index.
 * Looks up index from field +36 (m_groupIndex) in a 6-element string table
 * at 0x8202D034.
 *
 * The table contains shot type names (6 entries × 4 bytes = 24 bytes).
 *
 * @return The shot type group display name string
 */
const char* hitTipData_xmlNodeStructGroupType_GetGroupName(void* self) {
    // Read m_groupIndex from self+36
    uint32_t groupIndex = *(uint32_t*)((uint8_t*)self + 36);

    // Index into the shot type names table (shift left by 2 = multiply by 4)
    // Original: rlwinm r9,r10,2,0,29 → index * 4
    return g_shotTypeNames[groupIndex];
}

// gdDrillSoftShotData's class id; globals.c calls it g_drillCleanupParam.
extern uint32_t g_drillCleanupParam;  // @ 0x825C74FC

/**
 * pongDrillSoftShot::SetConfig
 * @ 0x8210EDA0 | size: 0x64 (vfn_1)
 *
 * Keeps the config, and also at +0x38 when it is a gdDrillSoftShotData.
 */
// @ 0x8210EDA0
void pongDrillSoftShot::SetConfig(pongTrainingDrillConfig* pConfig) {
    m_pConfig = pConfig;
    if (ConfigIsOfType(pConfig, g_drillCleanupParam)) {
        m_pSoftShotData = pConfig;
    }
}

/**
 * noSoftShotsTipData::PostLoadProperties @ 0x821F2678 | size: 0x48
 *
 * Validates that the provided type hash matches one of the allowed shot types
 * for the "no soft shots" tip. Returns true if the type is valid.
 *
 * This tip data validates against three specific shot type hashes stored in globals.
 */
bool noSoftShotsTipData::PostLoadProperties(uint32_t typeHash) {
    // Check against first allowed type
    if (typeHash == g_shotType1_825C5F50) {
        return true;
    }

    // Check against second allowed type
    if (typeHash == g_shotType2_825C803C) {
        return true;
    }

    // Check against third allowed type
    return (typeHash == g_shotType3_825C8038);
}

// =============================================================================
// pongDrill state-machine subclass vtable slots
// -----------------------------------------------------------------------------
// Each concrete drill subclass overrides three short slots off the base
// pongTrainingDrill vtable:
//   vfn_17 GetDrillTypeIndex  — integer drill-type tag used to index
//                               g_pDrillSaveData (see pongTrainingDrill::UpdateRank).
//                               Base returns 0; only Spin/FocusShot/
//                               CounterSpin/Smash override it.
//   vfn_18 GetConfigName      — pointer to the XML config-node name string.
//   vfn_21 HasActiveTarget    — returns true iff the subclass-specific target
//                               index field is in its "active" range
//                               (>= 0 or >= 1 depending on subclass).
//
// All addresses verified via mcp__tt-decomp__get_function_recomp. Offsets
// into the instance match the raw PPC loads in each scaffold.
// =============================================================================

// ── pongDrillMovement ────────────────────────────────────────────────────────

/**
 * pongDrillMovement::GetConfigName
 * @ 0x8210CBE0 | size: 0xC
 *
 * Returns the XML config node name for this drill.
 */
const char* pongDrillMovement::GetConfigName() {
    return "Movement";  // @ 0x820318F0 (.rdata, 9 bytes)
}

/**
 * pongDrillMovement::IsOver
 * @ 0x8210CBF0 | size: 0x8 (vfn_22)
 *
 * Whether the drill has ended: the clock ran out or every try was used.
 */
bool pongDrillMovement::IsOver() {
    return m_finished;
}

// ── pongDrillServeMeter ──────────────────────────────────────────────────────

/**
 * pongDrillServeMeter::GetConfigName
 * @ 0x8210CBF8 | size: 0xC
 */
const char* pongDrillServeMeter::GetConfigName() {
    return "Serve Meter";  // @ 0x820318FC (.rdata, 12 bytes)
}

/**
 * pongDrillServeMeter::HasActiveTarget
 * @ 0x8210CC20 | size: 0x1C
 *
 * Reads m_meterTargetIdx (+48). For the serve meter a target index of 1
 * or higher denotes an active phase; 0 (or negative) means idle.
 *
 * Original: lwz r11,48(r3); cmpwi r11,1; li r11,1; bge loc; li r11,0
 */
bool pongDrillServeMeter::HasActiveTarget() {
    return (int32_t)m_meterTargetIdx >= 1;
}

// ── pongDrillServing ─────────────────────────────────────────────────────────

/**
 * pongDrillServing::GetConfigName
 * @ 0x8210CC10 | size: 0xC
 */
const char* pongDrillServing::GetConfigName() {
    return "Serve Aim";  // @ 0x82031908 (.rdata, 10 bytes)
}

// ── pongDrillReturn ──────────────────────────────────────────────────────────

/**
 * pongDrillReturn::GetConfigName
 * @ 0x8210CC48 | size: 0xC
 */
const char* pongDrillReturn::GetConfigName() {
    return "Return";  // @ 0x82031914 (.rdata, 7 bytes)
}

/**
 * pongDrillReturn::HasActiveTarget
 * @ 0x8210CD80 | size: 0x1C
 *
 * Reads m_returnTargetIdx (+36). Non-negative index = active target.
 *
 * Original: lwz r11,36(r3); cmpwi r11,0; li r11,1; bge loc; li r11,0
 */
bool pongDrillReturn::HasActiveTarget() {
    return m_returnTargetIdx >= 0;
}

// ── pongDrillPlacement ───────────────────────────────────────────────────────

/**
 * pongDrillPlacement::GetConfigName
 * @ 0x8210CC60 | size: 0xC
 */
const char* pongDrillPlacement::GetConfigName() {
    return "Placement";  // @ 0x8203191C (.rdata, 10 bytes)
}

// ── pongDrillSoftShot ────────────────────────────────────────────────────────

/**
 * pongDrillSoftShot::GetConfigName
 * @ 0x8210CC78 | size: 0xC
 */
const char* pongDrillSoftShot::GetConfigName() {
    return "Soft Shot";  // @ 0x82031928 (.rdata, 10 bytes)
}

/**
 * pongDrillSoftShot::HasActiveTarget
 * @ 0x8210CC88 | size: 0x1C
 *
 * Reads m_softShotTargetIdx (+52). Non-negative index = active target.
 */
bool pongDrillSoftShot::HasActiveTarget() {
    return m_softShotTargetIdx >= 0;
}

// ── pongDrillCharging ────────────────────────────────────────────────────────

/**
 * pongDrillCharging::GetConfigName
 * @ 0x8210CCB0 | size: 0xC
 */
const char* pongDrillCharging::GetConfigName() {
    return "Charging";  // @ 0x82031934 (.rdata, 9 bytes)
}

/**
 * pongDrillCharging::HasActiveTarget
 * @ 0x8210CCC0 | size: 0x1C
 *
 * Reads m_chargingTargetIdx (+56). Non-negative index = active target.
 */
bool pongDrillCharging::HasActiveTarget() {
    return m_chargingTargetIdx >= 0;
}

// ── pongDrillSpin ────────────────────────────────────────────────────────────

/**
 * pongDrillSpin::GetDrillTypeIndex
 * @ 0x8210CCE0 | size: 0x8
 *
 * Returns the drill-type slot (7) for the Spin drill. The base class
 * returns 0; this override lets pongTrainingDrill::UpdateRank index the
 * proper slot in g_pDrillSaveData for save-data tracking.
 */
int pongDrillSpin::GetDrillTypeIndex() {
    return kDrillTypeSpin;  // 7
}

/**
 * pongDrillSpin::GetConfigName
 * @ 0x8210CCE8 | size: 0xC
 */
const char* pongDrillSpin::GetConfigName() {
    return "Spin";  // @ 0x82031940 (.rdata, 5 bytes)
}

/**
 * pongDrillSpin::HasActiveTarget
 * @ 0x8210CD10 | size: 0x1C
 *
 * Reads m_spinTargetIdx (+40). Non-negative index = active target.
 */
bool pongDrillSpin::HasActiveTarget() {
    return m_spinTargetIdx >= 0;
}

// ── pongDrillFocusShot ───────────────────────────────────────────────────────

/**
 * pongDrillFocusShot::GetDrillTypeIndex
 * @ 0x8210CCF8 | size: 0x8
 */
int pongDrillFocusShot::GetDrillTypeIndex() {
    return kDrillTypeFocusShot;  // 8
}

/**
 * pongDrillFocusShot::GetConfigName
 * @ 0x8210CD00 | size: 0xC
 */
const char* pongDrillFocusShot::GetConfigName() {
    return "Focus Shot";  // @ 0x82031948 (.rdata, 11 bytes)
}

// ── pongDrillCounterSpin ─────────────────────────────────────────────────────

/**
 * pongDrillCounterSpin::GetDrillTypeIndex
 * @ 0x8210CD30 | size: 0x8
 */
int pongDrillCounterSpin::GetDrillTypeIndex() {
    return kDrillTypeCounterSpin;  // 9
}

/**
 * pongDrillCounterSpin::GetConfigName
 * @ 0x8210CD38 | size: 0xC
 */
const char* pongDrillCounterSpin::GetConfigName() {
    return "Counter Spin";  // @ 0x82031954 (.rdata, 13 bytes)
}

/**
 * pongDrillCounterSpin::HasActiveTarget
 * @ 0x8210CD48 | size: 0x1C
 *
 * Reads m_counterSpinTargetIdx (+72). Non-negative index = active target.
 */
bool pongDrillCounterSpin::HasActiveTarget() {
    return m_counterSpinTargetIdx >= 0;
}

// ── pongDrillSmash ───────────────────────────────────────────────────────────

/**
 * pongDrillSmash::GetDrillTypeIndex
 * @ 0x8210CD68 | size: 0x8
 */
int pongDrillSmash::GetDrillTypeIndex() {
    return kDrillTypeSmash;  // 10
}

/**
 * pongDrillSmash::GetConfigName
 * @ 0x8210CD70 | size: 0xC
 */
const char* pongDrillSmash::GetConfigName() {
    return "Smash";  // @ 0x82031964 (.rdata, 6 bytes)
}
