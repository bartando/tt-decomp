#include "xam/kernel.h"
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#include <new>
#include <unordered_map>

namespace {
struct WaitObject {
    enum Kind { Event, Semaphore } kind;
    std::mutex mutex;
    std::condition_variable changed;
    int32_t count = 0, maximum = 1;
    bool manual = false, closed = false;
    explicit WaitObject(Kind k) : kind(k) {}
};
std::mutex registryMutex;
std::unordered_map<void*, std::shared_ptr<WaitObject>> objects;
std::unordered_map<void*, std::shared_ptr<std::recursive_mutex>> criticalSections;
std::shared_ptr<WaitObject> lookup(void* key) {
    std::lock_guard<std::mutex> guard(registryMutex);
    auto it = objects.find(key);
    return it == objects.end() ? nullptr : it->second;
}
std::shared_ptr<std::recursive_mutex> critical(void* key) {
    std::lock_guard<std::mutex> guard(registryMutex);
    auto& value = criticalSections[key];
    if (!value) value = std::make_shared<std::recursive_mutex>();
    return value;
}
NTSTATUS create(HANDLE* out, WaitObject::Kind kind, int32_t count, int32_t maximum, bool manual) {
    if (!out) return STATUS_INVALID_PARAMETER;
    *out = nullptr;
    try {
        auto object = std::make_shared<WaitObject>(kind);
        object->count = count;
        object->maximum = maximum;
        object->manual = manual;
        std::lock_guard<std::mutex> guard(registryMutex);
        objects.emplace(object.get(), object);
        *out = object.get();
        return STATUS_SUCCESS;
    } catch (const std::bad_alloc&) { return STATUS_NO_MEMORY; }
}
NTSTATUS setEvent(void* key, int32_t* previous, bool set) {
    auto object = lookup(key);
    if (!object || object->kind != WaitObject::Event) return STATUS_INVALID_HANDLE;
    std::lock_guard<std::mutex> guard(object->mutex);
    if (object->closed) return STATUS_INVALID_HANDLE;
    if (previous) *previous = object->count;
    object->count = set;
    if (set) {
        if (object->manual) object->changed.notify_all();
        else object->changed.notify_one();
    }
    return STATUS_SUCCESS;
}
}

extern "C" NTSTATUS NtCreateEvent(HANDLE* out, uint32_t, void* attributes, uint32_t type, uint32_t initial) {
    if (out) *out = nullptr;
    if (type > 1) return STATUS_INVALID_PARAMETER;
    if (attributes) return STATUS_NOT_SUPPORTED; // Named/security NT objects have no host namespace.
    return create(out, WaitObject::Event, initial != 0, 1, type == NotificationEvent);
}
extern "C" void KeInitializeEvent(void* storage, EVENT_TYPE type, int32_t state) {
    if (!storage || (type != NotificationEvent && type != SynchronizationEvent)) return;
    auto object = std::make_shared<WaitObject>(WaitObject::Event);
    object->count = state != 0;
    object->manual = type == NotificationEvent;
    std::lock_guard<std::mutex> guard(registryMutex);
    objects[storage] = std::move(object);
}
extern "C" NTSTATUS NtSetEvent(HANDLE event, int32_t* previous) { return setEvent(event, previous, true); }
extern "C" NTSTATUS NtClearEvent(HANDLE event) { return setEvent(event, nullptr, false); }
extern "C" int32_t KeSetEvent(void* event, int32_t, uint32_t) {
    int32_t previous = 0;
    setEvent(event, &previous, true);
    return previous;
}
extern "C" int32_t KeResetEvent(void* event) {
    int32_t previous = 0;
    setEvent(event, &previous, false);
    return previous;
}
extern "C" NTSTATUS NtCreateSemaphore(HANDLE* out, uint32_t, void* attributes, int32_t initial, int32_t maximum) {
    if (out) *out = nullptr;
    if (initial < 0 || maximum <= 0 || initial > maximum) return STATUS_INVALID_PARAMETER;
    if (attributes) return STATUS_NOT_SUPPORTED;
    return create(out, WaitObject::Semaphore, initial, maximum, false);
}
extern "C" NTSTATUS NtReleaseSemaphore(HANDLE handle, int32_t count, int32_t* previous) {
    auto object = lookup(handle);
    if (!object || object->kind != WaitObject::Semaphore) return STATUS_INVALID_HANDLE;
    if (count <= 0) return STATUS_INVALID_PARAMETER;
    std::lock_guard<std::mutex> guard(object->mutex);
    if (object->closed) return STATUS_INVALID_HANDLE;
    if (count > object->maximum - object->count) return STATUS_SEMAPHORE_LIMIT_EXCEEDED;
    if (previous) *previous = object->count;
    object->count += count;
    object->changed.notify_all();
    return STATUS_SUCCESS;
}
extern "C" NTSTATUS NtWaitForSingleObjectEx(HANDLE handle, uint32_t mode, uint32_t alertable, LARGE_INTEGER* timeout) {
    if (mode > 1) return STATUS_INVALID_PARAMETER;
    if (alertable) return STATUS_NOT_SUPPORTED; // No host APC delivery mechanism.
    auto object = lookup(handle);
    if (!object) return STATUS_INVALID_HANDLE;
    std::unique_lock<std::mutex> guard(object->mutex);
    auto ready = [&] { return object->closed || object->count != 0; };
    if (!ready()) {
        if (!timeout) {
            object->changed.wait(guard, ready);
        } else if (*timeout < 0) {
            // NT relative intervals use 100ns ticks; INT64_MIN is valid.
            const uint64_t ticks = uint64_t(-(*timeout + 1)) + 1;
            using Clock = std::chrono::steady_clock;
            auto now = Clock::now();
            auto limit = std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::time_point::max() - now).count();
            auto ns = static_cast<int64_t>(std::min<uint64_t>(ticks, uint64_t(limit / 100))) * 100;
            if (!object->changed.wait_until(guard, now + std::chrono::nanoseconds(ns), ready)) return STATUS_TIMEOUT;
        } else {
            // Absolute NT timestamps are measured from 1601, not from now.
            using Clock = std::chrono::system_clock;
            constexpr int64_t epochTicks = INT64_C(116444736000000000);
            int64_t nowTicks = std::chrono::duration_cast<std::chrono::duration<int64_t, std::ratio<1, 10000000>>>(Clock::now().time_since_epoch()).count() + epochTicks;
            if (*timeout <= nowTicks) return STATUS_TIMEOUT;
            int64_t unixTicks = *timeout - epochTicks;
            auto seconds = std::chrono::seconds(unixTicks / 10000000);
            auto remainder = std::chrono::nanoseconds((unixTicks % 10000000) * 100);
            auto maxSeconds = std::chrono::duration_cast<std::chrono::seconds>(Clock::duration::max()).count();
            auto deadline = seconds.count() >= maxSeconds ? Clock::time_point::max()
                : Clock::time_point(std::chrono::duration_cast<Clock::duration>(seconds)
                                    + std::chrono::duration_cast<Clock::duration>(remainder));
            if (!object->changed.wait_until(guard, deadline, ready)) return STATUS_TIMEOUT;
        }
    }
    if (object->closed) return STATUS_INVALID_HANDLE;
    if (object->kind == WaitObject::Semaphore || !object->manual) --object->count;
    return STATUS_SUCCESS;
}
extern "C" NTSTATUS KeWaitForSingleObject(void* object, uint32_t, uint32_t mode, uint32_t alertable, LARGE_INTEGER* timeout) {
    return NtWaitForSingleObjectEx(object, mode, alertable, timeout);
}
extern "C" NTSTATUS NtClose(HANDLE handle) {
    std::shared_ptr<WaitObject> object;
    {
        std::lock_guard<std::mutex> guard(registryMutex);
        auto it = objects.find(handle);
        if (it == objects.end()) return STATUS_INVALID_HANDLE;
        object = it->second;
        objects.erase(it);
    }
    std::lock_guard<std::mutex> guard(object->mutex);
    object->closed = true;
    object->changed.notify_all();
    return STATUS_SUCCESS;
}
extern "C" NTSTATUS RtlInitializeCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (!cs) return STATUS_INVALID_PARAMETER;
    try { critical(cs); return STATUS_SUCCESS; }
    catch (const std::bad_alloc&) { return STATUS_NO_MEMORY; }
}
extern "C" NTSTATUS RtlDeleteCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (!cs) return STATUS_INVALID_PARAMETER;
    std::lock_guard<std::mutex> guard(registryMutex);
    criticalSections.erase(cs); // Caller must have released it, as in the NT contract.
    return STATUS_SUCCESS;
}
extern "C" void RtlEnterCriticalSection(RTL_CRITICAL_SECTION* cs) { if (cs) critical(cs)->lock(); }
extern "C" void RtlLeaveCriticalSection(RTL_CRITICAL_SECTION* cs) { if (cs) critical(cs)->unlock(); }
extern "C" uint32_t RtlTryEnterCriticalSection(RTL_CRITICAL_SECTION* cs) { return cs && critical(cs)->try_lock(); }
