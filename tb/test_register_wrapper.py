# Check register access, byte strobes, and matrix results.

import os

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from model.golden_model import model
from test_controller import pack_matrix

A = np.array([[64, -128], [127, 32]], dtype=np.int8)
B = np.array([[64, -64], [127, 32]], dtype=np.int8)


async def read_register(dut, address):
    await FallingEdge(dut.clk)

    dut.addr.value = address
    dut.write.value = 0
    dut.wstrb.value = 0
    dut.valid.value = 1

    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 1, f"Read at 0x{address:02X}: wrapper not ready"

    raw_rdata = int(dut.rdata.value)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.valid.value = 0
    return raw_rdata


async def write_register(dut, address, value, wstrb=0xF):
    await FallingEdge(dut.clk)

    dut.addr.value = address
    dut.wdata.value = value
    dut.wstrb.value = wstrb
    dut.write.value = 1
    dut.valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.ready.value) == 1, f"Write at 0x{address:02X}: wrapper not ready"

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.valid.value = 0
    dut.write.value = 0


async def wait_for_done(dut, case_id):
    for _ in range(10):
        status = await read_register(dut, 0x04)
        if status & 0b10:
            break
    else:
        assert False, f"{case_id}: did not finish within 10 STATUS reads"

    assert status == 2, f"{case_id}: expected STATUS=2, got {status}"


async def check_results(dut, expected, case_id):
    for r in range(2):
        for c in range(2):
            address = 0x10 + 4 * (r * 2 + c)
            rdata = await read_register(dut, address)
            # Decode signed 32-bit results.
            if rdata >= 0x80000000:
                rdata -= 0x100000000

            assert rdata == int(expected[r, c]), (
                f"{case_id} C[{r},{c}] at 0x{address:02X}: "
                f"expected {expected[r, c]}, got {rdata}"
            )


@cocotb.test()
async def test_public_signals(dut):
    C = np.array([[1, 2], [3, 4]], dtype=np.int8)
    D = np.array([[5, 6], [7, 8]], dtype=np.int8)

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.valid.value = 0
    dut.write.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.wstrb.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 0

    dut.reset.value = 0
    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 1

    for mask in (0x0, 0x2, 0x4, 0x8, 0xE):
        await write_register(dut, 0x00, 1, wstrb=mask)
        status = await read_register(dut, 0x04)
        assert status == 0, (
            f"CONTROL wstrb=0x{mask:X}: expected idle STATUS=0, got {status}"
        )

    cases = [
        (0x1, 0x112233DD),
        (0x2, 0x1122CC44),
        (0x4, 0x11BB3344),
        (0x8, 0xAA223344),
        (0x0, 0x11223344),
        (0xF, 0xAABBCCDD),
    ]
    for address in (0x08, 0x0C):
        for wstrb, expected_value in cases:
            await write_register(dut, address, 0x11223344)
            await write_register(dut, address, 0xAABBCCDD, wstrb=wstrb)
            actual = await read_register(dut, address)
            assert actual == expected_value, (
                f"Register 0x{address:02X}, wstrb=0x{wstrb:X}: "
                f"expected 0x{expected_value:08X}, got 0x{actual:08X}"
            )

    await write_register(dut, 0x08, pack_matrix(A))

    assert await read_register(dut, 0x08) == pack_matrix(A)

    await write_register(dut, 0x0C, pack_matrix(B))

    checks = [
        (0x08, pack_matrix(A)),
        (0x0C, pack_matrix(B)),
    ]
    for address, expected_value in checks:
        actual = await read_register(dut, address)
        assert actual == expected_value, (
            f"Register 0x{address:02X}: expected {expected_value}, got {actual}"
        )

    for control_value in (0, 2):
        await write_register(dut, 0x00, control_value)
        status = await read_register(dut, 0x04)
        assert status == 0, (
            f"CONTROL={control_value}: expected idle STATUS=0, got {status}"
        )

    await write_register(dut, 0x00, 1, wstrb=0x1)
    await write_register(dut, 0x08, pack_matrix(C))
    await write_register(dut, 0x0C, pack_matrix(D))
    await write_register(dut, 0x00, 1)
    status = await read_register(dut, 0x04)
    assert status == 1, f"After start: expected busy STATUS=1, got {status}"

    await wait_for_done(dut, "First operation")

    expected, _ = model(A, B)

    await check_results(dut, expected, "First operation")
        
    assert await read_register(dut, 0x04) == 2

    await write_register(dut, 0x04, 0)

    assert await read_register(dut, 0x04) == 2

    for address in [0x10, 0x14, 0x18, 0x1C]:
        raw_value = await read_register(dut, address)
        await write_register(dut, address, raw_value ^ 0xFFFFFFFF)
        assert raw_value == await read_register(dut, address), (
            f"Failure in {address}"
        )
    
    assert await read_register(dut, 0x20) == 0

    await write_register(dut, 0x20, 0xFFFFFFFF)

    assert await read_register(dut, 0x20) == 0

    checks = [
        (0x08, pack_matrix(C)),
        (0x0C, pack_matrix(D)),
    ]
    for address, expected_value in checks:
        actual = await read_register(dut, address)
        assert actual == expected_value, (
            f"Register 0x{address:02X}: expected {expected_value}, got {actual}"
        )

    assert await read_register(dut, 0x04) == 2

    await FallingEdge(dut.clk)

    dut.addr.value = 0x08

    dut.wdata.value = 0
    dut.wstrb.value = 0xF
    dut.write.value = 1
    dut.valid.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.write.value = 0

    assert await read_register(dut, 0x08) == pack_matrix(C)

    assert await read_register(dut, 0x04) == 2

    await write_register(dut, 0x00, 1)

    assert await read_register(dut, 0x04) == 1

    await wait_for_done(dut, "Second operation")

    expected, _ = model(C, D)

    await check_results(dut, expected, "Second operation")
    
    await write_register(dut, 0x00, 1)
    assert await read_register(dut, 0x04) == 1

    await FallingEdge(dut.clk)
    dut.reset.value = 1
    await Timer(1, unit="ns")

    assert int(dut.ready.value) == 0

    dut.addr.value = 0x08
    dut.wdata.value = 0xFFFFFFFF
    dut.wstrb.value = 0xF
    dut.write.value = 1
    dut.valid.value = 1

    await FallingEdge(dut.clk)
    
    dut.valid.value = 0
    dut.write.value = 0
    dut.reset.value = 0
    await Timer(1, unit="ns")

    assert int(dut.ready.value) == 1

    for address in (0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C):
        actual = await read_register(dut, address)
        assert actual == 0, (
            f"After reset, register 0x{address:02X}: expected 0, got {actual}"
        )
    
    await write_register(dut, 0x08, pack_matrix(A))
    await write_register(dut, 0x0C, pack_matrix(B))
    await write_register(dut, 0x00, 1)

    assert await read_register(dut, 0x04) == 1

    await wait_for_done(dut, "Post-reset operation")

    expected, _ = model(A, B)

    await check_results(dut, expected, "Post-reset operation")


@cocotb.test()
async def test_random_matrices(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.valid.value = 0
    dut.write.value = 0
    dut.addr.value = 0
    dut.wdata.value = 0
    dut.wstrb.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 0

    dut.reset.value = 0
    await Timer(1, unit="ns")
    assert int(dut.ready.value) == 1

    seed = int(os.getenv("TEST_SEED", "42"))
    num_cases = int(os.getenv("NUM_CASES", "100"))
    rng = np.random.default_rng(seed)

    for i in range(num_cases):
        a = rng.integers(-128, 128, size=(2, 2), dtype=np.int8)
        b = rng.integers(-128, 128, size=(2, 2), dtype=np.int8)
        case_id = f"seed={seed} case={i}"
        expected, _ = model(a, b)
    
        await write_register(dut, 0x08, pack_matrix(a))
        await write_register(dut, 0x0C, pack_matrix(b))
        await write_register(dut, 0x00, 1)

        status = await read_register(dut, 0x04)
        assert status == 1, f"{case_id}: expected busy STATUS=1, got {status}"

        await wait_for_done(dut, case_id)
        await check_results(dut, expected, case_id)
