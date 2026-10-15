#pragma once
/**
 * sg_physical.hpp — sgPhysicalObject physics-integrated scene node
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * 2 vtables — multiple/template inheritance
 * Inherits from: sgRMDrawable (primary), and a secondary render-entry base at +0x60
 */

#include "sg_drawable.hpp"
#include <stddef.h>

// Forward declare — full definition in physics/ph_physics.hpp (rage namespace)
namespace rage { struct phInst; }
using rage::phInst;

// Forward declarations for physics types
struct phBound;
struct phUpdateObject;  // physics/ph_physics.hpp

// ---------------------------------------------------------------------------
// sgPhysicalObject  —  scene node with integrated physics simulation
//
// Layout (confirmed from recomp of 0x823D9208, 0x823D98C0):
//   inherits sgRMDrawable fields (+0x00..+0x57)
//   +0x58  uint32_t  field_0x0058       — unknown (padding/flags between base and render entry)
//   +0x5C  uint32_t  field_0x005C       — unknown
//   +0x60  void**    m_renderEntry_vtable — secondary vtable for render entry (2nd RTTI @ 0x8204F408)
//   +0x64  float     m_fRenderDistance  — distance to camera (written during visibility check)
//   +0x68  uint32_t  m_nVisibility      — visibility flags from cull check
//   +0x6C  uint32_t  field_0x006C       — unknown (padding)
//   +0x70  uint8_t   m_bIsHidden        — suppresses cleanup call when invisible
//   +0x71  uint8_t   _pad71
//   +0x72  uint8_t   m_bIsArticulated   — true = ragdoll/skeleton physics, false = rigid body
//   +0x73  uint8_t   _pad73
//   +0x74  void*     m_pPhysicsType     — physics type descriptor
//   +0x78  uint32_t  m_nSecondaryData   — copied from phys type +4 on articulated creation
//   +0x7C  phUpdateObject* m_pDrawObject — built by AdvancedPhysics (0x8227F6A8 /
//          0x8227F810); Transform reads its drawable/collider/transform source
// ---------------------------------------------------------------------------
// NOTE: fields +0x58, +0x5C and +0x6C are never read/written by any lifted
// method we have; they sit between the sgRMDrawable base and the secondary
// render-entry vtable at +0x60 (and between that group and the hidden/
// articulated byte block at +0x70).  Most likely layout padding inserted
// by the multiple-vtable RTTI.  Left as opaque words until a reference
// surfaces.
struct sgPhysicalObject : sgRMDrawable {
    uint32_t field_0x0058;         // +0x58  opaque (likely MI/vtable pad)
    uint32_t field_0x005C;         // +0x5C  opaque (likely MI/vtable pad)
    void**   m_pRenderEntryVtable; // +0x60  secondary vtable (render entry)
    float    m_fRenderDistance;    // +0x64  camera distance for LOD
    uint32_t m_nVisibility;        // +0x68  visibility/cull result
    uint32_t field_0x006C;         // +0x6C  opaque (likely flag/hidden pad)
    uint8_t  m_bIsHidden;          // +0x70  suppresses cleanup when invisible
    uint8_t  _pad71;               // +0x71
    uint8_t  m_bIsArticulated;     // +0x72  articulated (ragdoll) flag
    uint8_t  _pad73;               // +0x73
    void*    m_pPhysicsType;       // +0x74  physics type descriptor
    uint32_t m_nSecondaryData;     // +0x78  secondary physics data
    phUpdateObject* m_pDrawObject; // +0x7C  draw object (phUpdateObject layout)

    // slot 29 — Transform() / visibility update @ 0x823D9208 (size 0x130)
    //   1. Bail if no physics instance or no bound.
    //   2. Pick transform source: articulation > blended pose > base.
    //   3. Virtual visibility/culling check (phBound slot 9).
    //   4. If visible: store distance + flags, add to draw bucket.
    //   5. If invisible and not m_bIsHidden: call render-entry cleanup (slot 1).
    void Transform();

    // slot 33 — @ 0x823D9368 (size 0x14)
    //   Tail-calls the draw object's slot 5 (phUpdateObject::RenderShadow), f1 untouched.
    void PhysicsUpdate(float shadowScale);

    // slot 39 — AdvancedPhysics() @ 0x823D98C0 (size 0x7C)
    //   Creates physics instance: articulated (ragdoll) or simple (rigid body).
    void AdvancedPhysics();
};

// Game layout (32-bit); the host build has 8-byte pointers.
static_assert(sizeof(void*) != 4 || offsetof(sgNode, m_pFirstChild) == 0x0C, "sgNode layout");
static_assert(sizeof(void*) != 4 || offsetof(sgRMDrawable, m_transform) == 0x10, "sgRMDrawable layout");
static_assert(sizeof(void*) != 4 || offsetof(sgRMDrawable, m_pName) == 0x50, "sgRMDrawable layout");
static_assert(sizeof(void*) != 4 || offsetof(sgPhysicalObject, m_pRenderEntryVtable) == 0x60, "sgPhysicalObject layout");
static_assert(sizeof(void*) != 4 || offsetof(sgPhysicalObject, m_bIsHidden) == 0x70, "sgPhysicalObject layout");
static_assert(sizeof(void*) != 4 || offsetof(sgPhysicalObject, m_pDrawObject) == 0x7C, "sgPhysicalObject layout");
