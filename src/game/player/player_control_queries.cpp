// Player ownership/control queries recovered from the original PPC.
#include <cstdint>
#include "crt/rtti.h"

struct pongPlayer;
extern "C" int32_t lbl_825C9A2C; // @ 0x825C9A2C
extern "C" void* g_render_obj_ptr; // @ 0x825EAB2C
extern "C" void* g_pGameLogic; // @ 0x8260639C
extern RTTITypeDescriptor g_typeDescriptor_gmLogic; // @ 0x825D3758
extern RTTITypeDescriptor g_typeDescriptor_gmLogicSpectator; // @ 0x825D6FAC

namespace {
template<class T> const T& at(const void* object, unsigned offset) {
    return *reinterpret_cast<const T*>(static_cast<const uint8_t*>(object) + offset);
}
}

// Whether this player's input slot is controlled in the current game mode.
// The spectator cast's result is unused, but its call precedes reloading the
// network controller and player slot in the original.
// @ 0x8218C690 | size: 0x118
uint8_t game_C690(pongPlayer* player) {
    const int32_t mode = lbl_825C9A2C;
    if (mode == 0)
        return at<int32_t>(g_render_obj_ptr, 0x128) == at<int32_t>(player, 0x1D0);
    if (mode == 1) {
        const int32_t slot = at<int32_t>(player, 0x1D0);
        void* logic = g_pGameLogic;
        if (slot != 0) return 0;
        const int32_t logicMode = at<int32_t>(logic, 0x54);
        return logicMode == 1 || logicMode == 2;
    }
    if (mode == 2) {
        RTDynamicCast(g_pGameLogic, 0, &g_typeDescriptor_gmLogic,
                      &g_typeDescriptor_gmLogicSpectator, 0);
        return at<int32_t>(g_render_obj_ptr, 0x128) == at<int32_t>(player, 0x1D0);
    }
    return 0;
}
