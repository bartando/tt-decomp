#include <cstdint>
#include "rage/ptr32.hpp"

struct replayDataView;
extern "C" void* g_pActiveMatchContext; // @ 0x8271A2FC

// Publish whether a requested replay has entries, unless the match context is
// already holding its replay state. Byte flags accept every nonzero value.
// @ 0x821CCE00 | size: 0xE4
void util_CE00(replayDataView* object) {
    const auto* replay = reinterpret_cast<const uint8_t*>(object);
    const bool requested = replay[0x68CFC] != 0 || replay[0x68CFD] != 0 || replay[0x68CFB] != 0;
    bool hasEntries = false;
    if (replay[0x68CFE] == 0) {
        const auto* list = rage::load_ptr32<uint8_t>(replay, 0x68D10);
        hasEntries = list != nullptr && *reinterpret_cast<const uint16_t*>(list + 4) > 0;
    }
    auto* context = static_cast<uint8_t*>(g_pActiveMatchContext);
    if (context[0x24] != 0) return;
    context[0x1D] = requested && hasEntries;
    *reinterpret_cast<rage::ptr32<void>*>(context + 0x20) = rage::load_ptr32<void>(replay, 0x68D00);
    context[0x1C] = 1;
    context[0x24] = 0;
}
