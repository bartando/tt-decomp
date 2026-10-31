#include "platform/time_stamp.h"
#include <cstddef>

static_assert(offsetof(KeTimeStampBundle, milliseconds) == 0x10, "kernel tick offset");

// The Xbox import refers to kernel-updated shared memory. The host refreshes a
// per-thread snapshot at the import boundary, avoiding a polling thread or races.
extern "C" const KeTimeStampBundle* hostGetKeTimeStampBundle() {
    thread_local KeTimeStampBundle snapshot{};
    snapshot.milliseconds = tt_uptime_milliseconds();
    return &snapshot;
}
