// Crowd animation playback. Names below are descriptive, inferred from the
// crowd-manager tick at 0x8238AE10 and the resource constructor at 0x82386918.
#include "fx_effects.hpp"
#include "../rage/animation/rage_anim.hpp"

extern uint32_t g_prngState[2]; // @ 0x825CA2C8 (seed, carry)
extern float lbl_825CAEB8[];    // @ 0x825CAEB8 (sysTimeManager; +8 is delta time)

// The original ignores r4; retain that slot so the frame is passed in r5.
extern void LocomotionStateAnim_88E0_g(void* clip, void* unusedR4,
                                      rage::crAnimFrame* frame,
                                      uint32_t integralFrames, uint32_t flags,
                                      float time); // @ 0x822488E0
extern void LocomotionStateAnim_6E50_w(fxCrowdAnimPlayback* playback, float* phase,
                                      void* animation, uint32_t advanceState); // @ 0x82386E50
extern void LocomotionStateAnim_BB98(void*, void*, float, uint32_t, uint32_t); // @ 0x8224BB98

struct fxCrowdAnimPlaybackClip {
    uint8_t unknown00[20];
    uint32_t type;                // +0x14: types 1 and 11 start in phase 1
    uint8_t unknown18[8];
    float delayScale;             // +0x20
    float fadeIn;                 // +0x24
    float fadeOut;                // +0x28
    float minSpeed;               // +0x2C
    float maxSpeed;               // +0x30
    void* clips[3];               // +0x34: intro, loop, outro
};

// No vtable: this is the resource-backed block at crowd archetype +0x20.
struct fxCrowdAnimPlayback {
    fxCrowdAnimPlaybackClip* current; // +0x00
    fxCrowdAnimPlaybackClip* next;    // +0x04
    uint8_t finishCurrent;           // +0x08
    uint8_t unknown09[3];
    float currentPhase;              // +0x0C (normalized)
    float nextPhase;                 // +0x10
    float speed;                     // +0x14
    float blendWeight;               // +0x18
    float delay;                     // +0x1C
    uint32_t state;                  // +0x20: intro, loop, outro
    fxCrowdAnimPlaybackClip* queue[2]; // +0x24
    uint32_t writeIndex;             // +0x2C
    uint32_t readIndex;              // +0x30 (last consumed slot)
    uint32_t queued;                 // +0x34
    rage::crAnimFrame* currentFrame;  // +0x38
    rage::crAnimFrame* nextFrame;     // +0x3C
};

// @ 0x82386A20 | size: 0x42C (former auto-name LocomotionStateAnim_6A20_g)
void fxCrowdAnimPlayback_Update(fxCrowdAnimPlayback* self) {
    // MSVC rounds the range*random product before its fused scale+minimum.
    auto randomSpeed = [](const fxCrowdAnimPlaybackClip* clip) {
        const uint64_t next = uint64_t(g_prngState[0]) * 0x5CDCFAA7u + g_prngState[1];
        g_prngState[0] = uint32_t(next);
        g_prngState[1] = uint32_t(next >> 32);
        const float product = (clip->maxSpeed - clip->minSpeed)
            * float(uint32_t(next) & 0x7FFFFF);
        return __builtin_fmaf(product, 0x1p-23f, clip->minSpeed);
    };
    auto pop = [self]() {
        if (++self->readIndex == 2)
            self->readIndex = 0;
        --self->queued;
        return self->queue[self->readIndex];
    };

    if (!self->current && self->queued != 0) {
        self->current = pop();
        self->currentPhase = 0.0f;
        self->finishCurrent = 0;
        self->speed = randomSpeed(self->current);
        self->state = (self->current->type == 1 || self->current->type == 11) ? 1 : 0;
    }

    if (!self->next && self->queued != 0 && self->state != 2) {
        uint32_t index = self->readIndex + 1;
        if (index == 2)
            index = 0;
        if (self->queue[index]->type == 1 && self->current->type != 1) {
            self->finishCurrent = 1;
        } else {
            self->finishCurrent = 0;
            self->next = pop();
            self->nextPhase = 0.0f;
            self->delay = randomSpeed(self->next) * self->next->delayScale;
        }
    }

    const bool blendNext = self->next && self->delay <= 0.0f;
    if (self->delay > 0.0f)
        self->delay -= lbl_825CAEB8[2];

    void* clip = self->current->clips[self->state];
    const float duration = *reinterpret_cast<const float*>(static_cast<const uint8_t*>(clip) + 12);
    LocomotionStateAnim_88E0_g(clip, nullptr, self->currentFrame, 0, 1, duration * self->currentPhase);

    bool advanceCurrent = true;
    if (blendNext) {
        self->delay = 0.0f;
        clip = self->next->clips[self->state];
        const float nextDuration = *reinterpret_cast<const float*>(static_cast<const uint8_t*>(clip) + 12);
        LocomotionStateAnim_88E0_g(clip, nullptr, self->nextFrame, 0, 1, nextDuration * self->nextPhase);
        LocomotionStateAnim_6E50_w(self, &self->nextPhase, self->next, 0);

        float phase = self->nextPhase == 0.0f ? 1.0f : self->nextPhase;
        float fade = self->next->fadeIn;
        if (phase >= 1.0f - self->next->fadeOut) {
            fade = self->next->fadeOut;
            phase = 1.0f - phase;
        }
        float weight;
        if (phase >= fade)
            weight = 1.0f;
        else if (phase <= 0.0f)
            weight = 0.0f;
        else
            weight = phase / fade;
        self->blendWeight = weight;
        // fsel selects zero for a negative or unordered weight, then caps at one.
        const float nonnegative = weight >= 0.0f ? weight : 0.0f;
        const float clamped = nonnegative >= 1.0f ? 1.0f : nonnegative;
        rage::crAnimFrame_ApplyMatchingDofs(self->currentFrame, self->nextFrame,
            nullptr, nullptr, nullptr, clamped, nullptr, LocomotionStateAnim_BB98);

        if (self->blendWeight >= 1.0f) {
            self->current = self->next;
            self->currentPhase = self->nextPhase;
            self->next = nullptr;
            advanceCurrent = false;
        }
    }

    if (advanceCurrent) {
        LocomotionStateAnim_6E50_w(self, &self->currentPhase, self->current, 1);
        if (self->finishCurrent && self->currentPhase == 0.0f) {
            if (self->state == 1)
                self->state = 2;
            else if (self->state == 2) {
                self->current = nullptr;
                self->finishCurrent = 0;
            }
        }
    }
}
