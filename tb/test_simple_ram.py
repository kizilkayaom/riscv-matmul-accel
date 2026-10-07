# Check RAM reads, byte writes, and reset behavior.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

@cocotb.test()
async def test_simple_ram(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.mem_addr.value = 0x00000000
    dut.mem_valid.value = 1
    dut.mem_wdata.value = 0
    dut.mem_wstrb.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 0

    dut.mem_valid.value = 0
    dut.reset.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000000
    dut.mem_wdata.value = 0x12345678
    dut.mem_wstrb.value = 0xF
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000000
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0x12345678

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000004
    dut.mem_wdata.value = 0xAABBCCDD
    dut.mem_wstrb.value = 0xF
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000000
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0x12345678

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000004
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0xAABBCCDD

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0
    dut.mem_wdata.value = 0xAABBCCDD
    dut.mem_wstrb.value = 0x2
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0x1234CC78

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000FFC
    dut.mem_wdata.value = 0xDEADBEEF
    dut.mem_wstrb.value = 0xF
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    await RisingEdge(dut.clk)

    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00000FFC
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0xDEADBEEF

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0x00001000
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

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0x1234CC78

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0

    await FallingEdge(dut.clk)
    dut.reset.value = 1
    dut.mem_addr.value = 0
    dut.mem_wdata.value = 0xFFFFFFFF
    dut.mem_valid.value = 1
    dut.mem_wstrb.value = 0xF

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 0

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.mem_valid.value = 0
    dut.mem_wstrb.value = 0
    dut.reset.value = 0

    await FallingEdge(dut.clk)
    dut.mem_addr.value = 0
    dut.mem_wstrb.value = 0
    dut.mem_valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.mem_ready.value) == 1
    assert int(dut.mem_rdata.value) == 0x1234CC78

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.mem_valid.value = 0
