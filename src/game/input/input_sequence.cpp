#include "rage/sys_callback.hpp"
// Timed input-sequence recognition, alongside the gdInputSeq data definitions.
#include <cstdint>

extern "C" int pongPlayer_0270_g(const void* input, int button);  // @ 0x821E0270
extern bool CheckButtonPressed(void* record);                    // @ 0x821DFFF8

namespace {

struct InputSequenceStep {
    float earliest;                 // +0x00
    float latest;                   // +0x04
    int32_t button;                 // +0x08
};

// View of gdInputSeq (vtable @ 0x82049890), not its per-input runtime state.
struct InputSequenceData {
    void** vtable;                  // +0x00
    const char* name;               // +0x04
    uint8_t enabled;                // +0x08
    uint8_t valid;                  // +0x09
    uint8_t padding[2];
    int32_t firstButton;            // +0x0C  inclusive, signed
    int32_t lastButton;             // +0x10  inclusive, signed
    uint32_t stepCount;             // +0x14
    const InputSequenceStep* steps; // +0x18
};

struct InputSequenceState {
    uint32_t flags;                 // +0x00: active=1, cached enable=2, valid=4, complete=8
    const InputSequenceData* data;  // +0x04
    float elapsed;                 // +0x08
    uint32_t step;                 // +0x0C
};

struct InputSequenceInput {
    uint8_t padding[0x31C];
    uint8_t* buttons;               // +0x31C: four bytes per physical button
};

}  // namespace

// game_D418 @ 0x8220D418 | size: 0x228
// r4 is unused; the caller supplies deltaTime separately in f1, input in r5,
// and callback in r6. Preserve that register gap in the lifted signature.
extern "C" void gdInputSeq_Update(void* statePtr, uint32_t /*unused*/, void* inputPtr,
                                  void* callback, float deltaTime) {
    auto* state = static_cast<InputSequenceState*>(statePtr);
    state->flags &= ~8u;
    if (!(state->flags & 1) || !state->data || !(state->flags & 4)) return;

    const InputSequenceData* data = state->data;
    const uint32_t enabled = data->enabled;
    if (enabled != ((state->flags & 2) != 0)) {
        state->elapsed = 0.0f;
        state->step = 0;
        // The original copies bit 1 of -enabled, even for noncanonical bytes.
        state->flags = (state->flags & ~2u) | ((0u - enabled) & 2u);
        if (enabled == 0) return;
    }

    const uint32_t stepIndex = state->step;
    const float elapsed = state->elapsed + deltaTime;
    state->elapsed = elapsed;
    const InputSequenceStep* step = data->steps + stepIndex;
    if (!(elapsed > step->latest)) {
        auto* input = static_cast<InputSequenceInput*>(inputPtr);
        bool expectedPressed = false;
        bool otherPressed = false;
        const int32_t lastButton = data->lastButton;
        for (int32_t button = data->firstButton; button <= lastButton;
             button = static_cast<int32_t>(static_cast<uint32_t>(button) + 1)) {
            if (button == step->button || !otherPressed) {
                const int physical = pongPlayer_0270_g(input, button);
                const bool pressed = CheckButtonPressed(input->buttons + physical * 4);
                if (button == step->button) expectedPressed = pressed;
                else otherPressed = pressed;
            }
        }
        // blt + bso: unordered times take the early-input path too. In contrast,
        // an unordered latest bound above does not time out the sequence.
        if (elapsed >= step->earliest) {
            if (!otherPressed) {
                if (!expectedPressed) return;
                state->elapsed = 0.0f;
                state->step = stepIndex + 1;
                if (state->step != data->stepCount) return;
                state->flags |= 8;
                sysCallback_Invoke(callback, const_cast<InputSequenceData*>(state->data));
            }
        } else if (!expectedPressed && !otherPressed) {
            return;
        }
    }
    // Completion callbacks see the completed index and bit before this reset.
    state->elapsed = 0.0f;
    state->step = 0;
}
