/* Check C startup and measure accelerator driver execution. */

#include "accelerator.h"

volatile uint32_t boot_cookie = 0x13579BDFu;
volatile uint32_t boot_count;
extern volatile uint32_t benchmark_inputs[2];
extern volatile int32_t benchmark_results[4];
extern volatile uint32_t benchmark_markers[3];

int main(void)
{
    volatile uint32_t *inputs = benchmark_inputs;
    volatile uint32_t *markers = benchmark_markers;
    volatile int32_t *results = benchmark_results;

    /* Verify data and BSS initialization. */
    if (boot_cookie != 0x13579BDFu || boot_count != 0u) {
        markers[2] = 3u;
        return 1;
    }
    boot_count = 1u;
    markers[0] = 1u;
    uint32_t a = inputs[0];
    uint32_t b = inputs[1];
    int status = accelerator_matmul(a, b, results, 1000u);
    if (status != 0) {
        markers[2] = (uint32_t)-status;
        return 1;
    }
    markers[1] = 1u;
    return 0;
}
