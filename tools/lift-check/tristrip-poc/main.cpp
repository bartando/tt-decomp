// Differential test: lifted stripifier (host) vs ReXGlue recomp of the original PPC (guest memory).
#include "ppc_shim.h"
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <random>
#include <algorithm>
#include "lifted_tu.cpp"

static std::vector<uint8_t> g_memory(64u << 20);
static uint8_t* G = g_memory.data();
static uint32_t g_heap;
static std::vector<uint32_t> g_guestSizes, g_hostSizes;
static std::mt19937 rng(12345);
static int failures = 0;
#define CHECK(c, ...) do { if (!(c)) { if (failures++ < 30) { printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } } while (0)

static uint32_t GAlloc(uint32_t size) { g_heap = (g_heap + 15) & ~15u; uint32_t a = g_heap; memset(G + a, 0xCD, size); g_heap += size; return a; }

void guest_vcall(uint32_t, int slot, PPCContext& ctx, uint8_t*) {
    if (slot != 1) { printf("unexpected vcall slot %d\n", slot); exit(1); }
    if (ctx.r5.u32 != 16) { printf("unexpected align %u\n", ctx.r5.u32); exit(1); }
    g_guestSizes.push_back(ctx.r4.u32);
    ctx.r3.u64 = ctx.r4.u32 > 0x1000000 ? 0 : GAlloc(ctx.r4.u32);
}
void xe_main_thread_init_0038(PPCContext&, uint8_t*) {}
void __savegprlr_25(PPCContext&, uint8_t*) {}
void __restgprlr_25(PPCContext&, uint8_t*) {}
void memset(PPCContext& ctx, uint8_t* base) { ::memset(base + ctx.r3.u32, ctx.r4.u32 & 0xFF, ctx.r5.u32); }

void* cmOperatorCtor_Allocate(uint32_t size) {
    g_hostSizes.push_back(size);
    if (size > 0x1000000) return nullptr;
    void* p = aligned_alloc(16, (size + 15) & ~15u);
    ::memset(p, 0xAB, size);
    return p;
}

// Same slot choice in both worlds: the middle one.

void recomp_4C10_impl(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_4C10_wrh(PPCContext& ctx, uint8_t* base) {
    ctx.r1.u64 -= 496;  // the recomp does not model stwu frames
    recomp_4C10_impl(ctx, base);
    ctx.r1.u64 += 496;
}
void pongNetMessageHolder_4350_wrh(PPCContext& ctx, uint8_t* base) {
    uint32_t list = ctx.r3.u32, slot = ctx.r4.u32;
    uint32_t items = be32(base + list), count = be32(base + list + 4);
    uint32_t idx = (slot - items) / 4;
    for (uint32_t i = idx; i + 1 < count; ++i) wbe32(base + items + 4 * i, be32(base + items + 4 * (i + 1)));
    wbe32(base + list + 4, count - 1);
}

static std::vector<uint8_t> HostCacheBytes(const StripVertexCache* c) {
    std::vector<uint8_t> b(0x88, 0);
    wbe32(&b[0], (uint32_t)c->m_hits);
    for (int i = 0; i < 18; ++i) wbe16(&b[4 + 2 * i], c->m_verts[i]);
    for (int i = 0; i < 18; ++i) wbe32(&b[0x28 + 4 * i], (uint32_t)c->m_pass[i]);
    wbe32(&b[0x70], (uint32_t)c->m_next);
    for (int i = 0; i < 18; ++i) b[0x74 + i] = c->m_setByHit[i];
    return b;
}
void TriStripList::Erase(TriStrip** slot) {
    uint32_t idx = (uint32_t)(slot - m_items);
    for (uint32_t i = idx; i + 1 < m_count; ++i) m_items[i] = m_items[i + 1];
    m_count--;
}

static PPCContext NewCtx() { PPCContext c; ::memset(&c, 0, sizeof c); c.r1.u64 = 0x3F00000; c.r13.u64 = 0x1000; return c; }

static void TestAccess() {
    const uint32_t C = 0x80000;
    for (int trial = 0; trial < 2000; ++trial) {
        StripVertexCache h;
        h.m_hits = rng() % 50;
        for (int i = 0; i < 18; ++i) {
            h.m_verts[i] = rng() % 4 == 0 ? 0xFFFF : rng() % 30;
            h.m_pass[i] = rng() % 3;
            h.m_setByHit[i] = rng() % 2;
        }
        h.m_next = rng() % 18;
        std::vector<uint8_t> b = HostCacheBytes(&h);
        memcpy(G + C, b.data(), 0x88);
        for (int step = 0; step < 60; ++step) {
            int32_t pass = 1 + rng() % 2;
            uint16_t v = (uint16_t)(rng() % 30);
            int hr = h.Access(pass, v);
            PPCContext ctx = NewCtx();
            ctx.r3.u64 = C; ctx.r4.u64 = (uint32_t)pass; ctx.r5.u64 = v;
            cmOperatorCtor_57B8_w(ctx, G);
            CHECK(hr == (int)ctx.r3.u32, "Access ret host %d guest %u", hr, ctx.r3.u32);
            CHECK(memcmp(HostCacheBytes(&h).data(), G + C, 0x86) == 0, "Access state differs (trial %d step %d)", trial, step);
        }
    }
}

static std::vector<uint16_t> MakeMesh(int kind, int& numTris) {
    std::vector<uint16_t> idx;
    if (kind == 0) {  // grid of quads, consistent winding
        int w = 1 + rng() % 6, h = 1 + rng() % 6;
        for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
            uint16_t a = y * (w + 1) + x, b = a + 1, c = a + (w + 1), d = c + 1;
            idx.insert(idx.end(), {a, c, b, b, c, d});
        }
    } else {  // random soup over a small vertex pool (shared, duplicate, degenerate tris)
        int n = 1 + rng() % 40, pool = 3 + rng() % 12;
        for (int i = 0; i < n * 3; ++i) idx.push_back((uint16_t)(rng() % pool));
    }
    if (kind == 2) {  // shuffled grid triangles
        std::vector<uint16_t> g = MakeMesh(0, numTris);
        std::vector<int> order(g.size() / 3);
        for (size_t i = 0; i < order.size(); ++i) order[i] = (int)i;
        std::shuffle(order.begin(), order.end(), rng);
        idx.clear();
        for (int t : order) { int r = rng() % 3; for (int k = 0; k < 3; ++k) idx.push_back(g[t * 3 + (k + r) % 3]); }
    }
    numTris = (int)idx.size() / 3;
    return idx;
}

static void CompareStripper(const TriStripper& h, uint32_t S, const char* what) {
    CHECK((uint32_t)h.m_numTris == be32(G + S), "%s numTris", what);
    uint32_t nb = be32(G + S + 8), fl = be32(G + S + 12);
    for (int t = 0; t < h.m_numTris; ++t) {
        CHECK(h.m_triFlags[t] == be32(G + fl + 4 * t), "%s flags[%d] host %u guest %u", what, t, h.m_triFlags[t], be32(G + fl + 4 * t));
        for (int e = 0; e < 3; ++e) {
            int32_t gt = (int32_t)be32(G + nb + 24 * t + 4 * e);
            CHECK(h.m_neighbors[t].tri[e] == gt, "%s tri[%d].tri[%d] host %d guest %d", what, t, e, h.m_neighbors[t].tri[e], gt);
            if (gt != -1) {
                int32_t ge = (int32_t)be32(G + nb + 24 * t + 12 + 4 * e);
                CHECK(h.m_neighbors[t].edge[e] == ge, "%s tri[%d].edge[%d]", what, t, e);
            }
        }
    }
}

static void TestStripper() {
    for (int trial = 0; trial < 1500; ++trial) {
        int n = 0;
        std::vector<uint16_t> idx = MakeMesh(trial % 3, n);
        g_heap = 0x100000; g_guestSizes.clear(); g_hostSizes.clear();
        uint32_t I = GAlloc((uint32_t)idx.size() * 2);
        for (size_t i = 0; i < idx.size(); ++i) wbe16(G + I + 2 * i, idx[i]);
        uint32_t S = GAlloc(16);
        PPCContext ctx = NewCtx();
        ctx.r3.u64 = S; ctx.r4.u64 = (uint32_t)n; ctx.r5.u64 = I;
        cmOperatorCtor_5648_w(ctx, G);
        CHECK(ctx.r3.u32 == S, "ctor returns this");
        TriStripper h(n, idx.data());
        CompareStripper(h, S, "ctor");
        CHECK(g_guestSizes == g_hostSizes, "ctor alloc sizes");

        // LinkEdge on its own, with random flags (7 = skip) and cleared links.
        uint32_t nb = be32(G + S + 8), fl = be32(G + S + 12);
        for (int t = 0; t < n; ++t) {
            uint32_t f = rng() % 4 == 0 ? 7 : rng() % 8;
            h.m_triFlags[t] = f; wbe32(G + fl + 4 * t, f);
            for (int e = 0; e < 3; ++e) { h.m_neighbors[t].tri[e] = -1; wbe32(G + nb + 24 * t + 4 * e, 0xFFFFFFFF); }
        }
        for (int k = 0; k < 6; ++k) {
            int t = rng() % n, e = rng() % 3;
            h.LinkEdge(t, e);
            PPCContext c2 = NewCtx();
            c2.r3.u64 = S; c2.r4.u64 = (uint32_t)t; c2.r5.u64 = (uint32_t)e;
            cmOperatorCtor_54D0_wrh(c2, G);
            CompareStripper(h, S, "LinkEdge");
        }
    }
}

static void TestTriStrip() {
    const uint32_t cases[][2] = {{0, 0}, {1, 3}, {5, 7}, {0x3FFFFFFF, 0x7FFFFFFF}, {0x40000000, 0x80000000}, {0xFFFFFFFF, 1}, {100, 0}};
    for (auto& c : cases) {
        g_heap = 0x100000; g_guestSizes.clear(); g_hostSizes.clear();
        uint32_t O = GAlloc(0x18);
        PPCContext ctx = NewCtx();
        ctx.r3.u64 = O; ctx.r4.u64 = c[0]; ctx.r5.u64 = c[1];
        cmOperatorCtor_42A0_w(ctx, G);
        TriStrip h(c[0], c[1]);
        CHECK(ctx.r3.u32 == O, "TriStrip returns this");
        CHECK(h.m_numTris == be32(G + O + 4) && h.m_numIndices == be32(G + O + 12), "TriStrip counts");
        CHECK((h.m_tris == nullptr) == (be32(G + O + 8) == 0) && (h.m_indices == nullptr) == (be32(G + O + 16) == 0), "TriStrip null-ness");
        CHECK(g_guestSizes == g_hostSizes, "TriStrip alloc sizes %u,%u", c[0], c[1]); for (auto s : g_guestSizes) printf("  guest %08X\n", s); for (auto s : g_hostSizes) printf("  host %08X\n", s);
    }
}

static void TestJoin() {
    for (int trial = 0; trial < 3000; ++trial) {
        g_heap = 0x100000; g_guestSizes.clear(); g_hostSizes.clear();
        uint32_t k = 1 + rng() % 8, pool = 4 + rng() % 30;
        std::vector<TriStrip*> hostItems;
        uint32_t gItems = GAlloc(4 * k);
        for (uint32_t s = 0; s < k; ++s) {
            uint32_t len = 1 + rng() % 14;
            int32_t even = rng() % 2;
            TriStrip* hs = (TriStrip*)calloc(1, sizeof(TriStrip));
            hs->m_startsEven = even; hs->m_numIndices = len; hs->m_indices = (uint16_t*)calloc(len, 2);
            uint32_t gs = GAlloc(0x18), gi = GAlloc(2 * len);
            wbe32(G + gs, (uint32_t)even); wbe32(G + gs + 12, len); wbe32(G + gs + 16, gi);
            for (uint32_t i = 0; i < len; ++i) { uint16_t v = (uint16_t)(rng() % pool); hs->m_indices[i] = v; wbe16(G + gi + 2 * i, v); }
            hostItems.push_back(hs); wbe32(G + gItems + 4 * s, gs);
        }
        uint32_t gList = GAlloc(8); wbe32(G + gList, gItems); wbe32(G + gList + 4, k);
        uint32_t gOut = GAlloc(4); wbe32(G + gOut, 0);
        // dirty the guest stack so uninitialised cache fields differ from run to run
        for (uint32_t a = 0x3F00000; a < 0x3F00200; ++a) G[a] = (uint8_t)rng();

        PPCContext ctx = NewCtx();
        ctx.r3.u64 = 0xDEAD0; ctx.r4.u64 = gList; ctx.r5.u64 = gOut;
        cmOperatorCtor_4E90_w(ctx, G);
        uint32_t gCount = ctx.r3.u32, gBuf = be32(G + gOut);

        TriStripList hl{hostItems.data(), k};
        uint16_t* hBuf = nullptr;
        int hCount = ((TriStripper*)nullptr)->JoinStrips(&hl, &hBuf);  // doesn't touch this

        CHECK((uint32_t)hCount == gCount, "Join count host %d guest %u (trial %d)", hCount, gCount, trial);
        for (int i = 0; i < hCount && (uint32_t)hCount == gCount; ++i) CHECK(hBuf[i] == be16(G + gBuf + 2 * i), "Join out[%d]", i);
        CHECK(hl.m_count == 0 && be32(G + gList + 4) == 0, "Join empties list");
        CHECK(g_guestSizes == g_hostSizes, "Join alloc sizes");
    }
}

static void TestTakeBest() {
    const uint32_t C = 0x90000;
    for (int trial = 0; trial < 6000; ++trial) {
        g_heap = 0x100000;
        uint32_t k = trial % 50 == 0 ? 0 : 1 + rng() % 8, pool = 4 + rng() % 30;
        std::vector<TriStrip*> hostItems; std::vector<uint32_t> guestStrips;
        uint32_t gItems = GAlloc(4 * (k ? k : 1));
        for (uint32_t s = 0; s < k; ++s) {
            uint32_t len = 1 + rng() % 14;
            int32_t even = rng() % 3 == 0 ? 1 - (trial & 1) : (trial & 1);
            TriStrip* hs = (TriStrip*)calloc(1, sizeof(TriStrip));
            hs->m_startsEven = even; hs->m_numIndices = len; hs->m_indices = (uint16_t*)calloc(len, 2);
            uint32_t gs = GAlloc(0x18), gi = GAlloc(2 * len);
            wbe32(G + gs, (uint32_t)even); wbe32(G + gs + 12, len); wbe32(G + gs + 16, gi);
            for (uint32_t i = 0; i < len; ++i) { uint16_t v = (uint16_t)(rng() % pool); hs->m_indices[i] = v; wbe16(G + gi + 2 * i, v); }
            hostItems.push_back(hs); guestStrips.push_back(gs); wbe32(G + gItems + 4 * s, gs);
        }
        uint32_t gList = GAlloc(8); wbe32(G + gList, gItems); wbe32(G + gList + 4, k);
        StripVertexCache h;
        h.m_hits = rng() % 50;
        for (int i = 0; i < 18; ++i) {
            h.m_verts[i] = rng() % 5 == 0 ? 0xFFFF : rng() % pool;
            h.m_pass[i] = rng() % 4 == 0 ? 2 : 1;
            h.m_setByHit[i] = rng() % 2;
        }
        h.m_next = rng() % 18;
        std::vector<uint8_t> cb = HostCacheBytes(&h);
        memcpy(G + C, cb.data(), 0x88);
        for (uint32_t a = 0x3F00000 - 0x400; a < 0x3F00400; ++a) G[a] = (uint8_t)rng();

        PPCContext ctx = NewCtx();
        ctx.r3.u64 = gList; ctx.r4.u64 = C;
        cmOperatorCtor_4C10_wrh(ctx, G);
        std::vector<TriStrip*> hostOrig = hostItems;
        TriStripList hl{hostItems.data(), k};
        TriStrip** hr = hl.TakeBest(&h);

        CHECK((hr == nullptr) == (ctx.r3.u32 == 0), "TakeBest null-ness (k=%u)", k);
        if (hr && ctx.r3.u32) CHECK((uint32_t)(hr - hl.m_items) == (ctx.r3.u32 - gItems) / 4, "TakeBest slot");
        CHECK(memcmp(HostCacheBytes(&h).data(), G + C, 0x86) == 0, "TakeBest changed the cache");
        for (uint32_t s = 0; s < k; ++s) {
            uint32_t gs = be32(G + gItems + 4 * s);
            uint32_t gIdx = (uint32_t)(std::find(guestStrips.begin(), guestStrips.end(), gs) - guestStrips.begin());
            uint32_t hIdx = (uint32_t)(std::find(hostOrig.begin(), hostOrig.end(), hl.m_items[s]) - hostOrig.begin());
            CHECK(gIdx == hIdx, "TakeBest order slot %u: host strip %u guest strip %u (trial %d)", s, hIdx, gIdx, trial);
            TriStrip* hs = hostOrig[s]; uint32_t g = guestStrips[s], gi = be32(G + g + 16);
            for (uint32_t i = 0; i < hs->m_numIndices; ++i) CHECK(hs->m_indices[i] == be16(G + gi + 2 * i), "TakeBest indices strip %u [%u]", s, i);
        }
        for (TriStrip* hs : hostOrig) { free(hs->m_indices); free(hs); }
    }
}

int main() {
    // TLS block at 0x2000, allocator object at 0x3000 (r13 = 0x1000 points at the TLS pointer).
    wbe32(G + 0x1000, 0x2000); wbe32(G + 0x2004, 0x3000);
    TestAccess();   printf("Access done, failures so far %d\n", failures);
    TestTriStrip(); printf("TriStrip done, failures so far %d\n", failures);
    TestStripper(); printf("TriStripper/LinkEdge done, failures so far %d\n", failures);
    TestTakeBest(); printf("TakeBest done, failures so far %d\n", failures);
    TestJoin();     printf("JoinStrips done, failures so far %d\n", failures);
    printf(failures ? "FAILED (%d)\n" : "ALL OK\n", failures);
    return failures != 0;
}
