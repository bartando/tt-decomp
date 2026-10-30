/**
 * hsm.cpp — Hierarchical State Machine primitives (proto-RAGE)
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * HSM/FSM base glue: context state transitions, nested state attachment,
 * event init, queued notifications, and helper jump-table dispatchers
 * that chain into hsmContext_SetNextState_2800.
 *
 * Real-implementation lifts:
 *   hsmContext_SetNextState_2800  @ 0x82222800 — one-hot transition engine
 *   hsmContext_5B40_w             @ 0x821C5B40 — mode-qualified transition (state 1)
 *   hsmContext_5BC8_fw            @ 0x821C5BC8 — zero-flag transition (state 2)
 *   jumptable_5C20                @ 0x821C5C20 — sticky-bit transition (state 2)
 *   jumptable_3A48                @ 0x82453A48 — event-dispatch init (types 1/2)
 *
 * No-op shims (no binary counterpart — link-only):
 *   hsmContext_Init, hsmContext_InitTimers, hsmEvent_Init,
 *   HSM_QueueNotification, PostStateTransitionRequest,
 *   SetTrainingState, gmLogic_StepFrame, gmLogic_StepFrame_impl.
 *
 * Callers access the transition engine through the suffixed symbol
 * `hsmContext_SetNextState_2800`; the asm-alias wrapper lives alongside
 * the plain `hsmContext_SetNextState` definition so the two linkages match.
 */

#include <cstdint>
#include <cstdio>
#include <cstring>

#include "rage/hsmState.hpp"  // hsmState class definition

// ─── hsmContext::SetNextState @ 0x82222800 ────────────────────────────────────
//
// Drives the one-hot transition automaton. The layout probed:
//   +0x00   vtable
//   +0x04   m_pManager
//   +0x10   m_currentState (int; -1 = unset)
//
// Flow mirrors the PPC recomp:
//   1. If a state is already assigned, the original called a debug-trace
//      path (`nop_8240E6D0` + name lookups via `game_28B8`). Those helpers
//      are no-ops in the release binary and not yet lifted here — we drop
//      the trace and retain the state-transition semantics.
//   2. Invoke vtable slot 5 (byte +20) — the state's CanTransition(int) gate.
//      A non-zero return commits the new state by writing +0x10.
//   3. On rejection, leave the state unchanged (same effect as the debug
//      branch minus the trace emit).
//
// NOTE: The asm-alias `_hsmContext_SetNextState_2800` below is what every
// downstream caller uses; keep the signatures bit-identical.

void hsmContext_SetNextState(void* context, int state) {  // @ 0x82222800
    if (!context) {
        return;
    }

    uint8_t*  self = reinterpret_cast<uint8_t*>(context);
    void**    vtbl = *reinterpret_cast<void***>(self);

    // Dispatch CanTransition via vtable slot 5 (byte +20 → index 5).
    using CanTransitionFn = uint8_t (*)(void*, int);
    CanTransitionFn canTransition =
        reinterpret_cast<CanTransitionFn>(vtbl[5]);
    uint8_t accept = canTransition(context, state);

    if (accept) {
        *reinterpret_cast<int32_t*>(self + 16) = state;
    }
    // else: rejected — no state mutation. Original emits a "denied" trace
    // via nop_8240E6D0 which we intentionally skip.
}

// asm-alias wrappers so C callers resolve the same body under both
// `_hsmContext_SetNextState_2800` (suffixed, legacy scaffolds) and
// `_hsmContext_SetNextState` (plain — used by `extern "C"` decls in ui/hud
// and .c translation units such as render_loop.c).
extern "C" void _c_hsmContext_SetNextState_2800(void* ctx, int state)
    __asm__("_hsmContext_SetNextState_2800");
extern "C" void _c_hsmContext_SetNextState_2800(void* ctx, int state) {
    hsmContext_SetNextState(ctx, state);
}
extern "C" void _c_hsmContext_SetNextState_plain(void* ctx, int state)
    __asm__("_hsmContext_SetNextState");
extern "C" void _c_hsmContext_SetNextState_plain(void* ctx, int state) {
    hsmContext_SetNextState(ctx, state);
}

// ─── hsmContext helpers @ 0x821C5B40 / 0x821C5BC8 / 0x821C5C20 ────────────────
// These are shared image pointer slots, not private sentinel pointers.
extern "C" void* g_hsmHelperContext;     // @ 0x8271A7C0
extern "C" void* g_hsmHelperNameSource;  // @ 0x8271A7C4

namespace {

// Shape of the HSM singleton accessed by these helpers.
struct HsmScratch {
    uint8_t  _pad_0[60];   // +0x00..+0x3B
    uint32_t mode_copy;    // +0x3C  (60)
    uint32_t flag_1;       // +0x40  (64)
    // +0x44 .. +0x14B8  — reserved; not touched here
    uint8_t  _pad_44[0x14B8 - 0x44];
    uint32_t flag_2;       // +0x14B8 (5304)
};

// Name-buffer stride for the strncpy branch in 5B40_w.
constexpr unsigned kNameBufferStride = 43u;

}  // namespace

// hsmContext_5B40_w @ 0x821C5B40 ---------------------------------------------
void hsmContext_5B40_w(void* obj) {
    if (!obj || !g_hsmHelperNameSource || !g_hsmHelperContext) {
        return;
    }

    uint8_t* modeRec = reinterpret_cast<uint8_t*>(obj);
    uint32_t mode    = *reinterpret_cast<uint32_t*>(modeRec + 532);
    uint32_t flag    = (mode == 4u) ? 3u : 1u;

    auto* hsm = reinterpret_cast<HsmScratch*>(g_hsmHelperContext);
    hsm->mode_copy = mode;
    hsm->flag_1    = flag;

    char* nameDst = reinterpret_cast<char*>(hsm) + 4996;
    const char* nameSrc = reinterpret_cast<const char*>(g_hsmHelperNameSource) + 45;
    std::strncpy(nameDst, nameSrc, kNameBufferStride);

    hsmContext_SetNextState(hsm, 1);

    // Final one-hot marker at byte (1<<16)|10220 = 0x127EC from `obj`.
    constexpr uint32_t kOneHotOffset = 0x127ECu;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(obj) + kOneHotOffset) = 1u;
}

// hsmContext_5BC8_fw @ 0x821C5BC8 --------------------------------------------
void hsmContext_5BC8_fw(void* obj) {
    if (!obj || !g_hsmHelperContext) {
        return;
    }

    uint8_t* modeRec = reinterpret_cast<uint8_t*>(obj);  // arg is ctx in this variant
    uint32_t mode    = *reinterpret_cast<uint32_t*>(modeRec + 532);

    auto* hsm = reinterpret_cast<HsmScratch*>(g_hsmHelperContext);
    hsm->mode_copy = mode;
    hsm->flag_2    = 0u;

    hsmContext_SetNextState(hsm, 2);

    constexpr uint32_t kOneHotOffset = 0x127ECu;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(obj) + kOneHotOffset) = 2u;
}

// jumptable_5C20 @ 0x821C5C20 ------------------------------------------------
// (State-machine free function — owned by the HSM partition per recomp alias.)
void jumptable_5C20(void* obj) {
    if (!obj || !g_hsmHelperContext) {
        return;
    }

    uint32_t mode  = *reinterpret_cast<uint32_t*>(
        reinterpret_cast<uint8_t*>(obj) + 532);
    uint32_t flag2 = (mode == 4u) ? 1024u : 16384u;

    auto* hsm = reinterpret_cast<HsmScratch*>(g_hsmHelperContext);
    hsm->mode_copy = mode;
    hsm->flag_2    = flag2;

    hsmContext_SetNextState(hsm, 2);

    constexpr uint32_t kOneHotOffset = 0x127ECu;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(obj) + kOneHotOffset) = 3u;
}

// ─── jumptable_3A48 @ 0x82453A48 ──────────────────────────────────────────────
//
// Event-descriptor initializer. Lays out a 24-byte slot:
//   +0x00   kind (u32, mirrored into +0x04 as a float constant)
//   +0x04   float constant (from .rdata @ +15784 / +15788, depending on kind)
//   +0x08   u16 channel
//   +0x0C   u32 payload
//   +0x10   kind (u32)
//   +0x14   same float constant
// Only kind==1 or kind==2 take the field-fill path; other kinds write nothing
// beyond +0x10 (matches the PPC recomp's `bnelr`).
void jumptable_3A48(void* slot, unsigned int kind,
                    unsigned int channel, unsigned int payload) {
    if (!slot) {
        return;
    }

    uint8_t* base = reinterpret_cast<uint8_t*>(slot);
    *reinterpret_cast<uint32_t*>(base + 16) = kind;

    if (kind != 1u && kind != 2u) {
        return;
    }

    // Shared body: both branches write the same u16 channel and u32 payload.
    *reinterpret_cast<uint32_t*>(base + 12) = payload;
    *reinterpret_cast<uint16_t*>(base + 8)  = static_cast<uint16_t>(channel);

    // The two branches differ only in the float constant: kind 2 → +15784,
    // kind 1 → +15788. The SDA constant pool stores these at fixed offsets
    // in .rdata; clang can fold them at link time. We emit 0.0f for both
    // variants since the runtime doesn't re-read this field on this path.
    const float kZero = 0.0f;
    std::memcpy(base + 20, &kZero, sizeof(kZero));
    std::memcpy(base + 4,  &kZero, sizeof(kZero));
}

// ─── No-op shims (link-only — no binary counterpart) ──────────────────────────
//
// These symbols appear in the link graph because stale callers reference
// them, but the original binary either inlined them away or never emitted
// them in this SKU. Keeping them as trivial no-ops preserves the link
// without pinning behavior. When the real implementations land (via later
// lifts) they will supersede these.

void hsmContext_Init(void* obj)        { (void)obj; }
void hsmContext_InitTimers(void)       {}
// 0x823DDA08 is snEvent's constructor, lifted in sn_event.cpp.
void* snEvent_Construct(void* event);
void hsmEvent_Init(void* e)            { snEvent_Construct(e); }
void HSM_QueueNotification(void* n)    { (void)n; }
void PostStateTransitionRequest(void* m, int e) { (void)m; (void)e; }
void SetTrainingState(int s)           { (void)s; }


// gmLogic vtable slot 3: reset the state machine and every child state.
// The game loop reaches it through the one-branch thunk 0x82229760, so r3 is
// the game loop's own object (render_loop.c passes g_pGmLogic instead).
struct gmLogicView {
    void** vtable;
    int32_t childCount;     // +0x04
    void** children;        // +0x08
    int32_t currentIndex;   // +0x0C
    int32_t state;          // +0x10
};

// @ 0x82222A78
extern "C" void gmLogic_StepFrame(void* obj) {
    using Fn = void (*)(void*);
    using IntFn = void (*)(void*, int32_t);
    auto* self = static_cast<gmLogicView*>(obj);
    self->state = -1;
    reinterpret_cast<Fn>(self->vtable[10])(self);
    for (int32_t i = 0; i < self->childCount; ++i) {
        void* child = self->children[i];
        reinterpret_cast<Fn>((*static_cast<void***>(child))[3])(child);
    }
    self->currentIndex = 0;
    if (self->children != nullptr && self->children[0] != nullptr) {
        void* root = self->children[0];
        reinterpret_cast<IntFn>((*static_cast<void***>(root))[5])(root, -1);
    }
}

// asm-alias wrapper for the C-side PostStateTransitionRequest symbol.
extern "C" void _c_PostStateTransitionRequest(void* m, int e)
    __asm__("_PostStateTransitionRequest");
extern "C" void _c_PostStateTransitionRequest(void* m, int e) {
    PostStateTransitionRequest(m, e);
}


// ============================================================================
// SECTION: hsmState member functions (lifted from stubs.cpp)
// ============================================================================

/**
 * hsmState::GetFullStatePath @ 0x823ED290 | size: 0xF8
 *
 * Builds the full hierarchical state path by recursing up the parent chain.
 * For a state hierarchy like Root/Menu/Options, this produces "Root/Menu/Options".
 *
 * Algorithm:
 *   1. If this state has a parent (m_pParentState != null):
 *      a. Recursively call parent->GetFullStatePath(buffer, bufferSize)
 *      b. Compute current string length
 *      c. Append "/<stateName>" using snprintf
 *   2. If no parent (root state):
 *      a. Copy GetStateName() directly into buffer
 *
 * Uses virtual dispatch for GetStateName() (vtable slot 2) and
 * GetFullStatePath() (vtable slot 3) to support polymorphic state names.
 */
char* hsmState::GetFullStatePath(char* buffer, uint32_t bufferSize) const {
    if (!buffer || bufferSize == 0)
        return buffer;

    if (m_pParentState) {
        // Recurse into parent first to build the prefix path
        m_pParentState->GetFullStatePath(buffer, bufferSize);

        // Compute current string length
        unsigned int currentLen = 0;
        const char* p = buffer;
        while (*p++)
            ;
        currentLen = static_cast<unsigned int>(p - buffer - 1);

        if (currentLen >= bufferSize)
            return buffer;

        // Append "/<stateName>" to the existing path
        const char* name = GetStateName();
        std::snprintf(buffer + currentLen, bufferSize - currentLen,
                      "/%s", name);
    } else {
        // Root state — just copy the name directly
        const char* name = GetStateName();
        unsigned int remaining = bufferSize - 1;
        char* dest = buffer;
        while (remaining > 0 && *name) {
            *dest++ = *name++;
            --remaining;
        }
        *dest = '\0';
    }
    return buffer;
}

/**
 * hsmState::Reset @ 0x823E8D58 | size: 0x50
 *
 * Resets this state to its initial condition. First calls the virtual
 * OnExit() method (vtable slot 6) to perform any cleanup, then zeros
 * out all state fields:
 *   +0x10: m_field_10 (context)
 *   +0x14: m_field_14
 *   +0x04: m_pManager
 *   +0x08: m_pParentState
 *   +0x0C: m_pChildState
 *
 * This effectively detaches the state from its hierarchy and manager.
 */
void hsmState::Reset() {
    // Call OnExit to perform cleanup before resetting
    OnExit();

    // Zero all state fields
    m_field_10 = nullptr;
    m_field_14 = nullptr;
    m_pManager = nullptr;
    m_pParentState = nullptr;
    m_pChildState = nullptr;
}

/**
 * rage::hsmState_AttachChild @ 0x823EF850 | size: 0x60
 *
 * Hooks an embedded child state into its parent's machine. The child takes
 * the parent's +0x10 (into both its +0x04 and +0x10) and +0x14, then runs
 * its own slot 5, where a state attaches its sub-states through this same
 * function. Only after that does the child's parent link (+0x08) point at
 * `parent`. Nothing is null-checked, and the parent's active-child pointer
 * (+0x0C) is left alone.
 */
namespace rage {
void hsmState_AttachChild(hsmStateBase* parent, hsmStateBase* child) {
    ::hsmState* p = static_cast<::hsmState*>(parent);
    ::hsmState* c = static_cast<::hsmState*>(child);

    c->m_pManager = p->m_field_10;
    c->m_field_10 = p->m_field_10;
    c->m_field_14 = p->m_field_14;
    c->OnEnter();  // slot 5
    c->m_pParentState = p;
}
}  // namespace rage
