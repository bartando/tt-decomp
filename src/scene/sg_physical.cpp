#include "sg_physical.hpp"
#include "../physics/ph_physics.hpp"

// Draw bucket entry point -- adds a rendered object to the current frame's
// draw bucket for deferred submission.
extern "C" void pongDrawBucket_AddEntry(void* bucket, void* renderEntry, void* boundsData);  // @ 0x822278D8

// Physics system functions
extern "C" void* CreatePhysicsInstance(void* physSystem, void* physType, void* resource);  // @ 0x8227F6A8
extern "C" void* CreateSimplePhysicsInstance(void* physSystem, void* physType);             // @ 0x8227F810
extern "C" void  LinkPhysicsResource(void* physInstance, void* resource);                   // @ 0x8227D220

// Global physics system singleton
extern void* g_physicsSystem;           // @ 0x82606568 (phSimulator*)
// Global renderer state (contains camera/LOD data)
extern void* g_rendererState;           // @ 0x8260641C
extern "C" const float lbl_8202D110;   // 0.0f
// Global draw bucket for deferred rendering
extern void* g_drawBucket;              // @ 0x826064F4 (pongDrawBucketManager*)

/**
 * sgPhysicalObject::Transform
 * @ 0x823D9208 | size: 0x130
 *
 * phUpdateObject::AddToRenderBucket (0x8227D768) again, with the draw object
 * at +0x7C supplying drawable/collider/transform and the render entry at
 * +0x60 receiving the results (+0x64 lod, +0x68 visibility) and the slot-1
 * call when culled (unless +0x70 is set). The asm doesn't null-check +0x7C.
 */
void sgPhysicalObject::Transform() {
    phUpdateObject* obj = m_pDrawObject;
    if (!obj->m_pDrawable)
        return;

    void* transform;
    if (obj->m_pCollider) {
        uint8_t* state  = *(uint8_t**)((uint8_t*)obj->m_pCollider + 0x0C);
        uint8_t* frames = *(uint8_t**)(state + 0x40);
        uint32_t index  = *(uint32_t*)(state + 0x44);
        transform = *(uint8_t**)(frames + 0x14) + index * 64;
    } else {
        transform = obj->m_pTransformSrc;
        if (!transform)
            transform = (uint8_t*)obj->m_pData + 0x10;
    }

    uint8_t visible  = 0;
    float   lodParam = lbl_8202D110;
    void* drawable = obj->m_pDrawable;
    uint8_t* viewer = *(uint8_t**)((uint8_t*)g_rendererState + 0x28);
    uint8_t* view   = *(uint8_t**)(viewer + 0x2C);
    uint32_t viewArg = *(uint32_t*)(view + 0x98);
    typedef int (*VisTestFn)(void*, void*, uint32_t, uint8_t*, float*);
    VisTestFn visTest = (VisTestFn)(*(void***)drawable)[9];
    if (visTest(drawable, transform, viewArg, &visible, &lodParam)) {
        m_fRenderDistance = lodParam;
        m_nVisibility     = visible;
        void* drawable2 = m_pDrawObject->m_pDrawable;
        typedef void* (*GetPriorityFn)(void*);
        void* priority = ((GetPriorityFn)(*(void***)drawable2)[10])(drawable2);
        pongDrawBucket_AddEntry(g_drawBucket, &m_pRenderEntryVtable, priority);
    } else if (!m_bIsHidden) {
        void* entry = &m_pRenderEntryVtable;
        typedef void (*EntrySlotFn)(void*);
        ((EntrySlotFn)m_pRenderEntryVtable[1])(entry);
    }
}

/**
 * sgPhysicalObject::PhysicsUpdate
 * @ 0x823D9368 | size: 0x14
 *
 * Tail-calls the draw object's slot 5 (phUpdateObject::RenderShadow); f1 is
 * passed through untouched.
 */
void sgPhysicalObject::PhysicsUpdate(float shadowScale) {
    typedef void (*Slot5Fn)(phUpdateObject*, float);
    ((Slot5Fn)m_pDrawObject->vtable[5])(m_pDrawObject, shadowScale);
}

/**
 * sgPhysicalObject::AdvancedPhysics
 * @ 0x823D98C0 | size: 0x7C
 *
 * Creates a physics instance: articulated (ragdoll/skeleton) or simple (rigid body).
 */
void sgPhysicalObject::AdvancedPhysics() {
    if (m_bIsArticulated) {
        // Create articulated physics instance (ragdoll/skeleton)
        void* pNewInstance = CreatePhysicsInstance(g_physicsSystem, m_pPhysicsType, m_pName);
        m_pDrawObject = (phUpdateObject*)pNewInstance;

        // Copy secondary data from physics type (+4)
        m_nSecondaryData = *(uint32_t*)((char*)m_pPhysicsType + 4);
    } else {
        // Create simple physics instance (rigid body)
        void* pNewInstance = CreateSimplePhysicsInstance(g_physicsSystem, m_pPhysicsType);
        m_pDrawObject = (phUpdateObject*)pNewInstance;

        // Link the resource/mesh to the physics instance
        LinkPhysicsResource((void*)pNewInstance, m_pName);
    }
}
