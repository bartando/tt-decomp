#include "game/frontend_page_group.hpp"
#include "game/frontend_input.hpp"
#include "rage/hud_page_group.hpp"
#include "rage/swf_page_group.hpp"

extern const char g_dialogDoneKey[]; // @ 0x820627E4

namespace {
struct DialogClose {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Reserved3() = 0;
    virtual void Reserved4() = 0;
    virtual void Close() = 0;
};
}

// @ 0x82322470
uint32_t DialogPageGroup_IsComplete(void* group) {
    if (static_cast<const uint8_t*>(group)[0x61] != 0) {
        const uint8_t acquired = static_cast<uint8_t>(hudFlashBase_IsNetworkDirty(group));
        void* movie = hudFlashBase_GetPageGroup(group);
        // Retail leaves this stack word undefined when iDone is absent.
        int32_t done;
        swfGetPageGroupInteger(movie, g_dialogDoneKey, &done);
        if (acquired != 0) hudFlashBase_PublishPageGroup(group);
        if (done <= 0) return 0;
    }
    FrontendInputRecord notification;
    if (FrontendInput_FindHighestPriority(g_frontendInputQueue.get(), &notification, -1, -1) == 0)
        return 1;
    static_cast<DialogClose*>(group)->Close();
    return 0;
}
