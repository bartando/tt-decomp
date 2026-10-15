/**
 * sn_data.cpp — RAGE session network data the image defines
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that code in this subsystem references but nothing
 * defined. Each sits at the address in its comment; constants take their
 * value from the game image, pointers start null (the image's values are
 * PPC addresses), and vtables are null-filled tables of the original's size.
 * Names that the code uses for the same address are aliases of one object.
 */

#include <cstdint>
#include "link/tt_alias.h"


namespace rage {

// @ 0x82072864 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_hsmEvent[5] = {};

// @ 0x82072968 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtDestroy[5] = {};

// @ 0x82072A28 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtCreateFailed[5] = {};

// @ 0x82072A8C (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtStartSessionFailed[5] = {};

// @ 0x82072AA0 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtCreateSucceeded[5] = {};

// @ 0x82073CAC (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_hsmState[18] = {};

// @ 0x82073F1C (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_hsmStateBase[18] = {};

}  // namespace rage

namespace rage {
namespace snSession_States {

// @ 0x82072864 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_hsmEvent[5] = {};

// @ 0x820728A0 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtChangePresenceSucceeded[5] = {};

// @ 0x820728C8 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtMigrateSucceeded[5] = {};

// @ 0x820728DC (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtMigrateFailed[5] = {};

// @ 0x82072A64 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtApplyConfigFailed[5] = {};

// @ 0x82072A8C (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtStartSessionFailed[5] = {};

// @ 0x82072CF4 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtJoinSucceeded[5] = {};

// @ 0x82072DD0 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtSessionJoinFailed[5] = {};

// @ 0x820730BC (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern void* const g_vtbl_EvtLeaveSucceeded[5] = {};

// @ 0x825D18AC (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
alignas(16) uint32_t g_evtType_PresenceChanged[6] = {0xFFFFFFFFu, 0x0u, 0x0u, 0x0u, 0x0u, 0x0u};

// @ 0x825D1924 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
alignas(16) uint32_t g_evtType_SessionStarted[6] = {0xFFFFFFFFu, 0x0u, 0x0u, 0x0u, 0x0u, 0x0u};

// @ 0x825D1978 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
alignas(16) uint32_t g_evtType_SessionClosed[6] = {0xFFFFFFFFu, 0x0u, 0x0u, 0x0u, 0x0u, 0x0u};

// @ 0x825D1984 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
alignas(16) uint32_t g_evtType_SessionDeregistered[6] = {0xFFFFFFFFu, 0x0u, 0x0u, 0x0u, 0x0u, 0x0u};

}  // namespace snSession_States
}  // namespace rage

// @ 0x82072878 (.rdata) — rage::snEvent's vtable (RTTI ".?AVsnEvent@rage@@"),
// 5 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_vtbl_snEvent[5] = {};
