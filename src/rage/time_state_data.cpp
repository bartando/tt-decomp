#include "rage/time_state.hpp"
#include "link/tt_alias.h"
// @ 0x82038CA8 — exactly two code pointers. These are Reset/Tick, not destructors.
const TimeManagerVTable timeManagerVTable = {sysTimeManager_Reset, sysTimeManager_Tick};
// @ 0x825CAEB8 — full 0x60-byte image object, relocated to native pointer widths.
extern "C" TimeManagerState g_sysTimeManager = {
    &timeManagerVTable, 0,
    0x1.1111120000000p-6f, 0x1.e000000000000p+5f, 0x0.0p+0f, 0x0.0p+0f, 0x1.e000000000000p+5f, 0x1.1111120000000p-6f, 0x1.99999a0000000p-4f, 0x1.a36e2e0000000p-14f,
    0, 1, 1, 0, 0, 0, 0, 0, 0, {},
    0x1.1111120000000p-6f, 0x1.0000000000000p+0f, 0x1.1111120000000p-6f, 0x1.1111120000000p-6f, 0
};
TT_DATA_ALIAS("lbl_825CAEB8", "g_sysTimeManager");
