#include "rage/xml_tree.hpp"
#include "sg_scene_graph.hpp"

// RAGE engine heap free — canonical name declared in rage/rage_cm_types.hpp
extern void rage_free(void* ptr);               // @ 0x820C00C0

// sgSceneGraph internal destructor body @ 0x823D9AF8
// Frees the seven traverse-list pointers at offsets +0x10..+0x2C
// (skipping +0x1C), then calls atArray_Clear (rage::gameObject base dtor).
// Named after its address in the translation unit that contains sgSceneGraph.
// rage_8070 — rage::gameObject base destructor (clears atArray-like state)

// Forward declaration
void sgSceneGraph_FreeLists(void* obj);

/**
 * sgSceneGraph::~sgSceneGraph
 * @ 0x823D9AA8 | size: 0x50
 *
 * Resets the vtable to rage::gameObject's vtable, then calls
 * sgSceneGraph_FreeLists which frees all seven traversal-list
 * allocations and invokes the rage::gameObject base destructor.
 * The scalar-dtor wrapper handles the optional rage_free(this).
 */
sgSceneGraph::~sgSceneGraph() {
    sgSceneGraph_FreeLists(this);
}

/**
 * sgSceneGraph_FreeLists @ 0x823D9AF8 | size: 0x74
 *
 * Frees the seven traversal-list allocations stored at offsets
 * +0x10, +0x14, +0x18, +0x20, +0x24, +0x28, +0x2C (skipping +0x1C).
 * After freeing, resets the vtable to rage::gameObject and calls
 * the base destructor (rage_8070 @ 0x821A8070).
 */
void sgSceneGraph_FreeLists(void* obj) {
    uint8_t* self = static_cast<uint8_t*>(obj);

    // Free traversal list pointers at known offsets
    // Order matches the recomp: +20, +24, +32, +36, +40, +44, +16
    rage_free(*reinterpret_cast<void**>(self + 20));  // m_pTraverseList2
    rage_free(*reinterpret_cast<void**>(self + 24));  // m_pTraverseList3
    rage_free(*reinterpret_cast<void**>(self + 32));  // m_pTraverseList4
    rage_free(*reinterpret_cast<void**>(self + 36));  // m_pTraverseList5
    rage_free(*reinterpret_cast<void**>(self + 40));  // m_pTraverseList6
    rage_free(*reinterpret_cast<void**>(self + 44));  // m_pTraverseList7
    rage_free(*reinterpret_cast<void**>(self + 16));  // m_pTraverseList1

    // Call rage::gameObject base destructor
    atArray_Clear(obj);
}

// ---------------------------------------------------------------------------
// Traversal visitor thunks
//
// Each visitor's Apply is a single indirect tail-call into a fixed slot of
// the target node's own vtable. The compiler emits them all as:
//     lwz  r11, 0(r4)        ; load pNode->vtable
//     mr   r3,  r4           ; this = pNode
//     lwz  r10, SLOT*4(r11)  ; vtable[slotN]
//     mtctr r10 / bctr       ; tail-call
//
// The per-visitor difference is exactly the slot index; treating them as a
// family keeps the intent visible and avoids duplicating the dispatch logic.
// ---------------------------------------------------------------------------
namespace {

typedef void (*sgNodeVisitFn)(sgNode*);

// Indices into sgNode's vtable (slot-index, not byte offset).
enum sgNodeVisitorSlot : unsigned {
    kSlotInitialize = 23,  // byte  92 — Initialize()
    kSlotTerminate  = 24,  // byte  96 — Terminate()
    kSlotReset      = 25,  // byte 100 — Reset()
    kSlotRestart    = 26,  // byte 104 — Restart()
    kSlotUpdate     = 27,  // byte 108 — Update()
    kSlotPostUpdate = 28,  // byte 112 — PostUpdate()
    kSlotDraw       = 29,  // byte 116 — Draw()
    kSlotDrawDebug  = 30,  // byte 120 — DrawDebug()
};

// Fetch the node's virtual at the given slot and invoke it on pNode.
// Matches the `lwz r11,0(r4) / lwz r10,SLOT*4(r11) / mtctr / bctr` pattern.
static inline void DispatchNodeVisit(sgNode* pNode, sgNodeVisitorSlot slot) {
    sgNodeVisitFn fn = reinterpret_cast<sgNodeVisitFn>(pNode->vtable[slot]);
    fn(pNode);
}

}  // namespace

/**
 * sgTraverseInitialize::Apply
 * @ 0x823D9F10 | size: 0x14
 *
 * Invokes the node's Initialize() virtual (sgNode vtable slot 23).
 */
void sgTraverseInitialize::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotInitialize);
}

/**
 * sgTraverseTerminate::Apply
 * @ 0x823D9FB8 | size: 0x14
 *
 * Invokes the node's Terminate() virtual (sgNode vtable slot 24).
 */
void sgTraverseTerminate::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotTerminate);
}

/**
 * sgTraverseReset::Apply
 * @ 0x823D9F28 | size: 0x14
 *
 * Invokes the node's Reset() virtual (sgNode vtable slot 25).
 */
void sgTraverseReset::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotReset);
}

/**
 * sgTraverseRestart::Apply
 * @ 0x823D9F40 | size: 0x14
 *
 * Invokes the node's Restart() virtual (sgNode vtable slot 26).
 */
void sgTraverseRestart::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotRestart);
}

/**
 * sgTraverseUpdate::Apply
 * @ 0x823D9F58 | size: 0x14
 *
 * Invokes the node's Update() virtual (sgNode vtable slot 27).
 */
void sgTraverseUpdate::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotUpdate);
}

/**
 * sgTraversePostUpdate::Apply
 * @ 0x823D9F70 | size: 0x14
 *
 * Invokes the node's PostUpdate() virtual (sgNode vtable slot 28).
 */
void sgTraversePostUpdate::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotPostUpdate);
}

/**
 * sgTraverseDraw::Apply
 * @ 0x823D9F88 | size: 0x14
 *
 * Invokes the node's Draw() virtual (sgNode vtable slot 29).
 */
void sgTraverseDraw::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotDraw);
}

/**
 * sgTraverseDrawDebug::Apply
 * @ 0x823D9FA0 | size: 0x14
 *
 * Invokes the node's DrawDebug() virtual (sgNode vtable slot 30).
 */
void sgTraverseDrawDebug::Apply(sgNode* pNode) {
    DispatchNodeVisit(pNode, kSlotDrawDebug);
}

// ---------------------------------------------------------------------------
// sgTypedIterator — stateful pre-order walker with an sgNode type filter
//
// Prime and Advance are mutually recursive through the iterator state:
//   Advance() moves m_pCurrent to the next pre-order node, then calls Prime()
//   Prime()   checks the type filter; on miss it logs and calls Advance()
//
// Together they land m_pCurrent on the next sgNode-compatible node or
// leave it nullptr when the walk is exhausted.
// ---------------------------------------------------------------------------

// Loaded type ID shared with sgNode::IsType; this is a word, not its address.
extern uint32_t g_sgNode_typeId;  // @ 0x825C93D0

namespace {

// Assertion / trace format stub (4-byte `blr`-only stripped helper).
// Declared here rather than pulled in from pong_player.cpp to keep the
// scene-graph TU self-contained for lookups during link.
extern "C" void nop_8240E6D0(const char* fmt, const char* arg);   // @ 0x8240E6D0

// @ 0x82071DC8 (.rdata) — fmt passed to nop_8240E6D0
const char* const kTypeMismatchFmt = reinterpret_cast<const char*>(uintptr_t{0x82071DC8u});

}  // namespace

// @ 0x823DA0F8 | size: 0x40
// Search above node for the first sibling, without crossing the walk root.
sgNode* sgTypedIterator::FindAncestorSibling(sgNode* node) {
    for (sgNode* parent = node->m_pParent;
         parent != nullptr && parent != m_pRoot;
         parent = parent->m_pParent) {
        if (parent->m_pNextSibling != nullptr) {
            return parent->m_pNextSibling;
        }
    }
    return nullptr;
}

// @ 0x823DA070 | size: 0x88
// Leave the cursor on an sgNode; log and advance past other XML node types.
void sgTypedIterator::Prime() {
    sgNode* current = m_pCurrent;
    if (current == nullptr) {
        return;
    }
    using IsTypeFn = uint32_t (*)(sgNode*, uint32_t);
    IsTypeFn isType = reinterpret_cast<IsTypeFn>(current->vtable[20]);
    if ((isType(current, g_sgNode_typeId) & 0xFFu) != 0) {
        return;
    }
    // IsType is virtual and may change the cursor. Reload it before slot 19.
    using NameFn = const char* (*)(sgNode*);
    const char* name = reinterpret_cast<NameFn>(m_pCurrent->vtable[19])(m_pCurrent);
    nop_8240E6D0(kTypeMismatchFmt, name);
    Advance();
}

// @ 0x823D9FD0 | size: 0x9C
// Pre-order successor followed by the type filter; root bounds ancestor climbs.
void sgTypedIterator::Advance() {
    sgNode* current = m_pCurrent;
    sgNode* next = nullptr;
    if (current != nullptr) {
        if (current->m_pFirstChild != nullptr) {
            next = current->m_pFirstChild;
        } else if (current != m_pRoot) {
            next = current->m_pNextSibling;
            if (next == nullptr) {
                sgNode* parent = current->m_pParent;
                if (parent != nullptr && parent != m_pRoot) {
                    next = parent->m_pNextSibling;
                    if (next == nullptr) {
                        next = FindAncestorSibling(parent);
                    }
                }
            }
        }
    }
    m_pCurrent = next;
    Prime();
}

/**
 * sgTraverseInitialize::Traverse
 * @ 0x823D9E90 | size: 0x7C
 *
 * Iterator-driven visitor loop: snap the iterator's current pointer to its
 * root, Prime() to land on the first type-matched node, then repeatedly
 * invoke this->Apply(current) and advance until the iterator is exhausted.
 *
 * Matches the PPC body:
 *   r11 = pIter->m_pRoot;           // +0x00
 *   pIter->m_pCurrent = r11;        // +0x04 (reset)
 *   pIter->Prime();
 *   while (pIter->m_pCurrent != nullptr) {
 *       this->Apply(pIter->m_pCurrent);   // VCALL slot 1 on `this`
 *       pIter->Advance();
 *   }
 */
void sgTraverseInitialize::Traverse(sgTypedIterator* pIter) {
    // Reset walk cursor to root. The lifted asm reads +0x00 and writes
    // +0x04, so m_pCurrent starts equal to m_pRoot.
    pIter->m_pCurrent = pIter->m_pRoot;
    pIter->Prime();

    while (pIter->m_pCurrent != nullptr) {
        // VCALL slot 1 — this->Apply(current). Virtual so derived visitor
        // types (TraverseUpdate/TraverseDraw/…) would hook in via this
        // same driver, though only the Initialize specialization was
        // emitted per the symbol table.
        this->Apply(pIter->m_pCurrent);
        pIter->Advance();
    }
}
