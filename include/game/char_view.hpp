/**
 * char_view.hpp — Character View System Classes
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * Character viewing/selection UI data structures and state management.
 * These classes handle character model display, camera control, and
 * UI state for character selection screens.
 * 
 * Architecture:
 *   - pongAttractState: Base state machine state for all attract mode screens
 *     (logos, menus, character selection). Manages UI screen object lifecycle.
 *   
 *   - pongCharViewState: Derived state for character viewing/selection.
 *     Handles input, transitions, and rendering for character selection UI.
 *   
 *   - charViewData: Main data container with serialized XML fields.
 *     Manages array of 2D positions for character placement in UI.
 *   
 *   - charViewCharData: Per-character view data (positions, animations).
 *     Serialized from XML configuration files.
 *   
 *   - charViewCS: Camera shot controller for character view screens.
 *     Manages camera positioning and transitions.
 *   
 *   - pongCharViewContext: Context/controller with multiple inheritance.
 *     Coordinates the overall character viewing experience.
 * 
 * Classes:
 *   - charViewCharData: Per-character view data (positions, animations)
 *   - charViewData: Main character view data container
 *   - charViewCS: Character view camera shot
 *   - pongCharViewState: Character view UI state (inherits from pongAttractState)
 *   - pongCharViewContext: Character view context/controller
 *   - pongAttractState: Base state machine state for attract mode screens
 */

#pragma once

#include <stddef.h>
#include <stdint.h>
#include "rage/hsmState.hpp"
#include "rage/atSingleton.hpp"

// ────────────────────────────────────────────────────────────────────────────
// pongAttractState — Base State Machine State for Attract Mode
// @ vtable 0x8205E0AC
// Inherits from: hsmState
// ────────────────────────────────────────────────────────────────────────────

/**
 * Base state class for attract mode screens (logos, menus, character selection).
 * Implements hierarchical state machine pattern with UI object management.
 * 
 * Derived states: pongCharViewState, pongPauseState, pongCreditsState, etc.
 * 
 * Structure:
 *   Inherits hsmState fields (+0x00 to +0x14)
 *   +0x18: m_pScreenObject - UI screen object (32 bytes, allocated/freed)
 * 
 * Size: 0x1C (28 bytes) = hsmState (0x18) + m_pScreenObject (0x4)
 */
class pongAttractState {
public:
    // Slot methods, by the game's slot number (vtable 0x8205E0AC); not C++
    // virtuals. The game's pongAttractState isn't a rage::hsmState: its slots
    // 1..6 differ, and its fields are just the two below (0x823057E8 reads
    // +0x08, 0x8230592C +0x04). pong_states.hpp's names for the same slots
    // are in brackets.

    /**
     * GetContext @ 0x823057E8 | size: 0x18  [7, Reset]
     * Tail-calls the context object's slot 4 with r4 = 0.
     */
    void* GetContext();

    /**
     * OnExit @ 0x82306EA8 | size: 0x6C  [8, Shutdown]
     * Releases and destroys the context object.
     */
    void OnExit();

    /**
     * OnEvent @ 0x823058E0 | size: 0xC8  [11, OnEnter(int)]
     * Event 6: creates UI state; events 9, 12: no-op; others go to the manager.
     */
    void OnEvent(int32_t eventType);

    /**
     * OnExitEvent @ 0x823059A8 | size: 0xB4  [12, OnExit(int)]
     */
    void OnExitEvent(int32_t eventType);

    /**
     * GetStateName @ 0x82305A60 | size: 0xC  [13, GetName]
     */
    const char* GetStateName() const;

    /**
     * OnEnter @ 0x82305800 | size: 0xE0  [14, ProcessInput]
     * Allocates the 32-byte context object (back-pointer to this at its
     * +0x18) and stores it at +0x08.
     */
    void OnEnter();

    void**  vtable;               // +0x00
    void*   m_pManager;           // +0x04 - hsm context the state posts transitions to
    void*   m_pScreenObject;      // +0x08 - context object (32 bytes), owned
};

#if __SIZEOF_POINTER__ == 4
static_assert(offsetof(pongAttractState, m_pScreenObject) == 0x08, "");  // 0x823057E8
#endif

// ────────────────────────────────────────────────────────────────────────────
// charViewCharData — Per-Character View Data
// @ vtable 0x820762F4
// ────────────────────────────────────────────────────────────────────────────

/**
 * Stores view-specific data for a single character in the character
 * selection screen. Contains position, animation, and display parameters.
 * 
 * Serialized fields (XML):
 *   - field_10, field_14, field_18 (exact names TBD from XML)
 * 
 * Size: 0x1C (28 bytes) = vtable (4) + padding (12) + 3 fields (12)
 */
class charViewCharData {
public:
    // Virtual methods
    ~charViewCharData() = default;
    
    /**
     * IsCharacterType @ 0x8240B238 | size: 0x48
     * Type checking function - compares input ID against known character types
     */
    bool IsCharacterType(uint32_t typeId);
    
    /**
     * Serialize @ 0x8240B280 | size: 0x8C
     * Serialize character view data to XML/binary format
     */
    void Serialize(void* serializer);
    
    /**
     * GetDataInfo @ 0x8230A4F8 | size: 0xC
     * Get character view data size or type info
     */
    uint32_t GetDataInfo();

protected:
    void** m_vtable;              // +0x00
    uint32_t m_padding[3];        // +0x04-0x0F
    
    // Serialized fields (exact types TBD from usage)
    uint32_t m_field_10;          // +0x10 - XML field name TBD
    uint32_t m_field_14;          // +0x14 - XML field name TBD
    uint32_t m_field_18;          // +0x18 - XML field name TBD
};

// static_assert(sizeof(charViewCharData) == 0x1C, "charViewCharData size mismatch");  // PPC-only

// ────────────────────────────────────────────────────────────────────────────
// charViewData — Main Character View Data Container
// @ vtable 0x8207635C
// ────────────────────────────────────────────────────────────────────────────

/**
 * Main data container for the character view system. Manages multiple
 * character view entries, camera positions, and UI layout data.
 * 
 * Contains a large number of serialized fields (22+ fields) and manages
 * a dynamically allocated array of view elements (2D positions per character).
 * 
 * Data Flow:
 *   1. LoadViewData() allocates array based on character count from game data manager
 *   2. Initializes each element to (0.0f, 0.0f)
 *   3. Processes linked list of character data (m_pLinkedListHead)
 *   4. For each character matching type filter, looks up index and sets position
 * 
 * Serialized fields (XML):
 *   - field_10, field_14, field_18, field_1C, field_20, field_24
 *   - field_28, field_2C, field_40, field_44, field_4C, field_50
 *   - field_58, field_5C, field_60, field_64
 *   - field_F0, field_F4, field_120, field_124, field_150, field_154
 * 
 * Size: 0x184 (388 bytes)
 */
class charViewData {
public:
    // Virtual methods
    
    /**
     * ~charViewData @ 0x8240B530 | size: 0x68
     * Destructor - frees allocated view data array
     */
    ~charViewData();
    
    /**
     * Initialize @ 0x8240B598 | size: 0x24
     * Initialize or reset view data
     */
    void Initialize();
    
    /**
     * LoadViewData @ 0x8240B5C0 | size: 0x1AC
     * Load and populate character view data from game data
     * Allocates array, initializes elements, processes linked list
     */
    void LoadViewData();
    
    /**
     * ValidateData @ 0x8240B310 | size: 0x48
     * Type checking or validation function
     */
    bool ValidateData(uint32_t param);
    
    /**
     * Serialize @ 0x8240B770 | size: 0x47C
     * Serialize all character view data (22+ fields)
     */
    void Serialize(void* serializer);
    
    /**
     * GetDataInfo @ 0x8231F408 | size: 0xC
     * Get data info or size
     */
    uint32_t GetDataInfo();

protected:
    void** m_vtable;              // +0x00
    uint32_t m_padding[2];        // +0x04-0x0B
    void* m_pLinkedListHead;      // +0x0C - linked list of view elements
    
    // Serialized data fields (types inferred from serialization)
    // XML field names TBD - need to extract from string table
    uint32_t m_field_10;          // +0x10
    uint32_t m_field_14;          // +0x14
    uint32_t m_field_18;          // +0x18
    uint32_t m_field_1C;          // +0x1C
    uint32_t m_field_20;          // +0x20
    uint32_t m_field_24;          // +0x24
    uint32_t m_field_28;          // +0x28
    uint32_t m_field_2C;          // +0x2C
    uint8_t  _pad30[0x10];       // +0x30..+0x3F
    uint32_t m_field_40;          // +0x40
    uint32_t m_field_44;          // +0x44
    uint8_t  _pad48[0x4];       // +0x48..+0x4B
    uint32_t m_field_4C;          // +0x4C
    uint32_t m_field_50;          // +0x50
    uint8_t  _pad54[0x4];       // +0x54..+0x57
    uint32_t m_field_58;          // +0x58
    uint32_t m_field_5C;          // +0x5C
    uint32_t m_field_60;          // +0x60
    uint32_t m_field_64;          // +0x64
    uint8_t  _pad68[0x88];       // +0x68..+0xEF
    uint32_t m_field_F0;          // +0xF0
    uint32_t m_field_F4;          // +0xF4
    uint8_t  _padF8[0x28];       // +0xF8..+0x11F
    uint32_t m_field_120;          // +0x120
    uint32_t m_field_124;          // +0x124
    uint8_t  _pad128[0x28];       // +0x128..+0x14F
    uint32_t m_field_150;          // +0x150
    uint32_t m_field_154;          // +0x154
    uint8_t  _pad158[0x24];      // +0x158..+0x17B

    void* m_pAllocatedData;       // +0x17C (380) - array of 2D position elements
    uint16_t m_currentCount;      // +0x180 (384) - current element count
    uint16_t m_allocatedSize;     // +0x182 (386) - allocated array size; the dtor frees +0x17C when non-zero (0x8240B54C)
};

// static_assert(sizeof(charViewData) == 0x184, "charViewData size mismatch");  // PPC-only

// ────────────────────────────────────────────────────────────────────────────
// charViewCS — Character View Camera Shot
// @ vtable 0x820362C0
// ────────────────────────────────────────────────────────────────────────────

/**
 * Camera shot controller for character view screens.
 * Manages camera positioning, transitions, and rendering for character display.
 * 
 * Virtual methods need better names - research ongoing.
 */
class charViewCS {
public:
    // Virtual methods
    
    /**
     * ~charViewCS @ 0x8216BD20 | size: 0x68
     * Destructor - cleans up embedded object at +292
     */
    ~charViewCS();
    
    // TODO: Research and rename these methods
    /**
     * RegisterXmlFields @ 0x8216DBB8
     * Registers 6 XML-serializable fields (bound offset/size/shadows) with the
     * parser infrastructure. Calls pongHairData_7B60_g for each field at
     * offsets +156, +160, +164, +168, +172, +180.
     */
    void RegisterXmlFields(void* parser);   // vfn_3 @ 0x8216DBB8

    /**
     * Validate @ 0x8216DCB0
     * Tail-calls phBoundCapsule_DB10_g to validate bound data.
     */
    void Validate();                        // vfn_4 @ 0x8216DCB0

    /**
     * GetName @ 0x8216DB00
     * Returns a constant string "many bounds specified (Max=%d)" (class/error label).
     */
    const char* GetName();                  // vfn_6 @ 0x8216DB00

    /**
     * GetVariantName @ 0x82177840
     * Returns a constant string "Shadows:" (configuration block name).
     */
    const char* GetVariantName();           // vfn_7 @ 0x82177840

    /**
     * Update @ 0x8216C200 (size: 0x510)
     * Large per-frame update routine — animation/blend and driver dispatch.
     */
    void Update();                          // vfn_9 @ 0x8216C200

    /**
     * RecalcBounds @ 0x8216BED0
     * Iterates 4 bound slots; if bound count matches slot index and count >= 4,
     * calls RecalcBoundSlot(slot).
     */
    void RecalcBounds();                    // vfn_10 @ 0x8216BED0

    /**
     * PurgeFilteredNodes @ 0x8216DB88
     * Walks the global active-node linked list at lbl_825CA938/944, keeping
     * nodes whose type is one of {5, 6, 12, 13, 14, 16} and recycling the rest
     * to the free list. Returns true if any kept node was found.
     */
    bool PurgeFilteredNodes();              // vfn_11 @ 0x8216DB88

    // ── non-virtual helpers ──
    /**
     * RecalcBoundSlot @ 0x8216BF18 (size: 0x1E4)
     * Normalizes a single packed int16 bound descriptor into a float axis
     * component (X/Y/Z). Called by RecalcBounds() per axis.
     * @param slot  bound index in [0..3]
     */
    void RecalcBoundSlot(int slot);

    /**
     * ApplyAxis @ 0x8216C100 (size: 0x78)
     * Helper: clamps a bound's world-space position along one axis using the
     * bound's half-extent and the character's scale. Writes result back into
     * the per-slot array at this[+64 + axis*4].
     * @param axis  0=X, 1=Y, 2=Z
     */
    void ApplyAxis(int axis);

    /**
     * DispatchBoundsOrLookAt @ 0x8216C710 (size: 0x10C)
     * If the shot is in state 1 (field +284), computes |x|+|y|+|z| and
     * compares to bound-extent threshold, then virtual-dispatches one of
     * slots 12, 16, or 19 on the embedded sub-object at this+292. Otherwise
     * falls through to slot 19.
     */
    void DispatchBoundsOrLookAt();

protected:
    void** m_vtable;              // +0x00
    uint8_t m_data[288];          // +0x04-0x123
    uint32_t m_embeddedObject;    // +0x124 (292) - cleaned up in destructor
};

// ────────────────────────────────────────────────────────────────────────────
// pongCharViewState — Character View UI State
// @ vtable 0x8205F174
// Inherits from: pongAttractState
// ────────────────────────────────────────────────────────────────────────────

/**
 * UI state machine state for character viewing/selection screens.
 * Handles input, transitions, and rendering for character selection UI.
 */
class pongCharViewState : public pongAttractState {
public:
    // Virtual methods
    
    /**
     * ~pongCharViewState @ 0x8230C490 | size: 0x68
     * Destructor - calls parent OnExit for cleanup
     */
    ~pongCharViewState();

    /**
     * OnEnterEvent @ 0x8230C5F8 | size: 0xB8
     * Handles enter-phase events (event 6 sets up char view display)
     */
    void OnEnterEvent(int32_t eventType);

    /**
     * OnExitEvent @ 0x8230C6B0 | size: 0xD8
     * Handles exit-phase events (event 6 cleans up char view display)
     */
    void OnExitEvent(int32_t eventType);

    /**
     * GetStateName @ 0x8230A4E8 | size: 0xC
     * Returns the state name string for this char view state
     */
    const char* GetStateName() const;

    /**
     * OnEnter @ 0x8230C4F8 | size: 0x100
     * Allocates and initializes pongCharViewContext (100 bytes)
     */
    void OnEnter();

protected:
    // Inherits all fields from pongAttractState
    // Minimal additional data members
};

// ────────────────────────────────────────────────────────────────────────────
// pongCharViewContext — Character View Context/Controller
// @ vtables 0x8205F1BC, 0x8205F1D4 (multiple inheritance)
// ────────────────────────────────────────────────────────────────────────────

/**
 * Context/controller for character view system. Manages the overall
 * character viewing experience including camera, UI, and state transitions.
 * 
 * Uses multiple inheritance (2 vtables) for different interfaces.
 * 
 * Virtual methods need better names - research ongoing.
 */
class pongCharViewContext {
public:
    // Virtual methods

    /**
     * ~pongCharViewContext @ 0x8230A600 | size: 0xAC
     * Destructor - cleans up managed object at +44 and embedded object at +80
     */
    ~pongCharViewContext();

    /**
     * RegisterSceneSlot (vfn_11)
     * @ 0x8230A898 | size: 0x60
     * Registers this context (more precisely its secondary-vtable sub-object
     * at this+20) in the global UI scene slot table so the renderer can tick
     * it each frame. Bumps the global slot counter (at 0x825C9F64), writes
     * a tag byte (=128), type code (=20), and slot pointer into the three
     * parallel arrays. Returns 1 on success.
     */
    bool RegisterSceneSlot();

    /**
     * ReleasePoseSource (vfn_12)
     * @ 0x8230AB50 | size: 0x54
     * If a pose source object is mounted at this+44, invokes its vtable
     * slot 0 destructor (with deleting flag = 1) and nulls the pointer.
     * Returns 1 unconditionally.
     */
    bool ReleasePoseSource();

    /**
     * TickScene (vfn_16)
     * @ 0x8230AC90 | size: 0x2BC
     * Per-frame update dispatcher. When gameplay is paused (+495 flag) or
     * character selection is gated by the game-data-manager flag at +24,
     * drives the full character-view update chain: arms/disarms the source,
     * advances browse stepping (pg_B138 / pg_B3C0), resets view bound,
     * iterates both char slots calling AdvanceCharSlot + post-select, then
     * rebinds bound capsule + camera shot. Unlifted body kept as thunk due
     * to vector/float intensity; logic path is documented inline.
     */
    void TickScene();

    /**
     * UpdateMountedChars (vfn_17)
     * @ 0x8230AF50 | size: 0xAC
     * If the update gate is open (same pause/selection check as TickScene),
     * walks both mounted-character slot flags at this[+77..+78]. For each
     * active slot, looks up the char entry in the global data manager at
     * offset 25648 and calls vtable slot 6 on it (the per-character tick
     * that drives the pose/animation in the preview scene).
     */
    void UpdateMountedChars();

    /**
     * UnmountCharSlots (vfn_18)
     * @ 0x8230C0A8 | size: 0x220
     * Scene-tear-down counterpart of UpdateMountedChars. If a pose source
     * is mounted at +44 it issues the per-char clean-up call (slot 6) and
     * then clears the "active" byte (+212) and "visible" byte (+288) on
     * the two char entries, honoring the global view-kill flag at +576 of
     * the game data manager. Used on state exit to return the preview rig
     * to idle.
     */
    void UnmountCharSlots();

    /**
     * InitScene (vfn_23)
     * @ 0x8230A8F8 | size: 0x254
     * Scene initialiser — allocates the 1288-byte pose-source object via
     * vtable slot 1 on the scene allocator, stores it at this+44, loads
     * settings.xml into the embedded atArray at this+88, walks the parsed
     * node tree to pick the first node matching the "char view" filter
     * (vtable slot 20), records it at this+96, and cleans up temporary
     * xmlTree buffers. Called from pongCharViewState::OnEnter.
     */
    void InitScene();

protected:
    void** m_vtable;              // +0x00 - primary vtable
    uint8_t m_data1[16];          // +0x04-0x13
    void** m_vtable2;             // +0x14 (20) - secondary vtable
    uint8_t m_data2[20];          // +0x18-0x2B
    void* m_pManagedObject;       // +0x2C (44) - pose source object (scene rig driver)
    uint8_t m_data3[32];          // +0x30-0x4F
    uint32_t m_embeddedObject;    // +0x50 (80) - atArray_Clear called on it
};

// ────────────────────────────────────────────────────────────────────────────
// Non-virtual scene-side helpers (free functions in the binary)
// ────────────────────────────────────────────────────────────────────────────

/**
 * ResetCharViewData @ 0x8240A570 | size: 0x8C
 * Resets the per-scene pose block (48 bytes at the input pointer) and the
 * two companion globals at 0x82625E10 / 0x82625E14 (selection counter +
 * selection flag). All orbit/pose floats (+12,+16,+28,+32,+36,+40,+44,+48)
 * are cleared to 0.0f; int indices at +4,+8,+20,+24 zero; selected char
 * index at 0x825D6B78 set to -1 (invalid).
 */
void ResetCharViewData(void* scenePoseBlock);

/**
 * AdvanceCharSlot @ 0x8230B6E8 | size: 0xF0
 * Advances per-character-slot state:
 *   - state==1 ("stepping"): bumps timer at +72; when it reaches the target
 *     pose duration from the managed pose source[+24], flips slot state to
 *     2 and, when on slot 0 with idle filter (+24 of ctx == 0, pose float
 *     +48 == 0.0f constant), fires post-select notification via slot 1118.
 *   - state==2: falls through (no-op).
 *   - other: if select index at +60 is valid and slot predicate passes,
 *     calls ref_gdDrillMovementData_B960 to apply the new pose.
 * Called twice per TickScene (once per char slot).
 */
void AdvanceCharSlot(void* ctx, int slot);

// ────────────────────────────────────────────────────────────────────────────
// hudCharView — HUD Character View Component
// @ vtable 0x8206275C
// ────────────────────────────────────────────────────────────────────────────

/**
 * HUD component for displaying character information during gameplay.
 * Separate from the character selection screen views.
 * 
 * Virtual methods need better names - research ongoing.
 */
class hudCharView {
public:
    ~hudCharView() = default;
    
    // TODO: Research and rename these methods
    void vfn_2();         // @ 0x82320D68
    void vfn_5();         // @ 0x82320BE0

protected:
    void** m_vtable;              // +0x00
};
