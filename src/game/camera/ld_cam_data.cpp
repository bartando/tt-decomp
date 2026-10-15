/**
 * ld_cam_data.cpp — camera / char-view data the image defines
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that pong_camera.cpp, char_view.cpp and
 * cm_operators.cpp reference but nothing defined. Each sits at the address in
 * its comment; constants take their value from the game image, pointers start
 * null (the image's values are PPC addresses), and vtables are null-filled
 * tables of the original's size. Names that the code uses for the same
 * address are aliases of one object.
 *
 * pong_camera.cpp and char_view.cpp both lift camBaseCS's methods (as
 * "charViewCS"), so their charViewCS_* and g_str_charViewCS_* strings are the
 * same objects under two names.
 */

#include <cstddef>
#include <cstdint>
#include "link/tt_alias.h"


// @ 0x8202C4E4 (.rdata)
extern "C" const float g_cameraFinalFloat = 0.800000012f;

// @ 0x8202D108 (.rdata) — pongCameraMgr_8CB0_2hr indexes this pool from
// 0x8202D10C and also reads the word before it, so the pool starts one early.
extern "C" alignas(16) const float g_cameraConstPool[32] = {
    1.0f, 0.5f, 0.0f, 300.0f, 100.0f, 0.0f, 1.0f, 0.75f,
    20.0f, 16000.0f, 2000.0f, 20.0f, 10000.0f, 200.0f, -96.0f, 40.0f,
    0.0f, 1.58489311e-05f, 100.0f, 1.0f, -6.0f, 1.58489311e-05f, 1.0f, 0.5f,
    0.00100000005f, 1000.0f, 2.0f, 0.00100000005f, 1.0f, 0.00499999989f, 0.00100000005f, 2.0f};
TT_DATA_ALIAS("charViewCS_oneF", "g_cameraConstPool");                     // 0x8202D108
TT_DATA_ALIAS_AT("g_cameraConstTable", "g_cameraConstPool", 4);           // 0x8202D10C
TT_DATA_ALIAS_AT("g_cameraElapsedThreshold3", "g_cameraConstPool", 4);    // 0x8202D10C
TT_DATA_ALIAS_AT("g_cameraDefaultFOV", "g_cameraConstPool", 8);           // 0x8202D110 (0.0f)

// @ 0x82035CFC (.rdata) — camShot vtable, 14 slots of PPC code addresses in
// the image, null in the port. Not const: the lift stores its address into a void*.
extern "C" void* kCamShotVTable[14] = {};

// @ 0x82036454 (.rdata) — camBaseCS vtable (charViewCS's destructor restamps
// its base), 13 slots, null in the port. Not const: the lift stores it into a void**.
extern "C" void* charViewCS_vtable[13] = {};

// @ 0x820363F8 (.rdata) — what camBaseCS vfn_6 (0x8216DB00) returns
extern "C" const char g_str_many_bounds_specified[12] = "tune/camera";
TT_DATA_ALIAS("charViewCS_typeName", "g_str_many_bounds_specified");

// @ 0x82036404..0x82036440 (.rdata) — field names camBaseCS vfn_3 (0x8216DBB8)
// registers for +0x9C, +0xA0, +0xA4, +0xA8, +0xAC and +0xB4
extern "C" const char g_str_charViewCS_field_9C[10] = "BlendTime";        // @ 0x82036404
extern "C" const char g_str_charViewCS_field_A0[10] = "BlendGoal";        // @ 0x82036410
extern "C" const char g_str_charViewCS_field_A4[10] = "CameraFOV";        // @ 0x8203641C
extern "C" const char g_str_charViewCS_field_A8[11] = "CameraNear";       // @ 0x82036428
extern "C" const char g_str_charViewCS_field_AC[10] = "CameraFar";        // @ 0x82036434
extern "C" const char g_str_charViewCS_Shadows[15] = "IgnoreTimeWarp";    // @ 0x82036440
TT_DATA_ALIAS("charViewCS_paramName0", "g_str_charViewCS_field_9C");
TT_DATA_ALIAS("charViewCS_paramName1", "g_str_charViewCS_field_A0");
TT_DATA_ALIAS("charViewCS_paramName2", "g_str_charViewCS_field_A4");
TT_DATA_ALIAS("charViewCS_paramName3", "g_str_charViewCS_field_A8");
TT_DATA_ALIAS("charViewCS_paramName4", "g_str_charViewCS_field_AC");
TT_DATA_ALIAS("charViewCS_paramName5", "g_str_charViewCS_Shadows");

// @ 0x82037440 (.rdata) — what vfn_7 (0x82177840) returns
extern "C" const char charViewCS_debugLabel[10] = "parFileIO";

// @ 0x8205EFB4 (.rdata) — command 0x8230B6E8 sends when a slot settles
extern "C" const char g_str_charview_finalize[14] = "CMD_SHOW_FADE";

// @ 0x82079BB0 (.rdata) — 1/127
extern "C" const float charViewCS_byteScale = 0.00787401572f;

// @ 0x82079BB4 (.rdata)
extern "C" const float charViewCS_byteBias = 127.5f;

// @ 0x82079E78 (.rdata)
extern "C" const float g_cameraElapsedThreshold2 = 0.375f;

// @ 0x825C8080 (.data) — the word ph_data.cpp defines as g_phCapsuleShapeK;
// the image only ever loads it
extern "C" float g_cameraElapsedThreshold1 = 0.25f;

// @ 0x825CA938 / 0x825CA944 (.data) — heads of two circular node lists
// (rage::audVoice vtable at +0, then next/prev pointing at the head itself
// while empty). The "tails" the lift reads are the heads' next fields.
struct ldCamListNode {
    void* field_00;
    ldCamListNode* next;
    ldCamListNode* prev;
    void* info;
};
static_assert(offsetof(ldCamListNode, next) == 8, "alias offsets below");
extern "C" ldCamListNode g_charViewCS_freeListHead = {
    nullptr, &g_charViewCS_freeListHead, &g_charViewCS_freeListHead, nullptr};
extern "C" ldCamListNode g_charViewCS_activeListHead = {
    nullptr, &g_charViewCS_activeListHead, &g_charViewCS_activeListHead, nullptr};
TT_DATA_ALIAS_AT("g_charViewCS_freeTail", "g_charViewCS_freeListHead", 8);      // 0x825CA93C
TT_DATA_ALIAS_AT("g_charViewCS_activeTail", "g_charViewCS_activeListHead", 8);  // 0x825CA948

// @ 0x825CAEB8 (.data) — the first 0x60 bytes of the rage::sysTimeManager
// instance (match_data.cpp's g_sysTimeManager) in the image's 32-bit layout,
// vtable slot zeroed. A copy: the original's time manager rewrites +8 at runtime.
extern "C" alignas(16) const float charViewCS_scaleTable[24] = {
    0.0f, 0.0f, 0.0166666675f, 60.0f, 0.0f, 0.0f, 60.0f, 0.0166666675f,
    0.100000001f, 9.99999975e-05f, 0.0f, 0x1p-149f, 0x1p-125f, 0.0f, 0.0f, 0.0f,
    0.0f, 0.0f, 0.0f, 0.0166666675f, 1.0f, 0.0166666675f, 0.0166666675f, 0.0f};
TT_DATA_ALIAS_AT("g_charViewCS_boundHalfExtent", "charViewCS_scaleTable", 8);  // 0x825CAEC0

// 0x825F3864.. (g_sceneSlot*) is the message-sink registry, aliased in globals.c.

// @ 0x8260641A (.data)
extern "C" uint8_t g_cameraResetFlag = 0;

// @ 0x826064C4 (.data)
extern "C" uint32_t g_cameraLerpState = 0;

// 0x8271A318/0x8271A32C (g_globalCamPtr2/1) are aliased in globals.c.
