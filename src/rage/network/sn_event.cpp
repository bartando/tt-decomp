/**
 * sn_event.cpp — constructing a session event
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include <cstdint>

void datResource_PointerFixup(uint32_t* field);            // @ 0x82121B00

namespace rage {
extern void* const g_vtbl_hsmEvent[];                      // @ 0x82072864
struct hsmEventData;
}  // namespace rage

extern "C" void* const g_vtbl_snEvent[];                   // @ 0x82072878

// @ 0x823DDA08 — rage::snEvent's constructor (util_DA08)
// The hsmEvent base runs the resource fixup on its two link fields and then
// clears them; snEvent adds nothing but its vtable. Returns the event.
void* snEvent_Construct(void* event) {
    uint32_t* words = static_cast<uint32_t*>(event);
    *static_cast<void* const**>(event) = rage::g_vtbl_hsmEvent;
    datResource_PointerFixup(&words[1]);
    datResource_PointerFixup(&words[2]);
    words[2] = 0;
    words[1] = 0;
    *static_cast<void* const**>(event) = g_vtbl_snEvent;
    return event;
}

// snSessionStates.cpp's name for it.
namespace rage {
void hsmEvent_Init(hsmEventData* event) {
    snEvent_Construct(event);
}
}  // namespace rage
