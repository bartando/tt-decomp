/**
 * rage::swf* — Scaleform Flash UI System Classes
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * The SWF subsystem handles Flash/Scaleform UI rendering and ActionScript
 * execution. These classes form the core of the game's menu and HUD system.
 * 
 * All classes are in the rage:: namespace and follow RAGE engine conventions.
 */

#pragma once

#include <cstdint>

// Forward declarations
namespace rage {
    class swfBASE;
    class swfSCRIPTOBJECT;
    class swfCONTEXT;
    class swfFILE;
    class swfINSTANCE;
    class swfACTIONFUNC;
    class swfSCRIPTARRAY;
    class swfOBJECT;
    class swfSPRITE;
    class swfFONT;
    class swfTEXT;
    class swfEDITTEXT;
    class swfSHAPE;
    class swfBUTTON;
    class swfBITMAP;
    class swfCMD;
    class swfCMD_DoAction;
    class swfCMD_DoInitAction;
    class swfCMD_PlaceObject2;
    class swfCMD_PlaceObject2ClipEvent;
    class swfCMD_RemoveObject2;
}

namespace rage {

// The transform begins at swfINSTANCE + 8; matrix is {a, b, c, d, tx, ty}.
void swfSetTransformMatrix(void* transform, const float* matrix);

// Compose signed 2.6 color multipliers and byte offsets, then apply RGBA tint.
void swfConcatColorTransform(uint8_t* out, const uint8_t* local, const uint8_t* parent,
                             uint32_t rgb, uint32_t alpha); // @ 0x823FAE98

// Compose inherited render state, traverse children, and draw leaf definitions.
void swfRenderInstanceTree(void* instance, const void* parentTransform);

struct swfFontAtlas;
// Draw one atlas glyph at the text pen position using the current SWF transform.
void swfDrawFontGlyph(const swfFontAtlas* atlas, float x, float y, float scale, int glyphIndex);

struct swfShapeFillState;
// Command: vertex count followed by float twip-coordinate pairs. Returns words consumed.
uint32_t swfDrawShapeTriangles(const swfSHAPE* shape, const void* command,
                               const void* transform, const swfShapeFillState* fill);

// SWF stroke coordinates/width are in twips. UVs use the unoffset point.
void swfEmitLineVertexOffsetX(float x, float y, float offset);
void swfEmitLineVertexOffsetY(float x, float y, float offset);
void swfDrawLine(float x0, float y0, float x1, float y1, float width);

/**
 * swfValueType — ActionScript value type constants
 *
 * Matches the type IDs used in the SWF virtual machine's {value, type} pairs.
 * Cross-referenced with gameswf's as_value::type enum.
 */
enum swfValueType : uint32_t {
    SWF_VALUE_UNDEFINED   = 1,  // Undefined value
    SWF_VALUE_NUMBER      = 2,  // Number (double)
    SWF_VALUE_DELETED     = 3,  // Deleted/secondary undefined
    SWF_VALUE_BOOLEAN     = 4,  // Boolean
    SWF_VALUE_OBJECT      = 5,  // Object (as_object*)
    SWF_VALUE_NATIVE_FUNC = 6,  // Native C function pointer
    SWF_VALUE_STRING      = 7   // String
};

/**
 * swfBASE @ vtable 0x82074CCC
 * 
 * Base class for all SWF objects. Provides fundamental vtable structure
 * and memory management for the Scaleform integration.
 */
class swfBASE {
public:
    virtual ~swfBASE();  // @ 0x823F8A98 | size: 0x48
    
protected:
    void* m_vtable;  // +0x00
};

/**
 * swfSCRIPTOBJECT @ vtable 0x82074D0C
 * 
 * ActionScript object representation. Handles script-side object instances
 * and their properties/methods.
 */
class swfSCRIPTOBJECT : public swfBASE {
public:
    swfSCRIPTOBJECT();  // @ 0x823F8AE0 | size: 0x64
    virtual ~swfSCRIPTOBJECT();  // @ 0x823F8B70 | size: 0x70

    // The Itanium ABI destructor contributes slots 0/1. Retail script slots 2..5
    // are no-ops; retaining them puts the common member API at slots 6..13.
protected:
    virtual void ReservedSlot2() {}
    virtual void ReservedSlot3() {}
    virtual void ReservedSlot4() {}
    virtual void ReservedSlot5() {}

public:
    virtual void EnumerateMembers();  // @ 0x823FED10 | size: 0x8
protected:
    virtual uint32_t ReservedSlot7() { return 0; }

public:
    virtual int GetMemberCount();  // @ 0x823F8B48 | size: 0x24
    virtual int VisitMembers();  // @ 0x823FC1A0 | size: 0x8
    // Overrides may leave dirty upper return bits; callers test the low byte.
    virtual uint32_t GetMember(const char* name, void* result);  // @ 0x823FBFC0 | size: 0x1DC
    // Slot-11 status is consumed at 0x823F959C and 0x823F9798 after
    // virtual calls at 0x823F9598 and 0x823F9794; preserve all 32 bits.
    virtual uint32_t SetMember(const char* name, void* value);  // @ 0x823FC8A8 | size: 0x5C
    virtual void DeleteMember(const char* name);  // @ 0x823FC848 | size: 0x60
    virtual void Invoke(const char* methodName, void* args, int argCount, void* outResult);  // @ 0x823FEA28 | size: 0x120

protected:
    void* m_pNext;          // +0x04 - linked list next pointer
    void* m_pPrev;          // +0x08 - linked list prev pointer
    void* m_pMemberTable;   // +0x0C - SYMTAB member table pointer
};

/**
 * swfCONTEXT @ vtable 0x82074D4C
 * 
 * Flash execution context. Manages the runtime environment for ActionScript
 * execution including variable scope and function calls.
 */
class swfCONTEXT : public swfBASE {
public:
    virtual ~swfCONTEXT();  // @ 0x823F8FF0 | size: 0x50
    virtual void ScalarDestructor(int flags);  // @ 0x823F90C8 | size: 0x16C
    virtual void Execute();  // @ 0x823F9238 | size: 0x44
};

/**
 * swfFILE @ vtable 0x82074D8C
 * 
 * Represents a loaded SWF file. Manages the file's resources including
 * sprites, fonts, shapes, and ActionScript bytecode.
 */
class swfFILE : public swfBASE {
public:
    virtual ~swfFILE();  // @ 0x823F8BE0 | size: 0xDC
    virtual void AdvanceDefinitionFrame(swfINSTANCE* instance);
    virtual float FindExportFrame(float frameRate, const char* labelName, void* context);  // @ 0x823F9DC8 | size: 0xD4
};

/**
 * swfINSTANCE @ vtable 0x82074DCC
 * 
 * Instance of a Flash display object on stage. Represents a placed sprite,
 * shape, or other visual element with transform and properties.
 */
class swfINSTANCE : public swfSCRIPTOBJECT {
public:
    virtual ~swfINSTANCE();  // @ 0x823FB600 | size: 0x70
    virtual void GotoFrame(uint32_t targetFrame, uint32_t skipActions);  // @ 0x823FB7A8 | size: 0xF8
    virtual void NextFrame(void* context);  // @ 0x823FB8A0 | size: 0x7C
    virtual void PrevFrame();  // @ 0x823FB920 | size: 0x50
    virtual void MarkDirty();  // @ 0x823FB760 | size: 0x44
    virtual void SetVisible();  // @ 0x823FB150 | size: 0xC
    void EnumerateMembers() override;  // @ 0x823FED18 | size: 0xD0
    virtual swfINSTANCE* FindOrCreateChildByDepth(uint32_t depth = 0, uint32_t character = 0,
                                                 void* definition = nullptr);  // @ 0x823FC908 | size: 0x144
    int GetMemberCount() override;  // @ 0x823FB160 | size: 0x28
    int VisitMembers() override;  // @ 0x823FBF98 | size: 0x28
    uint32_t GetMember(const char* name, void* result) override;  // @ 0x823FB970 | size: 0x624
    uint32_t SetMember(const char* name, void* value) override;  // @ 0x823FC1A8 | size: 0x5F0
    void DeleteMember(const char* name) override;  // @ 0x823FABC0 | size: 0xE8
    void Invoke(const char* methodName, void* args, int argCount, void* outResult) override;  // @ 0x823FE500 | size: 0x3D0
};

/**
 * swfACTIONFUNC @ vtable 0x82074E0C
 * 
 * ActionScript function object. Represents a callable function in the
 * ActionScript VM with bytecode and execution context.
 */
class swfACTIONFUNC : public swfSCRIPTOBJECT {
public:
    virtual ~swfACTIONFUNC();  // @ 0x82403460
    // First additional virtual after the common script API: retail slot 14.
    virtual void Execute(void* args, int argCount, void* thisArg, int flags);  // [14] @ 0x823FF590 — AS function call entry
    // Legacy host methods below append after Execute; their retail signatures
    // do not override the reserved base slots (nor the host deleting destructor).
    virtual void ScalarDtor(int flags);  // @ 0x823FF4E8
    virtual void NextFrame();  // @ 0x823FF500
    virtual void PrevFrame();  // @ 0x823FF518
    virtual void MarkDirty();  // @ 0x823FF530
    virtual void SetVisible();  // @ 0x823FF548
    void EnumerateMembers() override;  // @ 0x823FF560
    virtual void VisitChildren();  // @ 0x823FF578
    int GetMemberCount() override;  // @ 0x823FF2A8 | size: 0x44
    int VisitMembers() override;  // @ 0x823FF3C0 | size: 0xDC
    uint32_t GetMember(const char* name, void* result) override;  // @ 0x823FF2F0 | size: 0xCC
    uint32_t SetMember(const char* name, void* value) override;  // @ 0x823FF4A0 | size: 0x14
    void DeleteMember(const char* name) override;  // @ 0x823FF4B8 | size: 0x14
    void Invoke(const char* methodName, void* args, int argCount, void* outResult) override;  // @ 0x823FF4D0

    // ── member fields ──
    uint8_t     _padAction04[112];   // 20-byte script base -> local count at +0x84
    int         m_localCount;        // +132 (0x84)
    uint8_t     _padLocalTable[7192]; // local name table (+136 .. +7327)
    void*       m_pLocalValues;      // +7328 (0x1CA0)
    // m_pInnerObject at +7332 wraps a swfINSTANCE (MovieClip) for AS closures.
    // Declared as swfINSTANCE* so forwarding thunks can use virtual dispatch.
    swfINSTANCE* m_pInnerObject;     // +7332 (0x1CA4)
};

static_assert(sizeof(void*) != 4 || __builtin_offsetof(swfACTIONFUNC, m_localCount) == 0x84,
              "swfACTIONFUNC local count layout");
static_assert(sizeof(void*) != 4 || __builtin_offsetof(swfACTIONFUNC, m_pInnerObject) == 0x1CA4,
              "swfACTIONFUNC inner object layout");

/**
 * swfSCRIPTARRAY @ vtable 0x82074E4C
 * 
 * ActionScript array object. Implements dynamic arrays accessible from
 * ActionScript code.
 */
class swfSCRIPTARRAY : public swfSCRIPTOBJECT {
public:
    virtual ~swfSCRIPTARRAY();  // @ 0x823FF218 | size: 0x8C
    uint32_t GetMember(const char* name, void* result) override;  // @ 0x823FEB48 | size: 0xF0
    uint32_t SetMember(const char* name, void* value) override;  // @ 0x823FEC38 | size: 0x70
};

/**
 * swfOBJECT @ vtable 0x82074E8C
 * 
 * Generic Flash object. Base for display list objects that can be
 * instantiated and placed on the stage.
 */
class swfOBJECT {
public:
    // Retail has one deleting-destructor slot. A C++ virtual destructor would
    // add a second slot under Itanium and displace Render from retail slot 1.
    virtual void Destroy(uint32_t flags) = 0;
    virtual void Render(const void* transform, int mode) = 0;
    ~swfOBJECT();
};

/**
 * swfSPRITE @ vtable 0x82074ECC
 * 
 * Flash sprite/movie clip. Contains timeline, frames, and child objects.
 * The primary container for animated Flash content.
 */
class swfSPRITE : public swfOBJECT {
public:
    ~swfSPRITE();
};

/**
 * swfFONT @ vtable 0x82074F0C
 * 
 * Flash font definition. Contains glyph shapes and metrics for text
 * rendering in the Flash UI.
 */
class swfFONT : public swfOBJECT {
public:
    ~swfFONT();
};

/**
 * swfTEXT @ vtable 0x82074F4C
 * 
 * Static text field. Represents non-editable text placed in the Flash
 * authoring tool.
 */
class swfTEXT : public swfOBJECT {
public:
    ~swfTEXT();
};

/**
 * swfEDITTEXT @ vtable 0x82074F8C
 * 
 * Dynamic/editable text field. Supports user input and dynamic text
 * updates from ActionScript.
 */
class swfEDITTEXT : public swfOBJECT {
public:
    ~swfEDITTEXT();
};

/**
 * swfSHAPE @ vtable 0x82074FCC
 * 
 * Vector shape definition. Contains fill styles, line styles, and
 * edge records for rendering vector graphics.
 */
class swfSHAPE : public swfOBJECT {
public:
    ~swfSHAPE();
    void Render(const void* transform, int mode) override; // @ 0x82406C58

    uint32_t resourceId;                 // +0x04
    swfShapeFillState* fills;             // +0x08, 40-byte entries
    const uint64_t* strokes;              // +0x0C, width +0, ARGB +4
    const uint32_t* commands;             // +0x10
};

/**
 * swfBUTTON @ vtable 0x8207500C
 * 
 * Interactive button. Handles mouse events and button state transitions
 * (up, over, down).
 */
class swfBUTTON : public swfOBJECT {
public:
    ~swfBUTTON();
};

/**
 * swfBITMAP @ vtable 0x8207504C
 * 
 * Bitmap image resource. Represents raster images embedded in or loaded
 * by the SWF file.
 */
class swfBITMAP : public swfOBJECT {
public:
    ~swfBITMAP();
};

/**
 * swfCMD @ vtable 0x8207508C
 * 
 * Base class for SWF tag commands. Represents operations in the SWF
 * bytecode stream.
 */
class swfCMD : public swfBASE {
public:
    virtual ~swfCMD();
};

/**
 * swfCMD_DoAction @ vtable 0x820750CC
 * 
 * DoAction tag. Contains ActionScript bytecode to execute when the
 * playhead reaches this frame.
 */
class swfCMD_DoAction : public swfCMD {
public:
    virtual ~swfCMD_DoAction();
};

/**
 * swfCMD_DoInitAction @ vtable 0x8207510C
 * 
 * DoInitAction tag. Executes ActionScript initialization code for a
 * sprite, runs once when the sprite is first instantiated.
 */
class swfCMD_DoInitAction : public swfCMD {
public:
    virtual ~swfCMD_DoInitAction();
    virtual void Cleanup();  // @ 0x821EFC00 | size: 0x10
};

/**
 * swfCMD_PlaceObject2 @ vtable 0x8207514C
 * 
 * PlaceObject2 tag. Places, moves, or modifies an object on the display
 * list with transform, color, and clip actions.
 */
class swfCMD_PlaceObject2 : public swfCMD {
public:
    virtual ~swfCMD_PlaceObject2();
    void Execute(swfINSTANCE* parent);  // Guest vtable slot 1; dispatched explicitly.
};

/**
 * swfCMD_PlaceObject2ClipEvent @ vtable 0x8207518C
 * 
 * Clip event handler for PlaceObject2. Defines ActionScript code to
 * execute in response to movie clip events (load, enterFrame, etc).
 */
class swfCMD_PlaceObject2ClipEvent : public swfBASE {
public:
    virtual ~swfCMD_PlaceObject2ClipEvent();
    void Execute(swfINSTANCE* parent);  // Guest vtable slot 1; dispatched explicitly.
    void UpdateClipEvents(swfINSTANCE* parent); // Guest vtable slot 3; dispatched explicitly.
};

/**
 * swfCMD_RemoveObject2 @ vtable 0x820751CC
 * 
 * RemoveObject2 tag. Removes an object from the display list at the
 * specified depth.
 */
class swfCMD_RemoveObject2 : public swfCMD {
public:
    virtual ~swfCMD_RemoveObject2();
};

} // namespace rage
