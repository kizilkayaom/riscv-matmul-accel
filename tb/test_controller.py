import os
import cocotb
import numpy as np
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from model.golden_model import model

A = np.array([[64, -128], [127, 32]], dtype=np.int8)
B = np.array([[64, -64], [127, 32]], dtype=np.int8)

C = np.array([[1, 2], [3, 4]], dtype=np.int8)
D = np.array([[5, 6], [7, 8]], dtype=np.int8)

@cocotb.test()
async def test_controller(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.start.value = 0
    dut.a_matrix.value = 0
    dut.b_matrix.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0
    assert int(dut.out.value) == 0

    dut.reset.value = 0

    dut.a_matrix.value = pack_matrix(A)
    dut.b_matrix.value = pack_matrix(B)
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.start.value = 0
    assert int(dut.busy.value) == 1
    assert int(dut.done.value) == 0

    dut.a_matrix.value = pack_matrix(C)
    dut.b_matrix.value = pack_matrix(D)

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.busy.value) == 1

    dut.start.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.start.value = 0

    assert int(dut.busy.value) == 1
    assert int(dut.done.value) == 0

    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            break
    else:
        assert False, "Controller did not finish within 10 cycles"

    assert int(dut.busy.value) == 0
    expected, _ = model(A, B)
    packed = int(dut.out.value)
    

    for r in range(2):
        for c in range(2):
            shift = (r * 2 + c) * 32
            actual = (packed >> shift) & 0xFFFFFFFF
            if actual >= 0x80000000:
                actual -= 0x100000000

            assert actual == int(expected[r, c]), (
                f"C[{r},{c}]: expected {expected[r, c]}, got {actual}"
            )
    saved_output = int(dut.out.value)

    for _ in range(3):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

        assert int(dut.done.value) == 1
        assert int(dut.busy.value) == 0
        assert int(dut.out.value) == saved_output
    
    expected, _ = model(C, D)
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.start.value = 0
    assert int(dut.done.value) == 0
    assert int(dut.busy.value) == 1

    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            break
    else:
        assert False, "Controller did not finish within 10 cycles"
    
    assert int(dut.busy.value) == 0
    packed = int(dut.out.value)
    for r in range(2):
        for c in range(2):
            shift = (r * 2 + c) * 32
            actual = (packed >> shift) & 0xFFFFFFFF
            if actual >= 0x80000000:
                actual -= 0x100000000

            assert actual == int(expected[r, c]), (
                f"Second operation C[{r},{c}]: "
                f"expected {expected[r, c]}, got {actual}"
            )

    
def pack_matrix(matrix):
    packed = 0
    for index, value in enumerate(matrix.flat):
        packed |= (int(value) & 0xFF) << (8 * index)
    return packed

@cocotb.test()
async def test_reset_while_busy(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.start.value = 0
    dut.a_matrix.value = 0
    dut.b_matrix.value = 0
    dut.reset.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.a_matrix.value = pack_matrix(A)
    dut.b_matrix.value = pack_matrix(B)
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.start.value = 0

    for _ in range(2):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    assert int(dut.busy.value) == 1
    assert int(dut.out.value) != 0

    dut.reset.value = 1
    await Timer(1, unit="ns")

    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0
    assert int(dut.out.value) == 0

    dut.reset.value = 0

    for _ in range(2):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.busy.value) == 0
        assert int(dut.done.value) == 0
        assert int(dut.out.value) == 0
    
    dut.a_matrix.value = pack_matrix(C)
    dut.b_matrix.value = pack_matrix(D)
    expected, _ = model(C, D)

    dut.start.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.start.value = 0

    assert int(dut.busy.value) == 1
    assert int(dut.done.value) == 0

    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            break
    else:
        assert False, "Recovery operation did not finish within 10 cycles"

    assert int(dut.busy.value) == 0
    
    packed = int(dut.out.value)

    for r in range(2):
        for c in range(2):
            shift = (r * 2 + c) * 32
            actual = (packed >> shift) & 0xFFFFFFFF
            if actual >= 0x80000000:
                actual -= 0x100000000

            assert actual == int(expected[r, c]), (
                f"Second operation C[{r},{c}]: "
                f"expected {expected[r, c]}, got {actual}"
            )

async def run_controller_case(dut, A, B, case_id):
    dut.a_matrix.value = pack_matrix(A)
    dut.b_matrix.value = pack_matrix(B)

    dut.start.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.start.value = 0

    assert int(dut.busy.value) == 1, f"{case_id}: start not accepted"
    assert int(dut.done.value) == 0, f"{case_id}: done did not clear"

    for _ in range(10):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.done.value) == 1:
            break
    else:
        assert False, f"{case_id}: controller did not finish within 10 cycles"

    assert int(dut.busy.value) == 0, f"{case_id}: busy remained high after completion"

    expected, _ = model(A, B)
    packed = int(dut.out.value)

    for r in range(2):
        for c in range(2):
            shift = (r * 2 + c) * 32
            actual = (packed >> shift) & 0xFFFFFFFF
            if actual >= 0x80000000:
                actual -= 0x100000000

            assert actual == int(expected[r, c]), (
                f"Second operation C[{r},{c}]: "
                f"expected {expected[r, c]}, got {actual}, case_id = {case_id}"
            )
    
@cocotb.test()
async def test_controller_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.start.value = 0
    dut.a_matrix.value = 0
    dut.b_matrix.value = 0

    dut.reset.value = 1
    
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    seed = int(os.environ.get("TEST_SEED", "42"))
    num_cases = int(os.environ.get("NUM_CASES", "100"))
    rng = np.random.default_rng(seed)

    for i in range(num_cases):
        A_random = rng.integers(-128, 128, size=(2, 2), dtype=np.int8)
        B_random = rng.integers(-128, 128, size=(2, 2), dtype=np.int8)

        await run_controller_case(
            dut, A_random, B_random,
            case_id=f"seed={seed}, case={i}",
        )
    
    dut._log.info(
        f"Passed {num_cases} controller operations; seed={seed}"
    )