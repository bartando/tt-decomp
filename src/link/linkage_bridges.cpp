/**
 * linkage_bridges.cpp — one function, two spellings
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Files disagree on how they declare some functions: extern "C" in one, C++
 * linkage in another, a namespace, or a parameter type that is the same
 * register on the Xbox 360 (a pointer and a u32, a u16 and a u32). Each
 * spelling is a different symbol to the linker, so the one nobody defines
 * stays undefined. Each bridge below defines that spelling and forwards to
 * the definition, with a comment naming the files that disagree. Making the
 * declarations agree would retire the bridge.
 *
 * Calls between a C-linkage and a C++-linkage function of the same name and
 * parameters can't be declared in one scope, so the C-linkage side is
 * declared inside a namespace (it keeps its unmangled symbol there).
 */

#include <cstdint>

// ── Targets: the definitions the bridges forward to ─────────────────────────

struct grcDeviceBeginScene;
struct grcDeviceClear;

namespace rage {
void rage_1058(void* obj);                                           // rage_core_utils.cpp
void snSession_AddNode(void* listHead, void* node);                  // pong_network_io.cpp
void snSession_AssociateConnections(void* session, void* dispatcher, void* connList);
void snSession_ProcessPendingConnections(void* session, void* dispatcher, void* connList);
void* rage_alloc_aligned(unsigned long size, unsigned long alignment);  // rage_memory.cpp

struct snLinkedList;
struct hsmEventNode;
struct hsmContext;
struct hsmStateBase;
}  // namespace rage

void audSystem_Configure(void* self, void* config);                  // rage_audio.cpp
void audSystem_Shutdown(void* self);
void grcDevice_beginScene(grcDeviceBeginScene* device);              // grc_render.cpp
void grcDevice_clear(grcDeviceClear* device);
void grcDevice_shutdown();                                           // grc_device.cpp
void grcDevice_shutdownAlt();
void phInst_6158_p39(void* self);                                    // ph_physics.cpp
const char* rage_strchr(const char* str, int ch);
void atSingleton_9728_2h(void* target, void* source);                // rage_memory.cpp
void atSingleton_DCE8_gen(void* data);
void atSingleton_EB38_p(void* wrapper, void* arg1, void* arg2);
void* rage_Alloc(unsigned int size);                                 // rage_core_utils.cpp
void RegisterSerializedField(void* obj, const void* fieldKey, void* fieldPtr, const void* schemaDesc,
                             uint32_t flags);                        // gd_data.cpp
void msgMsgSink_03B8_g(void* self, uint32_t index);                  // msg_msg_sink.cpp
void* msgMsgSink_8D10_g(void* self, uint32_t slotIndex);
void jumptable_3A48(void* slot, unsigned int kind, unsigned int channel, unsigned int payload);  // hsm.cpp

namespace c_linkage {
extern "C" {
void RtlEnterCriticalSection(void* cs);                              // kernel.c
void RtlLeaveCriticalSection(void* cs);
int _stricmp(const char* a, const char* b);                          // crt_init.c
float math_SafeReciprocal(float value, double fallback);             // rage_core_utils.cpp
bool pongPlayer_DE98_g(void* state);                                 // pong_player.cpp
void rage_27C0(void* obj);                                           // rage_core_utils.cpp
void sysCallback_Invoke(void* callback, int code);
void sysMemAllocator_Free(void* ptr);
void sysMemAllocator_PlatformFree(void* ptr, unsigned int flags);
void sysMemAllocator_InitMainThread(void);                           // entry.c
int rage_main_stub(void* startupParams, void* base);                 // main.c
void* rage_AllocInternal(uint32_t size, uint32_t flags);             // heap.c
}
}  // namespace c_linkage

// ── C spelling missing, C++ definition exists ───────────────────────────────
// The C-linkage bridges live in a namespace so they can sit next to the C++
// declarations above; extern "C" keeps their symbols unmangled.

namespace c_bridges {
extern "C" {

// render_loop.c declares these C; rage_audio.cpp defines them with C++ linkage.
void audSystem_Configure(void* loop, void* config) { ::audSystem_Configure(loop, config); }
void audSystem_Shutdown(void* loop) { ::audSystem_Shutdown(loop); }

// scene_render.c (C) vs grc_render.cpp (C++).
void grcDevice_beginScene(void* device) { ::grcDevice_beginScene(static_cast<grcDeviceBeginScene*>(device)); }
void grcDevice_clear(void* device) { ::grcDevice_clear(static_cast<grcDeviceClear*>(device)); }

// render_loop.c (C) vs grc_device.cpp (C++).
void grcDevice_shutdown(void) { ::grcDevice_shutdown(); }
void grcDevice_shutdownAlt(void) { ::grcDevice_shutdownAlt(); }

// ph_update_object.cpp declares it extern "C"; ph_physics.cpp defines it C++.
void phInst_6158_p39(void* self) { ::phInst_6158_p39(self); }

// game_loop.c (C, returns void*) vs ph_physics.cpp (C++, returns const char*).
void* rage_strchr(const char* str, int ch) { return const_cast<char*>(::rage_strchr(str, ch)); }

// cm_operators.cpp takes the address of these as extern "C"; rage_memory.cpp
// defines them C++.
void atSingleton_9728_2h(void* target, void* source) { ::atSingleton_9728_2h(target, source); }
// 0x8225EB38: calls *(fn*)r3 with (r4, r5). cm_operators.cpp declares one argument.
void atSingleton_EB38_p(void* wrapper, void* arg1, void* arg2) { ::atSingleton_EB38_p(wrapper, arg1, arg2); }

// pong_network.cpp passes a second argument (3); 0x8212DCE8 never reads r4.
void atSingleton_DCE8_gen(void* data, int) { ::atSingleton_DCE8_gen(data); }

// char_view.cpp, pong_network.cpp and rage_par.cpp declare it C (u32 size);
// rage_core_utils.cpp defines it C++.
void* rage_Alloc(uint32_t size) { return ::rage_Alloc(static_cast<unsigned int>(size)); }

}  // extern "C"
}  // namespace c_bridges

// ── C++ spelling missing, C definition exists ───────────────────────────────

// msg_msg_sink.cpp declares these C++; kernel.c defines them C.
void RtlEnterCriticalSection(void* cs) { c_linkage::RtlEnterCriticalSection(cs); }
void RtlLeaveCriticalSection(void* cs) { c_linkage::RtlLeaveCriticalSection(cs); }

// ph_update_object.cpp (C++) vs crt_init.c (C).
int _stricmp(const char* a, const char* b) { return c_linkage::_stricmp(a, b); }

// ph_physics.cpp (C++) vs rage_core_utils.cpp (extern "C").
float math_SafeReciprocal(float value, double fallback) { return c_linkage::math_SafeReciprocal(value, fallback); }

// pcr_anim_blenders.cpp (C++) vs pong_player.cpp (extern "C").
bool pongPlayer_DE98_g(void* state) { return c_linkage::pongPlayer_DE98_g(state); }

// pong_network.cpp (C++) vs rage_core_utils.cpp (extern "C").
void rage_27C0(void* obj) { c_linkage::rage_27C0(obj); }

// pong_network_classes.cpp (C++) vs rage_core_utils.cpp (extern "C").
void sysCallback_Invoke(void* callback, int code) { c_linkage::sysCallback_Invoke(callback, code); }

// gd_data.cpp, grc_device.cpp, pong_camera.cpp, pong_network_classes.cpp,
// rage_memory.cpp, rage_xml.cpp (C++) vs rage_core_utils.cpp (extern "C").
void sysMemAllocator_Free(void* ptr) { c_linkage::sysMemAllocator_Free(ptr); }

// gd_data.cpp (u32 flags) and pong_network_classes.cpp (int flags), both C++,
// vs rage_core_utils.cpp (extern "C").
void sysMemAllocator_PlatformFree(void* ptr, uint32_t flags) { c_linkage::sysMemAllocator_PlatformFree(ptr, flags); }
void sysMemAllocator_PlatformFree(void* ptr, int flags) {
    c_linkage::sysMemAllocator_PlatformFree(ptr, static_cast<unsigned int>(flags));
}

// gd_data.cpp (C++) vs entry.c (C).
void sysMemAllocator_InitMainThread() { c_linkage::sysMemAllocator_InitMainThread(); }

// rage_core_utils.cpp (C++) vs main.c (C).
int rage_main_stub(void* startupParams, void* base) { return c_linkage::rage_main_stub(startupParams, base); }

// msg_msg_sink.cpp (C++) vs heap.c (C).
void* rage_AllocInternal(uint32_t size, uint32_t allocatorId) { return c_linkage::rage_AllocInternal(size, allocatorId); }

// ── C++ spellings that differ in namespace or parameter types ───────────────

// ph_physics.cpp declares it in the global namespace; rage_core_utils.cpp
// defines it in rage.
void rage_1058(void* obj) { rage::rage_1058(obj); }

namespace rage {
// snSessionStates.cpp declares these with typed pointers; pong_network_io.cpp
// defines them with void*.
void snSession_AddNode(snLinkedList* list, hsmEventNode* node) { snSession_AddNode(static_cast<void*>(list), node); }
void snSession_AssociateConnections(hsmContext* context, hsmStateBase* state, void* connList) {
    snSession_AssociateConnections(static_cast<void*>(context), static_cast<void*>(state), connList);
}
void snSession_ProcessPendingConnections(hsmContext* context, hsmStateBase* state, void* connList) {
    snSession_ProcessPendingConnections(static_cast<void*>(context), static_cast<void*>(state), connList);
}

// rage_cm.cpp passes unsigned int; rage_memory.cpp takes unsigned long.
void* rage_alloc_aligned(unsigned int size, unsigned int alignment) {
    return rage_alloc_aligned(static_cast<unsigned long>(size), static_cast<unsigned long>(alignment));
}
}  // namespace rage

// pong_drill.cpp passes the field name and type descriptor as char* / void*;
// gd_data.cpp takes const void* / const void* / u32 flags.
void RegisterSerializedField(void* obj, const char* name, void* field, void* typeDesc, int flags) {
    RegisterSerializedField(obj, static_cast<const void*>(name), field, static_cast<const void*>(typeDesc),
                            static_cast<uint32_t>(flags));
}

// msg_msg_sink.cpp declares the index as u16 in some places, u32 in others
// (it is a 14-bit index in a 32-bit register).
void msgMsgSink_03B8_g(void* self, uint16_t index) { msgMsgSink_03B8_g(self, static_cast<uint32_t>(index)); }
void* msgMsgSink_8D10_g(void* self, uint16_t slotIndex) { return msgMsgSink_8D10_g(self, static_cast<uint32_t>(slotIndex)); }

// msg_msg_sink.cpp passes the channel as u16; hsm.cpp takes unsigned int.
void jumptable_3A48(void* slot, unsigned int kind, uint16_t channel, unsigned int payload) {
    jumptable_3A48(slot, kind, static_cast<unsigned int>(channel), payload);
}
