/* Measure accelerator execution between RAM marker writes. */

.section .text
.globl _start

_start:
    li t4, 1
    /* Start timing. */
    sw t4, 0x7F0(zero)
    li t0, 0x40000000
    lw t1, 0x600(zero)
    sw t1, 8(t0)
    lw t1, 0x604(zero)
    sw t1, 12(t0)
    li t1, 1
    sw t1, 0(t0)

poll:
    lw t2, 4(t0)
    andi t2, t2, 2
    beqz t2, poll
    lw t3, 16(t0)
    sw t3, 0x700(zero)
    lw t3, 20(t0)
    sw t3, 0x704(zero)
    lw t3, 24(t0)
    sw t3, 0x708(zero)
    lw t3, 28(t0)
    sw t3, 0x70C(zero)
    /* End timing after result stores. */
    sw t4, 0x7F4(zero)

halt:
    j halt
