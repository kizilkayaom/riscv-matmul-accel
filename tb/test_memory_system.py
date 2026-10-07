# Check shared RAM and accelerator address routing.

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from model.golden_model import model
from test_controller import pack_matrix

async def write_register(dut, address, value, wstrb=0xF):
    await FallingEdge(dut.clk)
    dut.mem_addr.value = address
    dut.mem_wdata.value = value
    dut.mem_wstrb.value = wstrb
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1, f"Write at 0x{address:08X} is not ready"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0


async def read_register(dut, address, wdata=0):
    await FallingEdge(dut.clk)
    dut.mem_addr.value = address
    dut.mem_wdata.value = wdata
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1, f"Read at 0x{address:08X} is not ready"
    value = int(dut.mem_rdata.value)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    return value


@cocotb.test()
async def test_memory_system(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.reset.value = 1
    dut.mem_addr.value = 0
    dut.mem_wdata.value = 0
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 0

    dut.mem_valid.value = 0
    dut.reset.value = 0

    await write_register(dut, 0x00000008, 0x11223344)
    await write_register(dut, 0x40000008, 0xAABBCCDD)

    assert await read_register(dut, 0x00000008) == 0x11223344
    assert await read_register(dut, 0x40000008) == 0xAABBCCDD

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x20000008
    dut.mem_wdata.value = 0xFFFFFFFF
    dut.mem_wstrb.value = 0xF
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 0
    assert int(dut.mem_rdata.value) == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0

    for address, expected in (
        (0x00000008, 0x11223344),
        (0x40000008, 0xAABBCCDD),
    ):
        actual = await read_register(dut, address)
        assert actual == expected, (
            f"After unmapped write, address 0x{address:08X}: "
            f"expected 0x{expected:08X}, got 0x{actual:08X}"
        )
    
    A = np.array([[64, -128], [127, 32]], dtype=np.int8)
    B = np.array([[64, -64], [127, 32]], dtype=np.int8)

    expected, _ = model(A, B)

    await write_register(dut, 0x40000008, pack_matrix(A))
    await write_register(dut, 0x4000000C, pack_matrix(B))

    await write_register(dut, 0x40000000, 1, 0x1)
    status_read = await read_register(dut, 0x40000004)
    assert status_read == 1

    for _ in range(10):
        status_read = await read_register(dut, 0x40000004)
        if status_read & 0b10:
            break
    else:
        assert False, "Polling operation did not finish within 10 STATUS reads"
    
    assert status_read == 2

    for r in range(2):
        for c in range(2):
            address = 0x40000010 + 4 * (r * 2 + c)
            actual = await read_register(dut, address)

            if actual >= 0x80000000:
                actual -= 0x100000000

            assert actual == int(expected[r, c]), (
                f"C[{r},{c}] at 0x{address:08X}: "
                f"expected {expected[r, c]}, got {actual}"
            )
    
    assert await read_register(dut, 0x00000008) == 0x11223344