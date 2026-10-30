#pragma once

#include <stdint.h>

/* Shared CRT image state. Native storage lives in src/globals.c. */
typedef struct CrtListEntry {
    struct CrtListEntry* m_pNext;
    struct CrtListEntry* m_pPrev;
} CrtListEntry;

typedef struct CrtInitCallbackNode {
    CrtListEntry m_links;
    void (*m_callback)(int initFlag);
} CrtInitCallbackNode;

typedef struct CrtTlsDispatch {
    int (*m_tlsAlloc)(void* destructorThunk);
    void* (*m_tlsGetValue)(uint32_t tlsIndex);
    int (*m_tlsSetValue)(uint32_t tlsIndex, void* value);
    int (*m_tlsFree)(uint32_t tlsIndex);
} CrtTlsDispatch;

extern void (*g_single_init_fn)(void);             // @ 0x825B1298
extern int g_cinit_retval;                        // @ 0x825B0A74
extern uint8_t g_crt_init_critical_section[8];     // @ 0x825B0A30
extern CrtListEntry g_crt_init_callback_list;      // @ 0x825B0A4C
extern CrtInitCallbackNode g_cinit_list_node;      // @ 0x825E6E78
extern CrtTlsDispatch g_tls_dispatch;             // @ 0x825E6E84
