#pragma once
/**
 * sg_drawable.hpp — sgRMDrawable renderable mesh node
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * vtable @ 0x82071C6C
 * Inherits from: sgNode
 * Size: ~88 bytes
 */

#include "sg_node.hpp"

// ---------------------------------------------------------------------------
// sgRMDrawable  —  renderable mesh scene-graph node
//
// Layout (confirmed from recomp of 0x823D8E30, 0x823D8CD8):
//   +0x00  void**       vtable              (from sgNode)
//   +0x04  sgNode*      m_pParent           (from sgNode)
//   +0x08  sgNode*      m_pNextSibling      (from sgNode)
//   +0x0C  sgNode*      m_pFirstChild       (from sgNode)
//   +0x10  float[4][4]  m_transform         — AltiVec-aligned 4×4 matrix (64 bytes)
//                                             Copied with VMX128 SIMD (lvx128/stvx)
//   +0x50  char*        m_pName         — "name" field (heap string); freed in destructor
//   +0x54  void*        m_pPhysics          — physics instance pointer
// ---------------------------------------------------------------------------
struct sgRMDrawable : sgNode {
    float  m_transform[4][4];  // +0x10  AltiVec-aligned 4×4 world matrix
    char*  m_pName;            // +0x50  "name" (heap string, freed by the destructor)
    void*  m_pPhysics;         // +0x54  physics instance (atSingleton-derived)

    // slot  0 — ~sgRMDrawable @ 0x823D8E30 (size 0x74)
    //   Frees m_pName via rage_free, calls atSingleton base dtor.
    ~sgRMDrawable();

    // slot 19 — GetTypeName() @ 0x823D8F80 (size 0x0C)
    //   Returns pointer to static string "sgRMDrawable".
    const char* GetTypeName() const;

    // slot 20 — IsType(uint32_t typeId) @ 0x823D8DF8 (size 0x38)
    //   Checks typeId against two global type-IDs (sgRMDrawable + sgNode chain).
    int IsType(uint32_t typeId);

    // slot 21 — RegisterFields() @ 0x823D8F18 (size 0x64)
    //   Registers m_pName and m_transform for RAGE serialization.
    void RegisterFields();

    // slot 22 — Render() @ 0x823D8D18 (size 0x0C)
    void Render();

    // slot 29 — UpdateBounds() @ 0x823D8EA8 (size 0x6C)
    void UpdateBounds();

    // slot 32 — SetTransform(const float mtx[4][4]) @ 0x823D8CD8 (size 0x40)
    //   Uses VMX128 SIMD for aligned 64-byte matrix copy.
    void SetTransform(const float mtx[4][4]);
};
