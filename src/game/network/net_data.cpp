/**
 * net_data.cpp — Network game code data the image defines
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


// @ 0x8202D110 (.rdata)
extern "C" const float g_fZeroConst = 0.0f;

// @ 0x8203A91C (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const FloatAverager_vtable_2[3] = {};

// @ 0x8206C304 (.rdata) — 10 slots of PPC code addresses in the image, null in the port
extern "C" void* const PongNetMessage_vtable[10] = {};

// @ 0x8206EE0C (.rdata)
extern "C" const char g_szScoreMessageFmt[19] = "RequestDataMessage";

// @ 0x82070D14 (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const SpectatorNetworkClient_vtable[25] = {};

// @ 0x82070D78 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const FloatAverager_vtable_3[3] = {};

// @ 0x8207116C (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetDataQuery_vtable[18] = {};

// @ 0x820711B4 (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetDataQuery_stateInit_vtable[18] = {};

// @ 0x820711FC (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetDataQuery_stateRequestData_vtable[18] = {};

// @ 0x82071244 (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetDataQuery_stateReceiveData_vtable[18] = {};

// @ 0x8207128C (.rdata) — 16 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetDataQuery_stateFinish_vtable[16] = {};

// @ 0x820713BC (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_vtable[18] = {};

// @ 0x82071404 (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateInit_vtable[18] = {};

// @ 0x8207144C (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateWaitForSyncState_vtable[18] = {};

// @ 0x82071494 (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateEnterState_vtable[18] = {};

// @ 0x820714DC (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateRequestSyncronization_vtable[18] = {};

// @ 0x82071524 (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateSendSyncronization_vtable[18] = {};

// @ 0x8207156C (.rdata) — 18 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateReceiveSyncronization_vtable[18] = {};

// @ 0x820715B4 (.rdata) — 16 slots of PPC code addresses in the image, null in the port
extern "C" void* const NetStateSync_stateWaitTime_vtable[16] = {};

// @ 0x82071654 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const AckHandling_vtable[3] = {};

// @ 0x82071660 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const FrameTimeEstimate_vtable[3] = {};

// @ 0x8207166C (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const FloatAverager_vtable[3] = {};

// @ 0x82071678 (.rdata) — 4 slots of PPC code addresses in the image, null in the port
extern "C" void* const pongPaddle_vtable[4] = {};

// @ 0x820716A8 (.rdata) — a string in the image, whatever the declaration says
extern "C" const char plrPropMgr_propType1_vtable[15] = "BallBufferSize";

// @ 0x820716B8 (.rdata) — a string in the image, whatever the declaration says
extern "C" const char plrPropMgr_propType2_vtable[17] = "PaddleBufferSize";

// @ 0x820717C4 (.rdata) — 32 slots of PPC code addresses in the image, null in the port
extern "C" void* const plrPropMgr_vtable[32] = {};

// @ 0x825CAEC4 (.data) — image: 0x42700000
extern "C" void* g_pMatchTimeSyncScale = nullptr;

// @ 0x825D1044 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_ShaderParams[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D1134 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_Vector4[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D126C (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_StructBool[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D13A4 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_13A4[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D1614 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_RangeMgr[24] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D164C (.data)
extern "C" void* g_holderInstance_MotionRangeMgr_ptr = nullptr;

// @ 0x825D1960 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_InputDataMgr[24] = {0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x826066C0 (.data)
extern "C" void* g_plrPropMgrSingleton = nullptr;

// @ 0x8261A0D0 (.data)
extern "C" alignas(16) uint8_t g_netMessageHolderBuffer[256] = {};

// @ 0x8271A2CC (.data) — a 24-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_networkSentinel[48] = {};
