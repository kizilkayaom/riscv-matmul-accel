/* Check operand register write and readback from the CPU. */

.section .text
.globl _start

_start:
    li t0, 0x40000000
    li t1, 42
    sw t1, 8(t0)
    lw t2, 8(t0)
    sw t2, 256(zero)

halt:
    j halt