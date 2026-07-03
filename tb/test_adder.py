import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_adder(dut):
    a, b = 5, 2
    dut.in1.value = a
    dut.in2.value = b
    await Timer(1, unit="ns")
    assert dut.out.value == a + b, f"Expected {a+b}, got {dut.out.value}"