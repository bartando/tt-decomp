#include "xam/kernel.h"
#include "xam/thread_sync.h"
#include "platform/host_error.h"
#include <atomic>
#include <cassert>
#include <chrono>
#include <climits>
#include <cstdio>
#include <thread>
#include <vector>

int main() {
    LARGE_INTEGER poll = 0, shortWait = -10000;
    HANDLE event = nullptr, sem = nullptr;
    assert(NtCreateEvent(&event, 0, nullptr, NotificationEvent, 0) == STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(event, 1, 0, &poll) == STATUS_TIMEOUT);
    assert(NtWaitForSingleObjectEx(event, 1, 0, &shortWait) == STATUS_TIMEOUT);
    int32_t old = -1;
    assert(NtSetEvent(event, &old) == STATUS_SUCCESS && old == 0);
    for (int i=0;i<2;++i) assert(NtWaitForSingleObjectEx(event, 1, 0, &poll) == STATUS_SUCCESS);
    assert(KeResetEvent(event) == 1);
    LARGE_INTEGER past = 1;
    assert(NtWaitForSingleObjectEx(event, 1, 0, &past) == STATUS_TIMEOUT);
    LARGE_INTEGER absolute;
    KeQuerySystemTime(&absolute);
    absolute += 10000;
    assert(NtWaitForSingleObjectEx(event, 1, 0, &absolute) == STATUS_TIMEOUT);
    assert(NtWaitForSingleObjectEx(event, 1, 1, nullptr) == STATUS_NOT_SUPPORTED);
    assert(NtClose(event) == STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(event, 1, 0, &poll) == STATUS_INVALID_HANDLE);
    assert(NtCreateEvent(&event, 0, nullptr, SynchronizationEvent, 1) == STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(event, 1, 0, &poll) == STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(event, 1, 0, &poll) == STATUS_TIMEOUT);
    std::thread signal([&] { std::this_thread::sleep_for(std::chrono::milliseconds(2)); NtSetEvent(event,nullptr); });
    LARGE_INTEGER longest = LLONG_MIN;
    assert(NtWaitForSingleObjectEx(event, 1, 0, &longest) == STATUS_SUCCESS);
    signal.join(); NtClose(event);
    assert(NtCreateSemaphore(&sem,0,nullptr,0,2)==STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(sem,1,0,&poll)==STATUS_TIMEOUT);
    assert(NtReleaseSemaphore(sem,2,&old)==STATUS_SUCCESS && old==0);
    assert(NtReleaseSemaphore(sem,INT_MAX,&old)==STATUS_SEMAPHORE_LIMIT_EXCEEDED);
    for (int i=0;i<2;++i) assert(NtWaitForSingleObjectEx(sem,1,0,&poll)==STATUS_SUCCESS);
    assert(NtWaitForSingleObjectEx(sem,1,0,&poll)==STATUS_TIMEOUT);
    std::atomic<bool> entered{false};
    std::thread waiter([&] { entered=true; assert(NtWaitForSingleObjectEx(sem,1,0,nullptr)==STATUS_SUCCESS); });
    while(!entered) std::this_thread::yield();
    assert(NtReleaseSemaphore(sem,1,nullptr)==STATUS_SUCCESS);
    waiter.join(); NtClose(sem);
    RTL_CRITICAL_SECTION cs{};
    assert(RtlInitializeCriticalSection(&cs)==STATUS_SUCCESS);
    RtlEnterCriticalSection(&cs); assert(RtlTryEnterCriticalSection(&cs)==1);
    std::thread contender([&] { assert(!RtlTryEnterCriticalSection(&cs)); }); contender.join();
    RtlLeaveCriticalSection(&cs); RtlLeaveCriticalSection(&cs);
    unsigned total=0;
    std::vector<std::thread> workers;
    for(int n=0;n<4;++n) workers.emplace_back([&] { for(int i=0;i<1000;++i) { RtlEnterCriticalSection(&cs); ++total; RtlLeaveCriticalSection(&cs); } });
    for(auto& worker:workers) worker.join();
    assert(total==4000); assert(RtlDeleteCriticalSection(&cs)==STATUS_SUCCESS);
    auto slot=KeTlsAlloc(); assert(slot!=UINT32_MAX);
    int mainValue=1, otherValue=2;
    assert(KeTlsSetValue(slot,&mainValue));
    std::thread tls([&] { assert(!KeTlsGetValue(slot)); assert(KeTlsSetValue(slot,&otherValue)); assert(KeTlsGetValue(slot)==&otherValue); }); tls.join();
    assert(KeTlsGetValue(slot)==&mainValue); assert(KeTlsFree(slot)); assert(!KeTlsSetValue(slot,nullptr));
    KfLowerIrql(0); assert(KeRaiseIrqlToDpcLevel()==0); assert(KeRaiseIrqlToDpcLevel()==2); KfLowerIrql(0);
    void* memory=MmAllocatePhysicalMemoryEx(0,5000,4,0,UINT32_MAX,8192);
    assert(memory && uintptr_t(memory)%8192==0 && MmQueryAllocationSize(memory)==8192);
    for(unsigned i=0;i<8192;++i) assert(static_cast<unsigned char*>(memory)[i]==0);
    MmFreePhysicalMemory(0,memory); assert(!MmQueryAllocationSize(memory));
    assert(!MmAllocatePhysicalMemoryEx(0,5000,4,1,UINT32_MAX,0));
    assert(!MmAllocatePhysicalMemoryEx(0,5000,4,0,UINT32_MAX,3));
    assert(sysThread_WaitTimeout(nullptr,0)==UINT32_MAX && hostGetLastError()==6);
    assert(NtCreateSemaphore(&sem,0,nullptr,0,1)==STATUS_SUCCESS);
    assert(sysThread_WaitTimeout(sem,0)==STATUS_TIMEOUT);
    assert(sysThread_WaitTimeoutEx(sem,0,1)==UINT32_MAX && hostGetLastError()==50);
    assert(sysThread_ReleaseSemaphore(sem,2,nullptr)==0 && hostGetLastError()==298);
    assert(sysThread_ReleaseSemaphore(sem,1,nullptr)==1);
    assert(sysThread_WaitTimeout(sem,0)==STATUS_SUCCESS);
    hostSetLastError(123);
    std::thread errors([] { assert(hostGetLastError()==0); hostSetLastError(456); assert(hostGetLastError()==456); });
    errors.join(); assert(hostGetLastError()==123); NtClose(sem);
    std::puts("PASS host synchronization, TLS, IRQL, allocation and integrated SDK wait/error contracts");
}
