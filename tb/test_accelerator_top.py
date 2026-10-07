# Test accelerator address decoding and register transactions.

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from model.golden_model import model
from test_controller import pack_matrix


async def write_register(dut, address, value, wstrb=0xF):
    await FallingEdge(dut.clk)
    dut.addr.value = address
    dut.wdata.value = value
    dut.wstrb.value = wstrb
    dut.write.value = 1
    dut.valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 1, f"Write at 0x{address:08X} is not ready"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.valid.value = 0
    dut.write.value = 0


async def read_register(dut, address):
    await FallingEdge(dut.clk)
    dut.addr.value = address
    dut.write.value = 0
    dut.wstrb.value = 0
    dut.valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 1, f"Read at 0x{address:08X} is not ready"
    value = int(dut.rdata.value)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.valid.value = 0
    return value


@cocotb.test()
async def test_accelerator_top(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.valid.value = 1
    dut.write.value = 0
    dut.addr.value = 0x40000008
    dut.wdata.value = 0
    dut.wstrb.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 0

    dut.valid.value = 0
    dut.reset.value = 0

    await write_register(dut, 0x40000008, 0x12345678)
    assert await read_register(dut, 0x40000008) == 0x12345678

    dut.addr.value = 0x50000008
    dut.wdata.value = 0xFFFFFFFF

    await FallingEdge(dut.clk)
    dut.valid.value = 1
    dut.wstrb.value = 0xF
    dut.write.value = 1
    await Timer(1, unit="ns")
    
    assert int(dut.ready.value) == 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.valid.value = 0
    dut.write.value = 0

    assert await read_register(dut, 0x40000008) == 0x12345678
    await write_register(dut, 0x40000008, 0x11223344)
    await write_register(dut, 0x40000008, 0xAABBCCDD, wstrb=0x5)
    assert await read_register(dut, 0x40000008) == 0x11BB33DD

    a = np.array([[64, -128], [127, 32]], dtype=np.int8)
    b = np.array([[64, -64], [127, 32]], dtype=np.int8)
    expected, _ = model(a, b)

    await write_register(dut, 0x40000008, pack_matrix(a))
    await write_register(dut, 0x4000000C, pack_matrix(b))

    await FallingEdge(dut.clk)
    dut.addr.value = 0x50000000
    dut.wdata.value = 1
    dut.valid.value = 1
    dut.wstrb.value = 0xF
    dut.write.value = 1

    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.valid.value = 0
    dut.write.value = 0
    assert await read_register(dut, 0x40000004) == 0

    await write_register(dut, 0x40000000, 1, wstrb=0x1)

    status = await read_register(dut, 0x40000004)
    assert status == 1, f"After start: expected STATUS=1, got {status}"

    for _ in range(10):
        status = await read_register(dut, 0x40000004)
        if status & 0b10:
            break
    else:
        assert False, "Polling operation did not finish within 10 STATUS reads"

    assert status == 2, f"Polling completed: expected STATUS=2, got {status}"

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
    await FallingEdge(dut.clk)
    dut.addr.value = 0x50000008
    dut.write.value = 0
    dut.wstrb.value = 0
    dut.valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 0
    assert int(dut.rdata.value) == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.valid.value = 0
