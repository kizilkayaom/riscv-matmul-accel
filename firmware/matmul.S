/* Run two accelerator operations and save results in RAM. */

.section .text
.globl _start

_start:
    li t0, 0x40000000
    li t1, 0x207F8040
    sw t1, 8(t0)
    li t1, 0x207FC040
    sw t1, 12(t0)
    li t1, 1
    sw t1, 0(t0)

poll:
    lw t2, 4(t0)
    andi t2, t2, 2
    beqz t2, poll
    lw t3, 16(t0)
    sw t3, 256(zero)
    lw t3, 20(t0)
    sw t3, 260(zero)
    lw t3, 24(t0)
    sw t3, 264(zero)
    lw t3, 28(t0)
    sw t3, 268(zero)
    li t1, 0
    sw t1, 8(t0)
    li t1, 1
    sw t1, 0(t0)

poll_second:
    lw t2, 4(t0)
    andi t2, t2, 2
    beqz t2, poll_second
    lw t3, 16(t0)
    sw t3, 272(zero)
    lw t3, 20(t0)
    sw t3, 276(zero)
    lw t3, 24(t0)
    sw t3, 280(zero)
    lw t3, 28(t0)
    sw t3, 284(zero)

halt:
    j halt
