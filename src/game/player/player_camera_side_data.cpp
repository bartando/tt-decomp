// Camera node registry singleton; the host startup code supplies its instance.
#include <cstdint>

extern "C" {
void* g_pCourtState = nullptr; // @ 0x8271A314
// The original type token is the address of its own storage.
uintptr_t g_cameraNodeType = reinterpret_cast<uintptr_t>(&g_cameraNodeType); // @ 0x825C7520
}
