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
struct snSessionData;
struct snListNode;
namespace snSession_States {
void snSession_InsertConnectionNode(snSessionData* session, snListNode* node);   // snSessionStates.cpp
void snSession_RemoveConnectionNode(snSessionData* session, snListNode* node);
}  // namespace snSession_States
void atSingleton_8068_h(void* obj);                                  // rage_core_utils.cpp
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
void phBoundGeometry_Constructor(void* self);                        // ph_physics.cpp
void phBoundSphere_Constructor(void* self);
void phBoundOctree_Constructor(void* self);
void phBoundOTGrid_Constructor(void* self);
void phBoundRibbon_Constructor(void* self);
void phBoundComposite_Constructor(void* self);
void ph_CleanupCompositePhInst(void* obj);
void pongNetMessageHolder_DestroyHitMessagePool(void* self);         // pong_network_classes.cpp
void pongNetMessageHolder_vfn_2_FD70(void* self);

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
void rage_free(void* ptr);                                           // heap.c
void util_PackColorRGBA(uint32_t* out, const float* rgba);           // rage_core_utils.cpp
void* xam_singleton_init_8D60(void* arg);                            // xam_shims.c
void grmShaderGroup_ArrayDtor64(void* arrayBase, int mode);          // rage_engine_dtors.cpp
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

// ph_physics.cpp declares the phBound constructors by their map names
// (0x82290F78, 0x822954C8, 0x822971A8, 0x8229B4E0, 0x8229D8D0, 0x8228DE80)
// extern "C" and defines them under readable names with C++ linkage. The
// sphere's radius argument isn't read (0x822954C8 never touches f1).
void ph_0F78(void* self) { ::phBoundGeometry_Constructor(self); }
void ph_54C8(void* self, float) { ::phBoundSphere_Constructor(self); }
void ph_71A8(void* self) { ::phBoundOctree_Constructor(self); }
void ph_B4E0(void* self) { ::phBoundOTGrid_Constructor(self); }
void ph_D8D0(void* self) { ::phBoundRibbon_Constructor(self); }
void ph_DE80(void* self) { ::phBoundComposite_Constructor(self); }

// 0x820EEA18: pong_network.cpp calls it rage_EA18; rage_engine_dtors.cpp
// defines it as grmShaderGroup_ArrayDtor64.
void rage_EA18(void* arrayBase, int mode) { c_linkage::grmShaderGroup_ArrayDtor64(arrayBase, mode); }

// ── Address-suffixed names for functions the port defines under another ─────

// 0x820DEC88, operator new. pong_match.cpp, pong_network.cpp and
// ph_physics.cpp call it xe_EC88; pong_network.cpp also calls it rage_Alloc
// ("Memory allocator @ 0x820DEC88"), which the port defines.
void* xe_EC88(uint32_t size) { return ::rage_Alloc(static_cast<unsigned int>(size)); }

// 0x820C00C0. fiAsciiTokenizer.cpp, rage_grm.cpp, pong_network.cpp and
// sysMemSimpleAllocator.cpp call it rage_free_00C0; heap.c defines it as
// rage_free and notes the two were merged. (rage_grm.cpp declares the
// argument uint32_t, which truncates a host pointer.)
void rage_free_00C0(void* ptr) { c_linkage::rage_free(ptr); }

// 0x820C0038 (gd_data.cpp: "sysMemAllocator_InitMainThread @ 0x820C0038").
// pong_camera.cpp, rage_grm.cpp and atSingleton.cpp call it by its map name.
void xe_main_thread_init_0038(void) { c_linkage::sysMemAllocator_InitMainThread(); }

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

// pong_render.cpp (C++) vs rage_core_utils.cpp (extern "C").
void util_PackColorRGBA(uint32_t* out, const float* rgba) { c_linkage::util_PackColorRGBA(out, rgba); }

// pong_network.cpp (C++, one spelling of two) vs xam_shims.c (C).
void* xam_singleton_init_8D60(void* arg) { return c_linkage::xam_singleton_init_8D60(arg); }

// pong_states.cpp calls 0x820C0038 rage_AssertMainThread (C++);
// rage_core_utils.cpp's C rage_AssertMainThread is an empty placeholder,
// entry.c's sysMemAllocator_InitMainThread is the function.
void rage_AssertMainThread() { c_linkage::sysMemAllocator_InitMainThread(); }

// msg_msg_sink.cpp calls 0x820C01B8 (the tagged allocation XMemFree's
// counterpart) rage_01B8 and rage_01B8_alloc; heap.c defines it as
// rage_AllocInternal.
void* rage_01B8(uint32_t size, uint32_t attributes) { return c_linkage::rage_AllocInternal(size, attributes); }
void* rage_01B8_alloc(uint32_t size, uint32_t attributes) { return c_linkage::rage_AllocInternal(size, attributes); }

// ── Map names for C++ functions defined under another name ──────────────────

// 0x8246FC68: ph_physics.cpp declares ph_FC68_h and defines
// ph_CleanupCompositePhInst.
void ph_FC68_h(void* obj) { ph_CleanupCompositePhInst(obj); }

// 0x823C0928 and 0x823BFD70: pong_network.cpp calls them by map name with a
// typed holder; pong_network_classes.cpp defines them with void*.
struct pongNetMessageHolder;
void pongNetMessageHolder_vfn_2_0928_1(pongNetMessageHolder* holder) { pongNetMessageHolder_DestroyHitMessagePool(holder); }
void pongNetMessageHolder_vfn_2_FD70_1(pongNetMessageHolder* holder) { pongNetMessageHolder_vfn_2_FD70(holder); }

// 0x823EDD10 and 0x823EDDB8: pong_network_io.cpp calls them by map name;
// snSessionStates.cpp defines them in rage::snSession_States.
void snSession_DD10_w(void* session, void* node) {
    rage::snSession_States::snSession_InsertConnectionNode(static_cast<rage::snSessionData*>(session),
                                                           static_cast<rage::snListNode*>(node));
}
void snSession_DDB8_w(void* session, void* node) {
    rage::snSession_States::snSession_RemoveConnectionNode(static_cast<rage::snSessionData*>(session),
                                                           static_cast<rage::snListNode*>(node));
}

// 0x82408068: swf.cpp calls it swfPlaceObject2ClipEvent_Cleanup in namespace
// rage; rage_core_utils.cpp defines it as rage::atSingleton_8068_h.
namespace rage {
void swfPlaceObject2ClipEvent_Cleanup(void* obj) { atSingleton_8068_h(obj); }
}  // namespace rage

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


// pong_drill.cpp's C++ spelling of 0x821A8F58 (lifted in par_xml_types.cpp).
extern "C" void RegisterSerializationField(void* obj, const char* name, void* fieldPtr, void* desc, int flags);
void RegisterSerializedField(void* obj, const char* name, void* field, void* typeDesc, int flags) {
    RegisterSerializationField(obj, name, field, typeDesc, flags);
}

// msg_msg_sink.cpp declares the index as u16 in some places, u32 in others
// (it is a 14-bit index in a 32-bit register).
void msgMsgSink_03B8_g(void* self, uint16_t index) { msgMsgSink_03B8_g(self, static_cast<uint32_t>(index)); }
void* msgMsgSink_8D10_g(void* self, uint16_t slotIndex) { return msgMsgSink_8D10_g(self, static_cast<uint32_t>(slotIndex)); }

// msg_msg_sink.cpp passes the channel as u16; hsm.cpp takes unsigned int.
void jumptable_3A48(void* slot, unsigned int kind, uint16_t channel, unsigned int payload) {
    jumptable_3A48(slot, kind, static_cast<unsigned int>(channel), payload);
}
