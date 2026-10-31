#include "platform/time_stamp.h"
#include <cassert>
#include <chrono>
#include <thread>

uint32_t atSingleton_6F98_g();

int main() {
    const uint32_t before = tt_uptime_milliseconds();
    const uint32_t sample = atSingleton_6F98_g();
    const uint32_t after = tt_uptime_milliseconds();
    assert(sample - before <= after - before);

    const auto start = std::chrono::steady_clock::now();
    const uint32_t first = hostGetKeTimeStampBundle()->milliseconds;
    std::this_thread::sleep_for(std::chrono::milliseconds(25));
    const uint32_t second = atSingleton_6F98_g();
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start).count();
    assert(second - first >= 20);
    assert(second - first <= static_cast<uint64_t>(elapsed) + 5);

    // The import snapshot is thread-local: another caller cannot overwrite it.
    const auto* snapshot = hostGetKeTimeStampBundle();
    const uint32_t saved = snapshot->milliseconds;
    std::thread other([] { (void)atSingleton_6F98_g(); });
    other.join();
    assert(snapshot->milliseconds == saved);
}
