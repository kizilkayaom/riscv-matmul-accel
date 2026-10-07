/* Drive a packed 2x2 matrix operation through MMIO. */

#include "accelerator.h"

int accelerator_matmul(uint32_t a, uint32_t b, volatile int32_t results[4], uint32_t poll_limit)
{
    volatile uint32_t *registers = (volatile uint32_t *)0x40000000u;
    /* Reject an active operation. */
    if ((registers[1] & 1u) != 0u)
        return -1;

    /* Load operands, then start. */
    registers[2] = a;
    registers[3] = b;
    registers[0] = 1u;

    /* Bound the completion wait. */
    while (poll_limit != 0u) {
        --poll_limit;
        if ((registers[1] & 2u) != 0u) {
            for (unsigned i = 0; i < 4; ++i)
                results[i] = (int32_t)registers[4 + i];
            return 0;
        }
    }
    return -2;
}
