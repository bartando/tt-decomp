#pragma once
#include <cstddef>
#include <cstdint>
struct TimeManagerState;
struct TimeManagerVTable {
    void (*reset)(TimeManagerState*);
    void (*tick)(TimeManagerState*);
};
struct TimeManagerState {
    const TimeManagerVTable* vtable;
    uint32_t field04;
    float frameSeconds, framesPerSecond;
    float previousElapsed, elapsed, nominalRate, fixedStep, maximumStep, minimumStep;
    uint32_t frameCount, clamped;
    uint8_t firstTick, field31, fixedRate, field33;
    int32_t forceFixed;
    uint64_t lastTimebase;
    uint8_t pauseAdvance, pad41[11];
    float deltaRaw, timeScale, timeUnscaled, timeUnscaledCopy;
    uint32_t field5C;
};
static_assert(sizeof(void*) != 4 || sizeof(TimeManagerState) == 0x60, "time-state image extent");
static_assert(sizeof(void*) != 4 || offsetof(TimeManagerState, lastTimebase) == 0x38, "time-state clock offset");
extern "C" {
void sysTimeManager_Reset(TimeManagerState*); // @ 0x82187BA0
void sysTimeManager_Tick(TimeManagerState*); // @ 0x82187BE8
extern TimeManagerState g_sysTimeManager; // @ 0x825CAEB8
extern TimeManagerState lbl_825CAEB8; // Same object, not a copied tuning table.
}
