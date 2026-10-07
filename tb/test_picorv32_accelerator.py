# Check accelerator access through the PicoRV32 memory interface.

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer
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
async def test_picorv32_accelerator(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.mem_valid.value = 1
    dut.mem_addr.value = 0x40000008
    dut.mem_wdata.value = 0
    dut.mem_wstrb.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 0

    dut.mem_valid.value = 0
    dut.reset.value = 0

    await write_register(dut, 0x40000008, 0x12345678)
    assert await read_register(dut, 0x40000008, wdata=0xFFFFFFFF) == 0x12345678
    assert await read_register(dut, 0x40000008) == 0x12345678

    await write_register(dut, 0x40000008, 0xAABBCCDD, wstrb=0x8)
    assert await read_register(dut, 0x40000008) == 0xAA345678

    a = np.array([[64, -128], [127, 32]], dtype=np.int8)
    b = np.array([[64, -64], [127, 32]], dtype=np.int8)
    expected, _ = model(a, b)

    await write_register(dut, 0x40000008, pack_matrix(a))
    await write_register(dut, 0x4000000C, pack_matrix(b))
    await write_register(dut, 0x40000000, 1, wstrb=0x1)

    status = await read_register(dut, 0x40000004)
    assert status == 1, f"After start: expected STATUS=1, got {status}"

    for _ in range(10):
        status = await read_register(dut, 0x40000004)
        if status & 0b10:
            break
    else:
        assert False, "Operation did not finish within 10 STATUS reads"

    assert status == 2, f"After completion: expected STATUS=2, got {status}"

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
